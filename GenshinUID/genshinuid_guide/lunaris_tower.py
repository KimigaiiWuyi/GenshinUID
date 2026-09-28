"""深渊日程与楼层来自 Lunaris，不再读打不开的 homdgcat database.js。"""

import json
import asyncio
import hashlib
import datetime
from typing import TypedDict
from pathlib import Path

import httpx
import aiofiles

_DATA = "https://api.lunaris.moe/data"
_TIME_FMT = "%Y-%m-%d %H:%M:%S"
_JSON_TTL = 6 * 3600


class ScheduleRow(TypedDict):
    openTime: str
    closeTime: str
    chsBuffName: str


class TowerMonster(TypedDict):
    name: str
    icon: str
    count: int
    hp: int


class TowerChamber(TypedDict):
    name: str
    level: int
    upper: list[TowerMonster]
    lower: list[TowerMonster]
    upper_buff: str
    lower_buff: str


class TowerFloorView(TypedDict):
    floor: int
    schedule_id: str
    buff_name: str
    buff_desc: str
    open_time: str
    close_time: str
    chambers: list[TowerChamber]


class TowerTrendRow(TypedDict):
    """某一期某层的上半 / 下半血量合计。current 标出正在看的那一期。"""

    id: str
    label: str
    upper: float
    lower: float
    current: bool


class TowerChamberHp(TypedDict):
    name: str
    upper: float
    lower: float


def plain_markup(text: str) -> str:
    out: list[str] = []
    skip = False
    for ch in text:
        if ch == "<":
            skip = True
            continue
        if ch == ">":
            skip = False
            continue
        if not skip:
            out.append(ch)
    return "".join(out).replace("\n", " ").strip()


def pick_schedule_id(listing: dict[str, ScheduleRow], now: datetime.datetime) -> str:
    """窗口内的期优先；都已结束则取最近一次开过的。"""
    current = ""
    latest_id = ""
    latest_open: datetime.datetime | None = None
    for schedule_id, row in listing.items():
        opened = datetime.datetime.strptime(row["openTime"], _TIME_FMT)
        closed = datetime.datetime.strptime(row["closeTime"], _TIME_FMT)
        if opened <= now <= closed:
            current = schedule_id
            break
        if latest_open is None or opened > latest_open:
            latest_open = opened
            latest_id = schedule_id
    return current or latest_id


def _month_close(opened: datetime.datetime) -> datetime.datetime:
    month = opened.month + 1
    year = opened.year
    if month > 12:
        month = 1
        year += 1
    return opened.replace(year=year, month=month, day=16, hour=3, minute=59, second=59)


def _align_sixteenth(listing: dict[str, ScheduleRow]) -> dict[str, ScheduleRow]:
    """锐进之月起每期都是 16 日 4:00 到下月 16 日。不足 7 天的空档丢掉。"""
    ordered = sorted(listing.items(), key=lambda item: item[1]["openTime"])
    anchor = -1
    for index, (_, row) in enumerate(ordered):
        if row["chsBuffName"] == "锐进之月":
            anchor = index
            break
    if anchor < 0:
        return listing
    aligned: dict[str, ScheduleRow] = {}
    for schedule_id, row in ordered[:anchor]:
        aligned[schedule_id] = row
    fixing = False
    next_open: datetime.datetime | None = None
    for schedule_id, row in ordered[anchor:]:
        opened = datetime.datetime.strptime(row["openTime"], _TIME_FMT)
        closed = datetime.datetime.strptime(row["closeTime"], _TIME_FMT)
        if (closed - opened).total_seconds() < 7 * 86400:
            continue
        if not fixing and opened.day == 16 and closed.day == 16:
            aligned[schedule_id] = row
            next_open = closed.replace(hour=4, minute=0, second=0)
            continue
        fixing = True
        if opened.day == 16:
            next_open = opened.replace(hour=4, minute=0, second=0)
        elif next_open is None:
            next_open = opened.replace(day=16, hour=4, minute=0, second=0)
        close = _month_close(next_open)
        aligned[schedule_id] = ScheduleRow(
            openTime=next_open.strftime(_TIME_FMT),
            closeTime=close.strftime(_TIME_FMT),
            chsBuffName=row["chsBuffName"],
        )
        next_open = close.replace(hour=4, minute=0, second=0)
    return aligned


