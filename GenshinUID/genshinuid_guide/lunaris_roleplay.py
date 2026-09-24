"""幻想真境剧诗日程与幕怪物。版本号先读 version.json，空壳再往旧版本找。"""

import json
import datetime
from typing import TypedDict

import aiofiles

from .endgame_query import RangeRow, choose_id, format_ranges
from .lunaris_tower import fetch_json_object

_DATA = "https://api.lunaris.moe/data"
_TIME_FMT = "%Y-%m-%d %H:%M:%S"
_ELEM_ID = {2: "火", 3: "水", 4: "草", 5: "雷", 6: "冰", 7: "风", 8: "岩"}
_VERSION_CAP = 8
_MISS = "-"


class RoleMonster(TypedDict):
    name: str
    icon: str


class RoleRoom(TypedDict):
    index: int
    level: int
    boss_name: str
    boss_desc: str
    monsters: list[RoleMonster]
    extra: bool


class RoleView(TypedDict):
    schedule_id: str
    data_version: str
    begin: str
    end: str
    difficulty: str
    min_level: int
    room_count: int
    invite: int
    rooms: list[RoleRoom]
    note: str
    elements: list[str]


class _RoleRow(TypedDict):
    beginTime: str
    endTime: str


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


def _dict(node: dict[str, object], key: str) -> dict[str, object] | None:
    if key not in node or not isinstance(node[key], dict):
        return None
    return node[key]


def role_listing(raw: dict[str, object]) -> dict[str, _RoleRow]:
    listing: dict[str, _RoleRow] = {}
    for schedule_id, item in raw.items():
        if not isinstance(item, dict):
            continue
        begin = _text(item, "beginTime")
        end = _text(item, "endTime")
        if not begin or not end or begin.startswith("2099"):
            continue
        listing[schedule_id] = _RoleRow(beginTime=begin, endTime=end)
    return listing


def pick_role_id(listing: dict[str, _RoleRow], now: datetime.datetime) -> str:
    """仍在开放的一期优先；否则取最近一次已经开过的。"""
    current = ""
    current_open: datetime.datetime | None = None
    latest_id = ""
    latest_open: datetime.datetime | None = None
    for schedule_id, row in listing.items():
        opened = datetime.datetime.strptime(row["beginTime"], _TIME_FMT)
        closed = datetime.datetime.strptime(row["endTime"], _TIME_FMT)
        if opened <= now <= closed and (current_open is None or opened > current_open):
            current = schedule_id
            current_open = opened
        if opened <= now and (latest_open is None or opened > latest_open):
            latest_open = opened
            latest_id = schedule_id
    return current or latest_id


def _monsters(raw: object) -> list[RoleMonster]:
    if not isinstance(raw, list):
        return []
    packed: list[RoleMonster] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = _text(item, "name")
        icon = _text(item, "icon")
        if name:
            packed.append(RoleMonster(name=name, icon=icon))
    return packed


def _room(index: int, raw: dict[str, object], extra: bool) -> RoleRoom:
    return RoleRoom(
        index=index,
        level=_int(raw, "monsterLevel"),
        boss_name=_text(raw, "bossName"),
        boss_desc=_text(raw, "bossDescription"),
        monsters=_monsters(raw["monsters"] if "monsters" in raw else None),
        extra=extra,
    )


def _merge_rooms(node: dict[str, object]) -> list[RoleRoom]:
    rooms_raw = _dict(node, "rooms") or {}
    hard_raw = _dict(node, "hardRooms") or {}
    keys = set(rooms_raw) | set(hard_raw)
    ordered = sorted(keys, key=lambda item: int(item) if item.isdigit() else 999)
    room_count = _int(node, "roomCount")
    rooms: list[RoleRoom] = []
    for key in ordered:
        index = int(key) if key.isdigit() else 0
        hard = hard_raw[key] if key in hard_raw and isinstance(hard_raw[key], dict) else None
        base = rooms_raw[key] if key in rooms_raw and isinstance(rooms_raw[key], dict) else None
        chosen = hard if hard is not None and _monsters(hard["monsters"] if "monsters" in hard else None) else base
        if chosen is None:
            continue
        extra = room_count > 0 and index > room_count
        rooms.append(_room(index, chosen, extra))
    return rooms


