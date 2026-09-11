"""Akasha 角色卡 Show damage distribution：这套装在各榜上的伤害拆分。

请求：``GET /api/damageDistribution/{calculationId}/{uid}/{md5}``。
``calculationId`` 取榜 ID 前 10 位（去掉 ``170er``）。一次返回该角色全部队伍榜。
``additional[]`` 是**当前这套装**各技能/反应的模拟伤害，换玩家会变。

``% of Result = 100 * value * quantity / base``。
有 ``name=Time`` 时 ``base`` 为去掉 Time 后的分段合计，并 ``dps = result``。
否则 ``base`` 为 ``result``。
"""

from __future__ import annotations

from typing import TypedDict

from .models import (
    DamagePart,
    SubstatWeapon,
    DamageDistributionBoard,
)


class _CalcMeta(TypedDict):
    name: str
    short: str
    weapon: SubstatWeapon
    hidden: bool


TIME_NAME = "Time"
BOARD_ID_LEN = 10


def board_calculation_id(calculation_id: str) -> str:
    """前端 ``selectedCalculationId.slice(0, 10)``，去掉 ``170er`` 后缀。"""
    return calculation_id[:BOARD_ID_LEN]


def part_total(value: float, quantity: float) -> float:
    """分段合计：``value * quantity``。"""
    return value * quantity


def pct_of_result(total: float, base: float) -> float:
    """页面 ``% of Result``：``100 * total / base``。

    ``base`` 必须非 0。有 Time 时用去掉 Time 的分段合计，否则用 ``result``。
    """
    return 100.0 * total / base


def parse_damage_distribution_payload(raw: object) -> list[DamageDistributionBoard] | None:
    """把 ``/api/damageDistribution/{id}/{uid}/{md5}`` 的 JSON 收成榜列表。

    含 ``hidden`` 的榜；不排序。结构对不上时返回 ``None``。
    """
    if not isinstance(raw, dict) or "data" not in raw:
        return None
    data = raw["data"]
    if not isinstance(data, list):
        return None
    boards: list[DamageDistributionBoard] = []
    for entry in data:
        parsed = _parse_board(entry)
        if parsed is None:
            return None
        boards.append(parsed)
    return boards


def list_visible_distributions(
    boards: list[DamageDistributionBoard],
    *,
    include_hidden: bool = False,
) -> list[DamageDistributionBoard]:
    """丢掉 ``calculation.hidden``（与前端 Select leaderboard 一致）。"""
    return [board for board in boards if include_hidden or not board["hidden"]]


def find_damage_distribution(
    boards: list[DamageDistributionBoard],
    calculation_id: str,
) -> DamageDistributionBoard | None:
    """按榜 ID 取一条；``170er`` 后缀会被去掉再比。"""
    wanted = board_calculation_id(calculation_id)
    for board in boards:
        if board["calculation_id"] == wanted:
            return board
    return None


def _parse_board(raw: object) -> DamageDistributionBoard | None:
    if not isinstance(raw, dict):
        return None
    needed = ("id", "result", "additional", "calculation")
    for field in needed:
        if field not in raw:
            return None
    calc_id = raw["id"]
    if isinstance(calc_id, int):
        calc_id_s = str(calc_id)
    elif isinstance(calc_id, str) and calc_id:
        calc_id_s = calc_id
    else:
        return None
    result = _as_float(raw["result"])
    if result is None:
        return None
    calc = _parse_calculation(raw["calculation"])
    parts_raw = _parse_additional(raw["additional"])
    if calc is None or parts_raw is None:
        return None
    time_sec: float | None = None
    parts_src: list[tuple[str, float, float, str]] = []
    for name, value, quantity, part_type in parts_raw:
        if name == TIME_NAME:
            time_sec = value
            continue
        parts_src.append((name, value, quantity, part_type))
    formula_sum = 0.0
    for _name, value, quantity, _typ in parts_src:
        formula_sum += part_total(value, quantity)
    has_time = time_sec is not None
    base = formula_sum if has_time else result
    if base == 0:
        return None
    parts: list[DamagePart] = []
    for name, value, quantity, part_type in parts_src:
        total = part_total(value, quantity)
        parts.append(
            {
                "name": name,
                "value": value,
                "quantity": quantity,
                "type": part_type,
                "total": total,
                "pct": pct_of_result(total, base),
            }
        )
    dps: float | None = result if has_time else None
    return {
        "calculation_id": calc_id_s,
        "name": calc["name"],
        "short": calc["short"],
        "weapon_name": calc["weapon"]["name"],
        "weapon_id": calc["weapon"]["weaponId"],
        "hidden": calc["hidden"],
        "result": result,
        "formula_sum": formula_sum,
        "time_sec": time_sec,
        "dps": dps,
        "parts": parts,
    }


def _parse_calculation(raw: object) -> _CalcMeta | None:
    if not isinstance(raw, dict):
        return None
    if "name" not in raw or "short" not in raw or "weapon" not in raw:
        return None
    name = raw["name"]
    short = raw["short"]
    if not isinstance(name, str) or not isinstance(short, str):
        return None
    weapon = _parse_weapon(raw["weapon"])
    if weapon is None:
        return None
    hidden = False
    if "hidden" in raw and isinstance(raw["hidden"], bool):
        hidden = raw["hidden"]
    return {"name": name, "short": short, "weapon": weapon, "hidden": hidden}


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


def _parse_additional(raw: object) -> list[tuple[str, float, float, str]] | None:
    if not isinstance(raw, list):
        return None
    out: list[tuple[str, float, float, str]] = []
    for entry in raw:
        parsed = _parse_part(entry)
        if parsed is None:
            return None
        out.append(parsed)
    return out


def _parse_part(raw: object) -> tuple[str, float, float, str] | None:
    if not isinstance(raw, dict) or "name" not in raw or "value" not in raw:
        return None
    name = raw["name"]
    if not isinstance(name, str) or not name:
        return None
    value = _as_float(raw["value"])
    if value is None:
        return None
    quantity = 1.0
    if "quantity" in raw:
        parsed_q = _as_float(raw["quantity"])
        if parsed_q is None:
            return None
        quantity = parsed_q
    part_type = "?"
    if "type" in raw and isinstance(raw["type"], str) and raw["type"]:
        part_type = raw["type"]
    return (name, value, quantity, part_type)


def _as_weapon_id(value: object) -> str | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value:
        return value
    return None


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