def schedule_listing(raw: dict[str, object]) -> dict[str, ScheduleRow]:
    listing: dict[str, ScheduleRow] = {}
    for schedule_id, item in raw.items():
        if not isinstance(item, dict):
            continue
        if "openTime" not in item or "closeTime" not in item:
            continue
        opened = item["openTime"]
        closed = item["closeTime"]
        if not isinstance(opened, str) or not isinstance(closed, str):
            continue
        buff = ""
        if "chsBuffName" in item and isinstance(item["chsBuffName"], str):
            buff = item["chsBuffName"]
        listing[schedule_id] = ScheduleRow(openTime=opened, closeTime=closed, chsBuffName=buff)
    return _align_sixteenth(listing)


def _pack_monsters(raw_list: object) -> list[TowerMonster]:
    if not isinstance(raw_list, list):
        return []
    order: list[str] = []
    counts: dict[str, int] = {}
    icons: dict[str, str] = {}
    hp_of: dict[str, int] = {}
    for item in raw_list:
        if not isinstance(item, dict) or "name" not in item:
            continue
        name = item["name"]
        if not isinstance(name, str) or not name:
            continue
        icon = ""
        if "icon" in item and isinstance(item["icon"], str):
            icon = item["icon"]
        hp = 0
        if "hp" in item and isinstance(item["hp"], (int, float)):
            hp = int(item["hp"])
        if name not in counts:
            order.append(name)
            counts[name] = 0
            icons[name] = icon
            hp_of[name] = hp
        counts[name] += 1
    return [TowerMonster(name=name, icon=icons[name], count=counts[name], hp=hp_of[name]) for name in order]


def _buff_text(raw: object) -> str:
    if not isinstance(raw, dict) or "description" not in raw:
        return ""
    desc = raw["description"]
    if not isinstance(desc, str):
        return ""
    return plain_markup(desc)


def parse_tower_floor(
    payload: dict[str, object], floor: int, schedule_id: str, schedule: ScheduleRow
) -> TowerFloorView | str:
    floors = payload["floors"] if "floors" in payload else None
    if not isinstance(floors, list):
        return "Lunaris 深渊数据没有楼层。"
    chosen: dict[str, object] | None = None
    for item in floors:
        if not isinstance(item, dict) or "floorIndex" not in item:
            continue
        index = item["floorIndex"]
        if index == floor:
            chosen = item
            break
    if chosen is None:
        return f"Lunaris 本期没有第 {floor} 层。"
    chambers_raw = chosen["chambers"] if "chambers" in chosen else None
    if not isinstance(chambers_raw, list):
        return f"Lunaris 第 {floor} 层没有间数据。"
    upper_buff = _buff_text(chosen["firstHalfBuff"] if "firstHalfBuff" in chosen else None)
    lower_buff = _buff_text(chosen["secondHalfBuff"] if "secondHalfBuff" in chosen else None)
    chambers: list[TowerChamber] = []
    for idx, chamber in enumerate(chambers_raw):
        if not isinstance(chamber, dict):
            continue
        level = chamber["monsterLevel"] if "monsterLevel" in chamber else 0
        if not isinstance(level, int):
            level = 0
        chambers.append(
            TowerChamber(
                name=f"{floor}-{idx + 1}",
                level=level,
                upper=_pack_monsters(chamber["firstHalfMonsters"] if "firstHalfMonsters" in chamber else None),
                lower=_pack_monsters(chamber["secondHalfMonsters"] if "secondHalfMonsters" in chamber else None),
                upper_buff=upper_buff,
                lower_buff=lower_buff,
            )
        )
    buff_name = ""
    if "buffName" in payload and isinstance(payload["buffName"], str):
        buff_name = payload["buffName"]
    if not buff_name:
        buff_name = schedule["chsBuffName"]
    monthly = payload["monthlyBuff"] if "monthlyBuff" in payload else None
    return TowerFloorView(
        floor=floor,
        schedule_id=schedule_id,
        buff_name=buff_name,
        buff_desc=_buff_text(monthly),
        open_time=schedule["openTime"],
        close_time=schedule["closeTime"],
        chambers=chambers,
    )


def _json_cache_path(url: str) -> Path:
    from ..utils.resource.RESOURCE_PATH import WIKI_DATA_PATH

    digest = hashlib.sha256(url.encode()).hexdigest()[:24]
    return WIKI_DATA_PATH / "lunaris_json" / f"{digest}.json"


def _json_ttl(url: str) -> float | None:
    # 版本号和危战正文会原地更新；带版本路径的楼层文件内容不变。
    if url.endswith("/version.json") or "/leylinechallenge/" in url:
        return _JSON_TTL
    return None