def _best_difficulty(diff: dict[str, object]) -> tuple[str, dict[str, object]] | None:
    ranked = sorted((int(key), key) for key in diff if key.isdigit())
    for _, key in reversed(ranked):
        node = diff[key]
        if not isinstance(node, dict):
            continue
        rooms = _merge_rooms(node)
        if any(room["monsters"] or room["boss_name"] for room in rooms):
            return key, node
    return None


def _has_rooms(payload: dict[str, object]) -> bool:
    diff = _dict(payload, "difficultyConfig")
    if diff is None:
        return False
    return _best_difficulty(diff) is not None


def restricted_elements(payload: dict[str, object]) -> list[str]:
    avatar = _dict(payload, "avatarConfig")
    if avatar is None or "elementRestrictions" not in avatar:
        return []
    raw = avatar["elementRestrictions"]
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, int) and item in _ELEM_ID and _ELEM_ID[item] not in names:
            names.append(_ELEM_ID[item])
    return names


def parse_roleplay(payload: dict[str, object], schedule_id: str, data_version: str, note: str) -> RoleView | str:
    diff = _dict(payload, "difficultyConfig")
    if diff is None:
        return "Lunaris 这一期剧诗还没有幕数据。"
    chosen = _best_difficulty(diff)
    if chosen is None:
        return "Lunaris 这一期剧诗还没有幕数据。"
    best_key, node = chosen
    return RoleView(
        schedule_id=schedule_id,
        data_version=data_version,
        begin=_text(payload, "beginTime"),
        end=_text(payload, "endTime"),
        difficulty=best_key,
        min_level=_int(node, "minAvatarLevel"),
        room_count=_int(node, "roomCount"),
        invite=_int(node, "invitePoolSize"),
        rooms=_merge_rooms(node),
        note=note,
        elements=restricted_elements(payload),
    )


async def _versions() -> list[str] | str:
    payload = await fetch_json_object(f"{_DATA}/version.json")
    if payload is None:
        return "Lunaris 版本号取不到。"
    if "versions" in payload and isinstance(payload["versions"], list):
        found = [item for item in payload["versions"] if isinstance(item, str) and item]
        if found:
            return found
    if "version" in payload and isinstance(payload["version"], str) and payload["version"]:
        return [payload["version"]]
    return "Lunaris 版本号取不到。"


def _cache_path():
    from ..utils.resource.RESOURCE_PATH import WIKI_DATA_PATH

    return WIKI_DATA_PATH / "lunaris_role_version.json"


async def _load_cache() -> dict[str, str]:
    path = _cache_path()
    if not path.exists():
        return {}
    async with aiofiles.open(path, encoding="utf-8") as file:
        raw: object = json.loads(await file.read())
    if not isinstance(raw, dict):
        return {}
    found: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str) and value:
            found[key] = value
    return found


async def _store_cache(cache: dict[str, str]) -> None:
    path = _cache_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(cache, ensure_ascii=False))


async def _detail(version: str, schedule_id: str) -> dict[str, object] | None:
    return await fetch_json_object(f"{_DATA}/{version}/chs/roleplay/{schedule_id}.json")


def _cache_key(schedule_id: str, begin: str) -> str:
    return f"{schedule_id}|{begin}"


def _matches(payload: dict[str, object] | None, begin: str) -> bool:
    return payload is not None and _text(payload, "beginTime") == begin and _has_rooms(payload)


async def _cached_hit(
    schedule_id: str,
    begin: str,
    cache: dict[str, str],
) -> tuple[dict[str, object], str] | None:
    key = _cache_key(schedule_id, begin)
    if key not in cache or cache[key] == _MISS:
        return None
    cached = await _detail(cache[key], schedule_id)
    if _matches(cached, begin):
        return cached, cache[key]
    return None


