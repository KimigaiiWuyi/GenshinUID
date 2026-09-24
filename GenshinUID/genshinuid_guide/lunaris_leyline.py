"""幽境危战日程。列表缓存在 data 里，新 id 出现才会再下载。"""

import json
import datetime
from typing import TypedDict

import aiofiles

from .endgame_query import RangeRow, choose_id, format_ranges
from .lunaris_tower import fetch_json_object

_HOST = "https://lunaris.moe/data/leylinechallenge"
_SEED = 5269001
_TIME_FMT = "%Y-%m-%d %H:%M:%S"
_RES_KEYS: tuple[tuple[str, str], ...] = (
    ("fireSubHurt", "火"),
    ("waterSubHurt", "水"),
    ("elecSubHurt", "雷"),
    ("iceSubHurt", "冰"),
    ("windSubHurt", "风"),
    ("rockSubHurt", "岩"),
    ("grassSubHurt", "草"),
    ("physicalSubHurt", "物"),
)


class LeyResist(TypedDict):
    name: str
    value: float


class LeyMech(TypedDict):
    name: str
    body: str


class LeyTip(TypedDict):
    text: str
    tag: str


class LeyHp(TypedDict):
    label: str
    level: int
    hp: float


class LeyLane(TypedDict):
    name: str
    icon: str
    special: str
    mechs: list[LeyMech]
    tips: list[LeyTip]
    tags: list[str]
    resists: list[LeyResist]
    hps: list[LeyHp]


class LeyView(TypedDict):
    schedule_id: str
    name: str
    begin: str
    end: str
    monster_level: int
    other_levels: list[int]
    lanes: list[LeyLane]


class _LeyMeta(TypedDict):
    id: str
    start: str
    end: str
    name: str


def _text(node: dict[str, object], key: str) -> str:
    if key not in node:
        return ""
    value = node[key]
    if isinstance(value, str):
        return value
    return ""


def _int(node: dict[str, object], key: str) -> int:
    if key not in node:
        return 0
    value = node[key]
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _float(node: dict[str, object], key: str) -> float:
    if key not in node:
        return 0.0
    value = node[key]
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def _cache_path():
    from ..utils.resource.RESOURCE_PATH import WIKI_DATA_PATH

    return WIKI_DATA_PATH / "lunaris_leyline_index.json"


def _meta(payload: dict[str, object]) -> _LeyMeta | None:
    schedule_id = _int(payload, "scheduleId")
    start = _text(payload, "scheduleStartTime")
    end = _text(payload, "scheduleEndTime")
    if not schedule_id or not start or not end:
        return None
    return _LeyMeta(id=str(schedule_id), start=start, end=end, name=_text(payload, "challengeName"))


async def _load_index() -> list[_LeyMeta]:
    path = _cache_path()
    if not path.exists():
        return []
    async with aiofiles.open(path, encoding="utf-8") as file:
        raw: object = json.loads(await file.read())
    if not isinstance(raw, list):
        return []
    rows: list[_LeyMeta] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        schedule_id = _text(item, "id")
        start = _text(item, "start")
        end = _text(item, "end")
        if schedule_id and start and end:
            rows.append(_LeyMeta(id=schedule_id, start=start, end=end, name=_text(item, "name")))
    return rows


async def _save_index(rows: list[_LeyMeta]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(rows, ensure_ascii=False))


async def _body(schedule_id: str) -> dict[str, object] | None:
    return await fetch_json_object(f"{_HOST}/{schedule_id}.json")


def pick_ley_id(rows: list[_LeyMeta], now: datetime.datetime) -> str:
    current = ""
    current_open: datetime.datetime | None = None
    latest_id = ""
    latest_open: datetime.datetime | None = None
    for row in rows:
        opened = datetime.datetime.strptime(row["start"], _TIME_FMT)
        closed = datetime.datetime.strptime(row["end"], _TIME_FMT)
        if opened <= now <= closed and (current_open is None or opened > current_open):
            current = row["id"]
            current_open = opened
        if opened <= now and (latest_open is None or opened > latest_open):
            latest_open = opened
            latest_id = row["id"]
    return current or latest_id


def _slots(node: dict[str, object], key: str) -> list[str]:
    if key not in node:
        return []
    value = node[key]
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [item if isinstance(item, str) else "" for item in value]


def _lane(raw: dict[str, object]) -> LeyLane | None:
    name = _text(raw, "chsLevelName")
    if not name:
        return None
    tags: list[str] = []
    if "tagType" in raw and isinstance(raw["tagType"], list):
        for tag in raw["tagType"]:
            if isinstance(tag, str) and tag and tag != "None":
                tags.append("优势" if tag == "Advantage" else tag)
    resists: list[LeyResist] = []
    stats = raw["monsterStats"] if "monsterStats" in raw and isinstance(raw["monsterStats"], dict) else None
    if stats is not None:
        for key, label in _RES_KEYS:
            resists.append(LeyResist(name=label, value=_float(stats, key)))
    names = _slots(raw, "chsMonsterSpecialMechanicName")
    bodies = _slots(raw, "chsLevelMaxDescription")
    if not any(bodies):
        bodies = _slots(raw, "chsLevelMinDescription")
    mechs: list[LeyMech] = []
    for index in range(max(len(names), len(bodies))):
        title = names[index] if index < len(names) else ""
        body = bodies[index] if index < len(bodies) else ""
        if title or body:
            mechs.append(LeyMech(name=title, body=body))
    raw_tips = _slots(raw, "chsRecommendedLevelMechanic")
    tips = [
        LeyTip(text=text, tag=tags[index] if index < len(tags) else "") for index, text in enumerate(raw_tips) if text
    ]
    return LeyLane(
        name=name,
        icon=_text(raw, "specialMonsterIcon"),
        special=_text(raw, "chsMonsterSpecialDesc"),
        mechs=mechs,
        tips=tips,
        tags=tags,
        resists=resists,
        hps=[],
    )