def _cache_fresh(path: Path, ttl: float | None) -> bool:
    if not path.exists():
        return False
    if ttl is None:
        return True
    age = datetime.datetime.now().timestamp() - path.stat().st_mtime
    return age < ttl


async def _read_json_file(path: Path) -> dict[str, object] | None:
    async with aiofiles.open(path, encoding="utf-8") as file:
        text = await file.read()
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(raw, dict):
        return raw
    return None


async def fetch_json_object(url: str) -> dict[str, object] | None:
    # 命中本地缓存就不再请求。远端超时或坏包不当作程序错误。
    path = _json_cache_path(url)
    miss = path.with_suffix(".miss")
    ttl = _json_ttl(url)
    if _cache_fresh(path, ttl):
        cached = await _read_json_file(path)
        if cached is not None:
            return cached
    if _cache_fresh(miss, _JSON_TTL):
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code != 200:
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(miss, "w", encoding="utf-8") as file:
            await file.write("")
        return None
    try:
        payload: object = response.json()
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(payload, ensure_ascii=False))
    if miss.exists():
        miss.unlink()
    return payload


def _tower_ranges(listing: dict[str, ScheduleRow]) -> str:
    from .endgame_query import RangeRow, format_ranges

    rows = [
        RangeRow(id=schedule_id, begin=row["openTime"], end=row["closeTime"], title=row["chsBuffName"])
        for schedule_id, row in listing.items()
    ]
    return format_ranges("深渊", rows)


async def tower_context() -> tuple[str, dict[str, ScheduleRow]] | None:
    """版本号 + 全部日程。取不到返回 None。"""
    version_payload = await fetch_json_object(f"{_DATA}/version.json")
    if version_payload is None or "version" not in version_payload:
        return None
    version = version_payload["version"]
    if not isinstance(version, str) or not version:
        return None
    listing_raw = await fetch_json_object(f"{_DATA}/{version}/towerlist.json")
    if listing_raw is None:
        return None
    return version, schedule_listing(listing_raw)


def _half_total(monsters: list[TowerMonster]) -> float:
    """数量 × 单只血量。Lunaris 的 firstHalfMonsters 是一条一条列的，count 是同名计数。"""
    return float(sum(item["hp"] * item["count"] for item in monsters))


def floor_totals(view: TowerFloorView) -> tuple[float, float]:
    """整层上半 / 下半血量合计。"""
    upper = 0.0
    lower = 0.0
    for chamber in view["chambers"]:
        upper += _half_total(chamber["upper"])
        lower += _half_total(chamber["lower"])
    return upper, lower


def chamber_hps(view: TowerFloorView) -> list[TowerChamberHp]:
    """逐间上下半血量，给当期血量图用。"""
    return [
        TowerChamberHp(name=chamber["name"], upper=_half_total(chamber["upper"]), lower=_half_total(chamber["lower"]))
        for chamber in view["chambers"]
    ]


# 单只怪血量的合理性上限。实测正常值 18万~750万（遗迹守卫 248万），
# 留到 1 亿仍有 13 倍余量。Lunaris 偶尔把某只写成千倍（20092 遗迹守卫 2,481,645,770），
# 这种期混进趋势会把纵轴拉爆、其余期全压成直线，只能整期剔掉。
ABYSS_HP_CAP = 100_000_000


def floor_is_plausible(view: TowerFloorView) -> bool:
    """这一期的血量能不能进趋势图。"""
    for chamber in view["chambers"]:
        for monsters in (chamber["upper"], chamber["lower"]):
            for item in monsters:
                if item["hp"] > ABYSS_HP_CAP:
                    return False
    return True


def _hp_cache_path() -> Path:
    from ..utils.resource.RESOURCE_PATH import WIKI_DATA_PATH

    return WIKI_DATA_PATH / "lunaris_tower_hp.json"


async def _load_hp_cache() -> dict[str, tuple[float, float]]:
    """历史期血量。开过的期不会再变，缓存下来就不再下载楼层正文。"""
    path = _hp_cache_path()
    if not path.exists():
        return {}
    async with aiofiles.open(path, encoding="utf-8") as file:
        raw: object = json.loads(await file.read())
    if not isinstance(raw, dict):
        return {}
    rows: dict[str, tuple[float, float]] = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, list) or len(value) != 2:
            continue
        first, second = value
        if isinstance(first, (int, float)) and isinstance(second, (int, float)):
            rows[key] = (float(first), float(second))
    return rows