async def _first_with_rooms(
    schedule_id: str,
    begin: str,
    versions: list[str],
    cache: dict[str, str],
    recheck: bool = False,
) -> tuple[dict[str, object], str] | None:
    key = _cache_key(schedule_id, begin)
    if recheck and versions:
        latest = await _detail(versions[0], schedule_id)
        if _matches(latest, begin):
            cache[key] = versions[0]
            return latest, versions[0]
    remembered = await _cached_hit(schedule_id, begin, cache)
    if remembered is not None:
        return remembered
    if key in cache and cache[key] == _MISS:
        return None
    misses = 0
    for version in versions[:_VERSION_CAP]:
        payload = await _detail(version, schedule_id)
        if payload is None:
            misses += 1
            if misses >= 2:
                break
            continue
        misses = 0
        if _matches(payload, begin):
            cache[key] = version
            return payload, version
    cache[key] = _MISS
    return None


def _role_ranges(listing: dict[str, _RoleRow]) -> str:
    rows = [RangeRow(id=sid, begin=row["beginTime"], end=row["endTime"], title="") for sid, row in listing.items()]
    return format_ranges("剧诗", rows)


async def fetch_roleplay(
    schedule_id: str = "",
    now: datetime.datetime | None = None,
    when: datetime.date | None = None,
    shift: int = 0,
) -> tuple[RoleView | None, str, str]:
    moment = now if now is not None else datetime.datetime.now()
    versions = await _versions()
    if isinstance(versions, str):
        return None, versions, ""
    listing_raw = await fetch_json_object(f"{_DATA}/{versions[0]}/roleplaylist.json")
    if listing_raw is None:
        return None, "Lunaris 剧诗日程取不到。", ""
    listing = role_listing(listing_raw)
    if not listing:
        return None, "Lunaris 剧诗日程是空的。", ""
    ranges = _role_ranges(listing)
    pinned = schedule_id.strip()
    rows = [RangeRow(id=sid, begin=row["beginTime"], end=row["endTime"], title="") for sid, row in listing.items()]
    target = choose_id(rows, today=moment.date(), when=when, pinned=pinned, shift=shift)
    if not target:
        if shift:
            label = "下期" if shift > 0 else "上期"
            return None, f"没有{label}剧诗。", ranges
        if when is not None:
            return None, f"{when.isoformat()} 没有落在任何剧诗日程里。", ranges
        if pinned:
            return None, f"Lunaris 没有剧诗日程 {pinned}。", ranges
        return None, "Lunaris 剧诗日程是空的。", ranges
    cache = await _load_cache()
    found = await _first_with_rooms(target, listing[target]["beginTime"], versions, cache, recheck=not pinned)
    note = ""
    shown = target
    if found is None and not pinned and when is None and shift == 0:
        note = "当期阵容尚未公布，下面是最近一期已经开过、并且公开了怪物的日程。"
        opened = [
            sid
            for sid in listing
            if datetime.datetime.strptime(listing[sid]["beginTime"], _TIME_FMT) <= moment and sid != target
        ]
        opened.sort(key=lambda sid: listing[sid]["beginTime"], reverse=True)
        for sid in opened:
            found = await _first_with_rooms(sid, listing[sid]["beginTime"], versions, cache)
            if found is not None:
                shown = sid
                break
    await _store_cache(cache)
    if found is None:
        row = listing[target]
        empty = RoleView(
            schedule_id=target,
            data_version=versions[0],
            begin=row["beginTime"],
            end=row["endTime"],
            difficulty="",
            min_level=0,
            room_count=0,
            invite=0,
            rooms=[],
            note="这一期怪物阵容 Lunaris 还没公布。",
            elements=[],
        )
        return empty, "", ranges
    payload, version = found
    parsed = parse_roleplay(payload, shown, version, note)
    if isinstance(parsed, str):
        return None, parsed, ranges
    return parsed, "", ranges
