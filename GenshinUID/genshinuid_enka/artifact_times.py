"""圣遗物副词条强化次数与档位。

Enka：`reliquary.appendPropIdList` 每项是一次掷骰，`id // 10` 为词条族，
末位 1–4 为档位（4 最高）。出现次数减 1 即强化次数。
米游社：`times` 已是强化次数；满值用「当前值 vs 单次上限 × 次数」推断。
"""

from __future__ import annotations

from typing import Mapping, Sequence, MutableMapping

AFFIX_FAMILY_TO_PROP: dict[int, str] = {
    50102: "FIGHT_PROP_HP",
    50103: "FIGHT_PROP_HP_PERCENT",
    50105: "FIGHT_PROP_ATTACK",
    50106: "FIGHT_PROP_ATTACK_PERCENT",
    50108: "FIGHT_PROP_DEFENSE",
    50109: "FIGHT_PROP_DEFENSE_PERCENT",
    50120: "FIGHT_PROP_CRITICAL",
    50122: "FIGHT_PROP_CRITICAL_HURT",
    50123: "FIGHT_PROP_CHARGE_EFFICIENCY",
    50124: "FIGHT_PROP_ELEMENT_MASTERY",
}

# 五星副词条单次上限（社区常用表）
_MAX_ROLL_5: dict[str, float] = {
    "FIGHT_PROP_HP": 298.75,
    "FIGHT_PROP_HP_PERCENT": 5.83,
    "FIGHT_PROP_ATTACK": 19.45,
    "FIGHT_PROP_ATTACK_PERCENT": 5.83,
    "FIGHT_PROP_DEFENSE": 23.15,
    "FIGHT_PROP_DEFENSE_PERCENT": 7.29,
    "FIGHT_PROP_CRITICAL": 3.89,
    "FIGHT_PROP_CRITICAL_HURT": 7.77,
    "FIGHT_PROP_CHARGE_EFFICIENCY": 6.48,
    "FIGHT_PROP_ELEMENT_MASTERY": 23.31,
}
_STAT_NAME_TO_PROP: dict[str, str] = {
    "血量": "FIGHT_PROP_HP",
    "百分比血量": "FIGHT_PROP_HP_PERCENT",
    "攻击力": "FIGHT_PROP_ATTACK",
    "百分比攻击力": "FIGHT_PROP_ATTACK_PERCENT",
    "防御力": "FIGHT_PROP_DEFENSE",
    "百分比防御力": "FIGHT_PROP_DEFENSE_PERCENT",
    "暴击率": "FIGHT_PROP_CRITICAL",
    "暴击伤害": "FIGHT_PROP_CRITICAL_HURT",
    "元素充能效率": "FIGHT_PROP_CHARGE_EFFICIENCY",
    "元素精通": "FIGHT_PROP_ELEMENT_MASTERY",
}

_MAX_ROLL_4: dict[str, float] = {
    "FIGHT_PROP_HP": 239.0,
    "FIGHT_PROP_HP_PERCENT": 4.66,
    "FIGHT_PROP_ATTACK": 15.56,
    "FIGHT_PROP_ATTACK_PERCENT": 4.66,
    "FIGHT_PROP_DEFENSE": 18.52,
    "FIGHT_PROP_DEFENSE_PERCENT": 5.83,
    "FIGHT_PROP_CRITICAL": 3.11,
    "FIGHT_PROP_CRITICAL_HURT": 6.22,
    "FIGHT_PROP_CHARGE_EFFICIENCY": 5.18,
    "FIGHT_PROP_ELEMENT_MASTERY": 18.65,
}


def count_affix_times(append_prop_id_list: Sequence[int]) -> dict[str, int]:
    """`appendPropIdList` → `{FIGHT_PROP_*: 强化次数}`，不含初次出现。"""
    rolls = collect_affix_rolls(append_prop_id_list)
    return {prop: len(ranks) - 1 for prop, ranks in rolls.items()}