async def _save_hp_cache(rows: dict[str, tuple[float, float]]) -> None:
    path = _hp_cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    packed = {key: [value[0], value[1]] for key, value in rows.items()}
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(packed, ensure_ascii=False))


async def fetch_tower_trend(
    schedule_id: str,
    floor: int,
    current: tuple[float, float],
    count: int = 6,
) -> list[TowerTrendRow]:
    """近几期该层上下半血量合计，末期是 schedule_id 那一期。

    只补历史期，当期由调用方从已经解析好的 view 传进来，保证是最新值。
    """
    from .endgame_query import RangeRow, period_key

    context = await tower_context()
    if context is None:
        return []
    version, listing = context
    packed = [
        RangeRow(id=sid, begin=row["openTime"], end=row["closeTime"], title=row["chsBuffName"])
        for sid, row in listing.items()
    ]
    ordered = sorted(packed, key=period_key)
    at = next((pos for pos, row in enumerate(ordered) if row["id"] == schedule_id), -1)
    if at < 0:
        return []
    window = ordered[max(0, at - count + 1) : at + 1]
    cache = await _load_hp_cache()
    wanted = [row["id"] for row in window if row["id"] != schedule_id]
    missing = [sid for sid in wanted if f"{sid}:{floor}" not in cache]
    bodies = await asyncio.gather(*(fetch_json_object(f"{_DATA}/{version}/chs/tower/{sid}.json") for sid in missing))
    dirty = False
    for sid, body in zip(missing, bodies):
        if body is None:
            continue
        parsed = parse_tower_floor(body, floor, sid, listing[sid])
        if isinstance(parsed, str):
            continue
        if not floor_is_plausible(parsed):
            continue  # 血量明显是脏数据，剔掉这期，别把纵轴拉爆
        cache[f"{sid}:{floor}"] = floor_totals(parsed)
        dirty = True
    if dirty:
        await _save_hp_cache(cache)
    rows: list[TowerTrendRow] = []
    # 旧缓存可能存着修复前写进去的脏数据，这里再挡一次，顺带让它自愈
    stale = ABYSS_HP_CAP * 8
    for row in window:
        if row["id"] == schedule_id:
            totals = current
        else:
            totals = cache.get(f"{row['id']}:{floor}", (0.0, 0.0))
        if totals[0] > stale or totals[1] > stale:
            continue
        if totals[0] <= 0 and totals[1] <= 0:
            continue
        rows.append(
            TowerTrendRow(
                id=row["id"],
                label=row["title"] or row["id"],
                upper=totals[0],
                lower=totals[1],
                current=row["id"] == schedule_id,
            )
        )
    return rows


async def fetch_tower_floor(
    floor: int,
    when: datetime.date | None = None,
    schedule_id: str = "",
    shift: int = 0,
) -> tuple[TowerFloorView | None, str, str]:
    """返回 (视图, 错误, 日程对照)。上期/下期相对今天，或相对 when。"""
    context = await tower_context()
    if context is None:
        return None, "Lunaris 深渊版本号或日程取不到。", ""
    version, listing = context
    ranges = _tower_ranges(listing)
    from .endgame_query import RangeRow, choose_id

    rows = [
        RangeRow(id=sid, begin=row["openTime"], end=row["closeTime"], title=row["chsBuffName"])
        for sid, row in listing.items()
    ]
    today = datetime.date.today()
    chosen = choose_id(rows, today=today, when=when, pinned=schedule_id.strip(), shift=shift)
    if not chosen:
        if shift:
            label = "下期" if shift > 0 else "上期"
            return None, f"没有{label}深渊。", ranges
        if when is not None:
            return None, f"{when.isoformat()} 没有落在任何深渊日程里。", ranges
        if schedule_id.strip():
            return None, f"没有深渊日程 {schedule_id.strip()}。", ranges
        return None, "Lunaris 深渊日程是空的。", ranges
    tower = await fetch_json_object(f"{_DATA}/{version}/chs/tower/{chosen}.json")
    if tower is None:
        return None, f"Lunaris 深渊 {chosen} 取不到。", ranges
    parsed = parse_tower_floor(tower, floor, chosen, listing[chosen])
    if isinstance(parsed, str):
        return None, parsed, ranges
    return parsed, "", ranges


async def fetch_current_floor(floor: int, now: datetime.datetime | None = None) -> TowerFloorView | str:
    when = now.date() if now is not None else None
    viewed, error, _ranges = await fetch_tower_floor(floor, when=when)
    if viewed is None:
        return error
    return viewed
