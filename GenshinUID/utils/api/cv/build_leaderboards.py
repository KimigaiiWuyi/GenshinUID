"""Akasha 角色卡 Hide/Show leaderboards：这套配装在各队伍榜上的名次。

请求：``GET /api/leaderboards/{uid}/{md5}?variant=profilePage``。
``data.calculations`` 按 ``calculationId``（可带 ``170er`` 后缀）索引。
名次 / 伤害分 / 队友是**当前这套装**的模拟，每次请求都会变。

``top N% = ceil(ranking / outOf * 10**decimals * 100) / 10**decimals``。
默认 ``decimals=0`` 再 ``min(100, …)``，与前端 ``topDecimals=0`` 一致。
"""

from __future__ import annotations

import math

from .models import (
    Teammate,
    SubstatWeapon,
    TeammateWeapon,
    TeammateCharacter,
    BuildLeaderboardRow,
)


def top_percentile(ranking: int, out_of: int, *, decimals: int = 0) -> float:
    """角色卡 ``top N%``。

    ``decimals=0``：``min(100, ceil(ranking / outOf * 100))``。
    ``out_of`` 必须 > 0。
    """
    if decimals == 0:
        return float(min(100, math.ceil(ranking / out_of * 100.0)))
    scale = 10**decimals
    return math.ceil(ranking / out_of * scale * 100.0) / scale


def parse_build_leaderboards_payload(
    raw: object,
    *,
    decimals: int = 0,
) -> list[BuildLeaderboardRow] | None:
    """把 ``/api/leaderboards/{uid}/{md5}`` 的 JSON 收成行列表。

    含 ``hidden`` 的榜；不排序。结构对不上时返回 ``None``。
    """
    if not isinstance(raw, dict) or "data" not in raw:
        return None
    data = raw["data"]
    if not isinstance(data, dict) or "calculations" not in data:
        return None
    calculations = data["calculations"]
    if not isinstance(calculations, dict):
        return None
    rows: list[BuildLeaderboardRow] = []
    for key, entry in calculations.items():
        if not isinstance(key, str):
            return None
        parsed = _parse_row(key, entry, decimals=decimals)
        if parsed is None:
            return None
        rows.append(parsed)
    return rows


def list_visible_leaderboards(
    rows: list[BuildLeaderboardRow],
    *,
    include_hidden: bool = False,
) -> list[BuildLeaderboardRow]:
    """过滤 ``hidden`` 后按名次升序，与前端 ``calculation-list`` 一致。"""
    visible = [row for row in rows if include_hidden or not row["hidden"]]
    return sorted(visible, key=lambda row: row["ranking"])


def find_build_leaderboard(
    rows: list[BuildLeaderboardRow],
    calculation_id: str,
) -> BuildLeaderboardRow | None:
    """按 ``calculationId``（可带 ``170er`` 后缀）取一条。"""
    for row in rows:
        if row["calculation_id"] == calculation_id:
            return row
    return None


def extract_build_md5(raw: object, character_id: str) -> str | None:
    """从 ``/api/builds?uid=`` 取某角色当前配装 ``md5``。

    优先 ``type == current``；否则取该 ``characterId`` 的第一条。
    """
    if not isinstance(raw, dict) or "data" not in raw:
        return None
    data = raw["data"]
    if not isinstance(data, list):
        return None
    fallback: str | None = None
    for entry in data:
        if not isinstance(entry, dict) or "md5" not in entry:
            continue
        md5 = entry["md5"]
        if not isinstance(md5, str) or not md5:
            continue
        cid = _entry_character_id(entry)
        if cid != character_id:
            continue
        kind = ""
        if "type" in entry and isinstance(entry["type"], str):
            kind = entry["type"]
        if kind == "current":
            return md5
        if fallback is None:
            fallback = md5
    return fallback


def _entry_character_id(entry: dict[str, object]) -> str | None:
    if "characterId" not in entry:
        return None
    raw = entry["characterId"]
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return str(raw)
    if isinstance(raw, str) and raw:
        return raw
    return None


def _parse_row(key: str, raw: object, *, decimals: int) -> BuildLeaderboardRow | None:
    if not isinstance(raw, dict):
        return None
    needed = ("short", "name", "ranking", "outOf", "result", "weapon", "teammates")
    for field in needed:
        if field not in raw:
            return None
    short = raw["short"]
    name = raw["name"]
    if not isinstance(short, str) or not isinstance(name, str):
        return None
    ranking = _as_rank(raw["ranking"])
    out_of = _as_int(raw["outOf"])
    result = _as_float(raw["result"])
    if ranking is None or out_of is None or out_of <= 0 or result is None:
        return None
    weapon = _parse_weapon(raw["weapon"])
    teammates = _parse_teammates(raw["teammates"])
    if weapon is None or teammates is None:
        return None
    # 变体行的 calculationId 字段不含 170er；dict key 才是唯一键
    hidden = False
    if "hidden" in raw and isinstance(raw["hidden"], bool):
        hidden = raw["hidden"]
    priority = 0
    if "priority" in raw and raw["priority"] is not None:
        parsed_priority = _as_int(raw["priority"])
        if parsed_priority is None:
            return None
        priority = parsed_priority
    label: str | None = None
    if "label" in raw and isinstance(raw["label"], str) and raw["label"]:
        label = raw["label"]
    variant_name: str | None = None
    variant_display: str | None = None
    if "variant" in raw and isinstance(raw["variant"], dict):
        variant = raw["variant"]
        if "name" in variant and isinstance(variant["name"], str) and variant["name"]:
            variant_name = variant["name"]
        if "displayName" in variant and isinstance(variant["displayName"], str):
            variant_display = variant["displayName"]
    return {
        "calculation_id": key,
        "short": short,
        "name": name,
        "ranking": ranking,
        "out_of": out_of,
        "result": result,
        "top_pct": top_percentile(ranking, out_of, decimals=decimals),
        "hidden": hidden,
        "priority": priority,
        "label": label,
        "variant_name": variant_name,
        "variant_display": variant_display,
        "weapon": weapon,
        "teammates": teammates,
    }