def collect_affix_rolls(append_prop_id_list: Sequence[int]) -> dict[str, list[int]]:
    """`appendPropIdList` → `{FIGHT_PROP_*: [档位1-4, ...]}`，含初次。"""
    rolls: dict[str, list[int]] = {}
    for affix_id in append_prop_id_list:
        family = affix_id // 10
        if family not in AFFIX_FAMILY_TO_PROP:
            continue
        rank = affix_id % 10
        if rank < 1 or rank > 4:
            continue
        prop = AFFIX_FAMILY_TO_PROP[family]
        if prop in rolls:
            rolls[prop].append(rank)
        else:
            rolls[prop] = [rank]
    return rolls


def max_sub_roll(name: str, star: int = 5) -> float:
    """中文副词条名 → 单次掷骰上限；未知词条为 0。"""
    if name not in _STAT_NAME_TO_PROP:
        return 0.0
    table = _MAX_ROLL_5 if star >= 5 else _MAX_ROLL_4
    prop = _STAT_NAME_TO_PROP[name]
    if prop not in table:
        return 0.0
    return table[prop]


def infer_is_max(prop: str, value: float, times: int, star: int) -> bool:
    table = _MAX_ROLL_5 if star >= 5 else _MAX_ROLL_4
    if prop not in table:
        return False
    rolls = times + 1
    if rolls <= 0:
        return False
    ceiling = table[prop] * rolls
    slack = 1.2 if table[prop] >= 20 else 0.16
    return value + slack >= ceiling


def apply_substat_times(
    substats: Sequence[MutableMapping[str, object]],
    times_by_prop: Mapping[str, int],
) -> None:
    """按 `appendPropId` 写入 `times`。对不上的词条不写，渲染侧按缺省处理。"""
    for sub in substats:
        if "appendPropId" not in sub:
            continue
        prop = sub["appendPropId"]
        if not isinstance(prop, str):
            continue
        if prop in times_by_prop:
            sub["times"] = times_by_prop[prop]


def apply_substat_affix(
    substats: Sequence[MutableMapping[str, object]],
    rolls_by_prop: Mapping[str, Sequence[int]],
) -> None:
    """写入 `times` / `rolls` / `isMax`。旧缓存没有这些键时渲染侧跳过。"""
    for sub in substats:
        if "appendPropId" not in sub:
            continue
        prop = sub["appendPropId"]
        if not isinstance(prop, str) or prop not in rolls_by_prop:
            continue
        ranks = [r for r in rolls_by_prop[prop] if isinstance(r, int) and 1 <= r <= 4]
        if not ranks:
            continue
        sub["times"] = len(ranks) - 1
        sub["rolls"] = ranks
        sub["isMax"] = all(r == 4 for r in ranks)


def apply_substat_max_from_value(
    substats: Sequence[MutableMapping[str, object]],
    star: int,
) -> None:
    """米游社只有 times+值：用单次上限推断 `isMax`。"""
    for sub in substats:
        if "appendPropId" not in sub or "times" not in sub or "statValue" not in sub:
            continue
        prop = sub["appendPropId"]
        times = sub["times"]
        value = sub["statValue"]
        if not isinstance(prop, str):
            continue
        if isinstance(times, bool) or not isinstance(times, int) or times < 0:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        sub["isMax"] = infer_is_max(prop, float(value), times, star)


def substat_times(sub: Mapping[str, object]) -> int | None:
    """有 `times` 则返回 int；旧缓存或缺字段返回 None。"""
    if "times" not in sub:
        return None
    value = sub["times"]
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if value < 0:
        return None
    return value


def substat_rolls(sub: Mapping[str, object]) -> list[int] | None:
    if "rolls" not in sub:
        return None
    raw = sub["rolls"]
    if not isinstance(raw, list):
        return None
    ranks: list[int] = []
    for item in raw:
        if isinstance(item, bool) or not isinstance(item, int):
            return None
        if item < 1 or item > 4:
            return None
        ranks.append(item)
    if not ranks:
        return None
    return ranks


def substat_is_max(sub: Mapping[str, object]) -> bool | None:
    if "isMax" not in sub:
        return None
    raw = sub["isMax"]
    if isinstance(raw, bool):
        return raw
    return None
