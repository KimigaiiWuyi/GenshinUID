"""Akasha substat priority：加一发五星满幅副词条后的榜单收益。

请求：``GET /api/substatPriority/{uid}/{md5}``。
``% gain over base = 100 * result / Base.result - 100``。
这是**当前这套配装**的模拟，不是全服表。
"""

from __future__ import annotations

from .models import (
    SubstatGain,
    SubstatRoll,
    SubstatWeapon,
    SubstatCalculation,
    SubstatPriorityItem,
    SubstatPriorityBoard,
)

# 前端始终展示这三列，即使 result 与 Base 相同
ALWAYS_VISIBLE_SUBSTATS: frozenset[str] = frozenset({"Base", "Crit RATE", "Crit DMG"})


def pct_gain_over_base(result: float, base_result: float) -> float:
    """相对 Base 榜分的百分比增益。

    对应页面行 ``% gain over base``：``100 * result / Base.result - 100``。
    ``base_result`` 必须非 0（Akasha 的 Base.result 是模拟伤害，正常 > 0）。
    """
    return 100.0 * result / base_result - 100.0


def dmg_gain_over_base(result: float, base_result: float) -> float:
    """相对 Base 榜分的绝对增量，对应页面行 ``DMG/Result gain over base``。"""
    return result - base_result


def should_show_substat(name: str, result: float, base_result: float) -> bool:
    """是否在表里显示该副词条列。

    与前端一致：``Base`` / 暴击 / 爆伤始终保留；
    其余列若 ``result == Base.result``（加这一发不改伤害）则隐藏。
    """
    if name in ALWAYS_VISIBLE_SUBSTATS:
        return True
    return result != base_result


def parse_substat_priority_payload(raw: object) -> list[SubstatPriorityItem] | None:
    """把 ``/api/substatPriority/{uid}/{md5}`` 的 JSON 收成 TypedDict 列表。

    ``raw`` 为接口整包（含 ``data``）。结构对不上时返回 ``None``。
    """
    if not isinstance(raw, dict):
        return None
    if "data" not in raw:
        return None
    data = raw["data"]
    if not isinstance(data, list):
        return None
    items: list[SubstatPriorityItem] = []
    for entry in data:
        parsed = _parse_item(entry)
        if parsed is None:
            return None
        items.append(parsed)
    return items


def compute_substat_priority_board(item: SubstatPriorityItem) -> SubstatPriorityBoard:
    """把单条榜的 raw substats 算成页面同款增益表。

    每列是「在当前配装上再加 ``substatValue``（一发五星满幅）后」重算的榜分。
    ``rank_delta = old_rank - new_rank``，正数表示名次上升。
    """
    substats = item["substats"]
    base = substats["Base"]
    base_result = base["result"]
    gains: list[SubstatGain] = []
    for name, roll in substats.items():
        if name == "Base":
            continue
        result = roll["result"]
        if not should_show_substat(name, result, base_result):
            continue
        old_rank = roll["oldRank"]
        new_rank = roll["newRank"]
        gains.append(
            {
                "name": name,
                "roll": roll["substatValue"],
                "result": result,
                "dmg_gain": dmg_gain_over_base(result, base_result),
                "pct_gain": pct_gain_over_base(result, base_result),
                "old_rank": old_rank,
                "new_rank": new_rank,
                "out_of": roll["outOf"],
                "rank_delta": old_rank - new_rank,
            }
        )
    calc = item["calculation"]
    return {
        "calculation_id": calc["calculationId"],
        "name": calc["name"],
        "short": calc["short"],
        "weapon_name": calc["weapon"]["name"],
        "variant": calc["variant"],
        "hidden": calc["hidden"],
        "base_result": base_result,
        "base_rank": base["oldRank"],
        "out_of": base["outOf"],
        "gains": gains,
    }