def _parse_weapon(raw: object) -> SubstatWeapon | None:
    if not isinstance(raw, dict):
        return None
    needed = ("name", "icon", "substat", "type", "rarity", "weaponId", "refinement")
    for field in needed:
        if field not in raw:
            return None
    name = raw["name"]
    icon = raw["icon"]
    substat = raw["substat"]
    wtype = raw["type"]
    rarity = _as_int(raw["rarity"])
    refinement = _as_int(raw["refinement"])
    weapon_id = _as_weapon_id(raw["weaponId"])
    if not isinstance(name, str) or not isinstance(icon, str):
        return None
    if not isinstance(substat, str) or not isinstance(wtype, str):
        return None
    if rarity is None or refinement is None or weapon_id is None:
        return None
    return {
        "name": name,
        "icon": icon,
        "substat": substat,
        "type": wtype,
        "rarity": rarity,
        "weaponId": weapon_id,
        "refinement": refinement,
    }


def _parse_teammates(raw: object) -> list[Teammate] | None:
    if not isinstance(raw, list):
        return None
    out: list[Teammate] = []
    for entry in raw:
        parsed = _parse_teammate(entry)
        if parsed is None:
            return None
        out.append(parsed)
    return out


def _parse_teammate(raw: object) -> Teammate | None:
    if not isinstance(raw, dict) or "character" not in raw:
        return None
    character = _parse_teammate_character(raw["character"])
    if character is None:
        return None
    weapon: TeammateWeapon | None = None
    if "weapon" in raw and raw["weapon"] is not None:
        weapon = _parse_teammate_weapon(raw["weapon"])
        if weapon is None:
            return None
    return {"character": character, "weapon": weapon}


def _parse_teammate_character(raw: object) -> TeammateCharacter | None:
    if not isinstance(raw, dict):
        return None
    needed = ("name", "element", "rarity", "icon")
    for field in needed:
        if field not in raw:
            return None
    name = raw["name"]
    element = raw["element"]
    icon = raw["icon"]
    rarity = _as_int(raw["rarity"])
    if not isinstance(name, str) or not isinstance(element, str) or not isinstance(icon, str):
        return None
    if rarity is None:
        return None
    constellation: int | None = None
    if "constellation" in raw:
        constellation = _as_int(raw["constellation"])
        if constellation is None:
            return None
    artifact_set: str | None = None
    if "artifactSet" in raw and isinstance(raw["artifactSet"], str):
        artifact_set = raw["artifactSet"]
    artifact_set_icon: str | None = None
    if "artifactSetIcon" in raw and isinstance(raw["artifactSetIcon"], str):
        artifact_set_icon = raw["artifactSetIcon"]
    return {
        "name": name,
        "element": element,
        "rarity": rarity,
        "icon": icon,
        "constellation": constellation,
        "artifact_set": artifact_set,
        "artifact_set_icon": artifact_set_icon,
    }


def _parse_teammate_weapon(raw: object) -> TeammateWeapon | None:
    if not isinstance(raw, dict):
        return None
    needed = ("name", "icon", "rarity", "refinement", "weaponId")
    for field in needed:
        if field not in raw:
            return None
    name = raw["name"]
    icon = raw["icon"]
    rarity = _as_int(raw["rarity"])
    refinement = _as_int(raw["refinement"])
    weapon_id = _as_weapon_id(raw["weaponId"])
    if not isinstance(name, str) or not isinstance(icon, str):
        return None
    if rarity is None or refinement is None or weapon_id is None:
        return None
    return {
        "name": name,
        "icon": icon,
        "rarity": rarity,
        "refinement": refinement,
        "weapon_id": weapon_id,
    }


def _as_weapon_id(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value:
        return value
    return None


def _as_rank(value: object) -> int | None:
    # 前端会把 ``~123`` / ``(123)`` 剥掉再比大小
    if isinstance(value, str):
        text = value.replace("~", "")
        if text.startswith("(") and text.endswith(")") and len(text) >= 2:
            text = text[1:-1]
        if text.isdigit():
            return int(text)
        return None
    return _as_int(value)


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