def _stats_hp(raw: dict[str, object]) -> float:
    stats = raw["monsterStats"] if "monsterStats" in raw and isinstance(raw["monsterStats"], dict) else None
    if stats is None:
        return 0.0
    return _float(stats, "hp")


def _config_map(level: dict[str, object]) -> dict[str, dict[str, object]]:
    configs = level["levelConfigs"] if "levelConfigs" in level else None
    found: dict[str, dict[str, object]] = {}
    if not isinstance(configs, list):
        return found
    for item in configs:
        if not isinstance(item, dict):
            continue
        icon = _text(item, "specialMonsterIcon")
        if icon:
            found[icon] = item
    return found


def parse_leyline(payload: dict[str, object]) -> LeyView | str:
    meta = _meta(payload)
    if meta is None:
        return "Lunaris 幽境危战日程不完整。"
    levels = payload["levels"] if "levels" in payload else None
    if not isinstance(levels, list) or not levels:
        return "Lunaris 幽境危战没有难度。"
    by_level: dict[int, dict[str, object]] = {}
    for item in levels:
        if isinstance(item, dict):
            by_level[_int(item, "monsterLevel")] = item
    hard = by_level[110] if 110 in by_level else None
    if hard is None:
        return "Lunaris 幽境危战没有 N6。"
    mid = by_level[105] if 105 in by_level else None
    mid_map = _config_map(mid) if mid is not None else {}
    configs = hard["levelConfigs"] if "levelConfigs" in hard else None
    if not isinstance(configs, list):
        return "Lunaris 幽境危战没有关卡。"
    lanes: list[LeyLane] = []
    for item in configs:
        if not isinstance(item, dict):
            continue
        lane = _lane(item)
        if lane is None:
            continue
        hps: list[LeyHp] = []
        icon = lane["icon"]
        if icon in mid_map:
            hps.append(LeyHp(label="N5", level=105, hp=_stats_hp(mid_map[icon])))
        hps.append(LeyHp(label="N6", level=110, hp=_stats_hp(item)))
        lane["hps"] = hps
        lanes.append(lane)
    if not lanes:
        return "Lunaris 幽境危战没有关卡。"
    return LeyView(
        schedule_id=meta["id"],
        name=meta["name"] or "幽境危战",
        begin=meta["start"],
        end=meta["end"],
        monster_level=110,
        other_levels=[105] if mid is not None else [],
        lanes=lanes,
    )


def _ley_ranges(rows: list[_LeyMeta]) -> str:
    packed = [RangeRow(id=row["id"], begin=row["start"], end=row["end"], title=row["name"]) for row in rows]
    return format_ranges("幽境危战", packed)


async def fetch_leyline(
    schedule_id: str = "",
    now: datetime.datetime | None = None,
    when: datetime.date | None = None,
    shift: int = 0,
) -> tuple[LeyView | None, str, str]:
    moment = now if now is not None else datetime.datetime.now()
    rows = await _load_index()
    fresh: dict[str, dict[str, object]] = {}
    start = _SEED
    if rows:
        start = max(int(row["id"]) for row in rows) + 1
    misses = 0
    cursor = start
    while misses < 2 and cursor < _SEED + 40:
        payload = await _body(str(cursor))
        if payload is None:
            misses += 1
            cursor += 1
            continue
        misses = 0
        meta = _meta(payload)
        if meta is not None:
            rows = [row for row in rows if row["id"] != meta["id"]]
            rows.append(meta)
            fresh[meta["id"]] = payload
        cursor += 1
    await _save_index(rows)
    ranges = _ley_ranges(rows)
    pinned = schedule_id.strip()
    if pinned and pinned not in {row["id"] for row in rows}:
        payload = await _body(pinned)
        if payload is None:
            return None, f"Lunaris 没有幽境危战 {pinned}。", ranges
        meta = _meta(payload)
        if meta is None:
            return None, f"Lunaris 没有幽境危战 {pinned}。", ranges
        rows.append(meta)
        fresh[pinned] = payload
        await _save_index(rows)
        ranges = _ley_ranges(rows)
    packed = [RangeRow(id=row["id"], begin=row["start"], end=row["end"], title=row["name"]) for row in rows]
    chosen = choose_id(packed, today=moment.date(), when=when, pinned=pinned, shift=shift)
    if not chosen:
        if shift:
            label = "下期" if shift > 0 else "上期"
            return None, f"没有{label}幽境危战。", ranges
        if when is not None:
            return None, f"{when.isoformat()} 没有落在任何幽境危战日程里。", ranges
        if pinned:
            return None, f"Lunaris 没有幽境危战 {pinned}。", ranges
        return None, "Lunaris 幽境危战日程是空的。", ranges
    body = fresh[chosen] if chosen in fresh else await _body(chosen)
    if body is None:
        return None, f"Lunaris 幽境危战 {chosen} 取不到。", ranges
    parsed = parse_leyline(body)
    if isinstance(parsed, str):
        return None, parsed, ranges
    return parsed, "", ranges