def compute_substat_priority_boards(
    items: list[SubstatPriorityItem],
    *,
    include_hidden: bool = False,
) -> list[SubstatPriorityBoard]:
    """批量计算。默认丢掉 ``calculation.hidden`` 的榜（与前端一致）。"""
    boards: list[SubstatPriorityBoard] = []
    for item in items:
        if item["calculation"]["hidden"] and not include_hidden:
            continue
        boards.append(compute_substat_priority_board(item))
    return boards


def find_substat_priority_board(
    boards: list[SubstatPriorityBoard],
    calculation_id: str,
) -> SubstatPriorityBoard | None:
    """按 ``calculationId``（可带 ``170er`` 后缀）取一条增益表。"""
    for board in boards:
        if board["calculation_id"] == calculation_id:
            return board
    return None


def _parse_item(raw: object) -> SubstatPriorityItem | None:
    if not isinstance(raw, dict):
        return None
    if "calculation" not in raw or "substats" not in raw:
        return None
    calc = _parse_calculation(raw["calculation"])
    substats = _parse_substats(raw["substats"])
    if calc is None or substats is None:
        return None
    if "Base" not in substats:
        return None
    return {"calculation": calc, "substats": substats}


def _parse_calculation(raw: object) -> SubstatCalculation | None:
    if not isinstance(raw, dict):
        return None
    needed = ("calculationId", "name", "short", "weapon")
    for key in needed:
        if key not in raw:
            return None
    weapon = _parse_weapon(raw["weapon"])
    if weapon is None:
        return None
    calc_id = raw["calculationId"]
    name = raw["name"]
    short = raw["short"]
    if not isinstance(calc_id, str) or not isinstance(name, str) or not isinstance(short, str):
        return None
    variant: str | None = None
    if "variant" in raw and isinstance(raw["variant"], str):
        variant = raw["variant"]
    hidden = False
    if "hidden" in raw and isinstance(raw["hidden"], bool):
        hidden = raw["hidden"]
    return {
        "calculationId": calc_id,
        "name": name,
        "short": short,
        "weapon": weapon,
        "variant": variant,
        "hidden": hidden,
    }


def _parse_weapon(raw: object) -> SubstatWeapon | None:
    if not isinstance(raw, dict):
        return None
    needed = ("name", "icon", "substat", "type", "rarity", "weaponId", "refinement")
    for key in needed:
        if key not in raw:
            return None
    name = raw["name"]
    icon = raw["icon"]
    substat = raw["substat"]
    wtype = raw["type"]
    rarity = raw["rarity"]
    weapon_id = raw["weaponId"]
    refinement = raw["refinement"]
    if not isinstance(name, str) or not isinstance(icon, str):
        return None
    if not isinstance(substat, str) or not isinstance(wtype, str):
        return None
    if not isinstance(rarity, int) or not isinstance(refinement, int):
        return None
    if isinstance(weapon_id, int):
        weapon_id_s = str(weapon_id)
    elif isinstance(weapon_id, str):
        weapon_id_s = weapon_id
    else:
        return None
    return {
        "name": name,
        "icon": icon,
        "substat": substat,
        "type": wtype,
        "rarity": rarity,
        "weaponId": weapon_id_s,
        "refinement": refinement,
    }


def _parse_substats(raw: object) -> dict[str, SubstatRoll] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, SubstatRoll] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            return None
        roll = _parse_roll(value)
        if roll is None:
            return None
        out[key] = roll
    return out


def _parse_roll(raw: object) -> SubstatRoll | None:
    if not isinstance(raw, dict):
        return None
    needed = ("result", "substatValue", "newRank", "oldRank", "outOf")
    for key in needed:
        if key not in raw:
            return None
    result = _as_float(raw["result"])
    substat_value = _as_float(raw["substatValue"])
    new_rank = _as_int(raw["newRank"])
    old_rank = _as_int(raw["oldRank"])
    out_of = _as_int(raw["outOf"])
    if result is None or substat_value is None:
        return None
    if new_rank is None or old_rank is None or out_of is None:
        return None
    return {
        "result": result,
        "substatValue": substat_value,
        "newRank": new_rank,
        "oldRank": old_rank,
        "outOf": out_of,
    }


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
