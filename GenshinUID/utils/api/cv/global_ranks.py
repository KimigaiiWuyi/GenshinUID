"""Akasha 全服榜：``GET /api/leaderboards?sort=calculation.result&calculationId=``。

与 ``gs角色排名`` 同一接口。``size`` 控制条数；``out_of`` 用队伍榜 ``outOf``。
"""

from __future__ import annotations

from .models import GlobalRankRow
from .build_leaderboards import top_percentile


def parse_global_ranks_payload(raw: object, out_of: int) -> list[GlobalRankRow] | None:
    """把全服榜 JSON 收成行。结构对不上时返回 ``None``。"""
    if out_of <= 0:
        return None
    if not isinstance(raw, dict) or "data" not in raw:
        return None
    data = raw["data"]
    if not isinstance(data, list):
        return None
    out: list[GlobalRankRow] = []
    for entry in data:
        parsed = _parse_row(entry, out_of)
        if parsed is None:
            return None
        out.append(parsed)
    return out


def _parse_row(raw: object, out_of: int) -> GlobalRankRow | None:
    if not isinstance(raw, dict):
        return None
    if "uid" not in raw or "index" not in raw or "calculation" not in raw:
        return None
    uid = raw["uid"]
    if not isinstance(uid, str) or not uid:
        return None
    rank = _as_int(raw["index"])
    if rank is None or rank <= 0:
        return None
    calc = raw["calculation"]
    if not isinstance(calc, dict) or "result" not in calc:
        return None
    result = _as_float(calc["result"])
    if result is None:
        return None
    constellation = 0
    if "constellation" in raw:
        parsed_c = _as_int(raw["constellation"])
        if parsed_c is not None:
            constellation = parsed_c
    nickname = ""
    region = ""
    if "owner" in raw and isinstance(raw["owner"], dict):
        owner = raw["owner"]
        if "nickname" in owner and isinstance(owner["nickname"], str):
            nickname = owner["nickname"]
        if "region" in owner and isinstance(owner["region"], str):
            region = owner["region"]
    weapon_name = ""
    weapon_id = ""
    refinement = 1
    if "weapon" in raw and isinstance(raw["weapon"], dict):
        weapon = raw["weapon"]
        if "name" in weapon and isinstance(weapon["name"], str):
            weapon_name = weapon["name"]
        if "weaponId" in weapon:
            wid = weapon["weaponId"]
            if isinstance(wid, int):
                weapon_id = str(wid)
            elif isinstance(wid, str) and wid:
                weapon_id = wid
        if "weaponInfo" in weapon and isinstance(weapon["weaponInfo"], dict):
            info = weapon["weaponInfo"]
            if "refinementLevel" in info and isinstance(info["refinementLevel"], dict):
                level = info["refinementLevel"]
                if "value" in level:
                    parsed_r = _as_int(level["value"])
                    if parsed_r is not None:
                        refinement = parsed_r + 1
    cv = 0.0
    if "critValue" in raw:
        parsed_cv = _as_float(raw["critValue"])
        if parsed_cv is not None:
            cv = parsed_cv
    stats = raw["stats"] if "stats" in raw else None
    character_id = ""
    if "characterId" in raw:
        cid = raw["characterId"]
        if isinstance(cid, int):
            character_id = str(cid)
        elif isinstance(cid, str) and cid:
            character_id = cid
    return {
        "rank": rank,
        "out_of": out_of,
        "top_pct": top_percentile(rank, out_of),
        "uid": uid,
        "nickname": nickname,
        "region": region,
        "constellation": constellation,
        "weapon_name": weapon_name,
        "weapon_id": weapon_id,
        "refinement": refinement,
        "result": result,
        "crit_rate": _nested_stat(stats, "critRate"),
        "crit_dmg": _nested_stat(stats, "critDamage"),
        "cv": cv,
        "hp": _nested_stat(stats, "maxHp"),
        "atk": _nested_stat(stats, "atk"),
        "character_id": character_id,
    }


def _nested_stat(stats: object, key: str) -> float:
    if not isinstance(stats, dict) or key not in stats:
        return 0.0
    node = stats[key]
    if isinstance(node, dict) and "value" in node:
        parsed = _as_float(node["value"])
        if parsed is not None:
            return parsed
        return 0.0
    parsed = _as_float(node)
    if parsed is not None:
        return parsed
    return 0.0


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
