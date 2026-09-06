from __future__ import annotations

from gsuid_core.utils.api.mys.models import MihoyoAvatar, MihoyoReliquary

# 综合分低于此值的卡片压暗；排序与亮暗都看综合分
CHAR_SCORE_FLOOR = 40.0

_STANDARD_FIVE: frozenset[str] = frozenset({"琴", "迪卢克", "莫娜", "七七", "提纳里", "刻晴", "迪西娅"})
_TRAVELER_NAMES: frozenset[str] = frozenset({"旅行者", "空", "荧"})
_TRAVELER_IDS: frozenset[int] = frozenset({10000005, 10000007})

_C5: tuple[int, ...] = (0, 6, 11, 14, 16, 17, 18)
_C4: tuple[int, ...] = (0, 2, 4, 7, 10, 13, 18)


def _is_traveler(char: MihoyoAvatar) -> bool:
    if char["id"] in _TRAVELER_IDS:
        return True
    return char["name"] in _TRAVELER_NAMES


def pool_factor(char: MihoyoAvatar) -> float:
    if _is_traveler(char):
        return 0.72
    if char["name"] in _STANDARD_FIVE:
        return 0.86
    if int(char["rarity"]) >= 5:
        return 1.00
    return 0.72


def _level_score(level: int) -> float:
    if level <= 0:
        return 0.0
    return 22.0 * (level / 90.0) ** 1.15


def _const_score(char: MihoyoAvatar) -> float:
    n = char["actived_constellation_num"]
    if n < 0:
        n = 0
    if n > 6:
        n = 6
    if int(char["rarity"]) >= 5 and not _is_traveler(char):
        return float(_C5[n])
    return float(_C4[n])


def _weapon_score(char: MihoyoAvatar) -> float:
    weapon = char["weapon"]
    star = int(weapon["rarity"])
    if star >= 5:
        base = 0.80
        step = 0.04
    elif star == 4:
        base = 0.62
        step = 0.08
    elif star == 3:
        base = 0.42
        step = 0.08
    elif star == 2:
        base = 0.24
        step = 0.08
    else:
        base = 0.16
        step = 0.08
    lv = weapon["level"]
    if lv <= 0:
        lv_f = 0.0
    else:
        lv_f = (lv / 90.0) ** 1.1
    affix = weapon["affix_level"]
    extra = 0 if affix <= 1 else affix - 1
    raw = 28.0 * base * lv_f * (1.0 + extra * step)
    if raw > 28.0:
        return 28.0
    return raw


def _has_four_set(relics: list[MihoyoReliquary]) -> bool:
    counts: dict[str, int] = {}
    for relic in relics:
        name = relic["set"]["name"]
        if name in counts:
            counts[name] += 1
        else:
            counts[name] = 1
    for n in counts.values():
        if n >= 4:
            return True
    return False


def _artifact_score(char: MihoyoAvatar) -> float:
    if "reliquaries" not in char:
        return 0.0
    relics = char["reliquaries"]
    if not relics:
        return 0.0
    levels: list[int] = []
    for relic in relics:
        if relic["rarity"] >= 5:
            levels.append(relic["level"])
    if not levels:
        return 0.0
    avg = sum(levels) / len(levels)
    score = 32.0 * (len(levels) / 5.0) * (avg / 20.0)
    if not _has_four_set(relics):
        score *= 0.85
    if score > 32.0:
        return 32.0
    return score


def _fetter_adj(char: MihoyoAvatar) -> float:
    v = char["fetter"] * 0.1
    if v > 1.0:
        return 1.0
    return v


def char_build_score(char: MihoyoAvatar) -> float:
    total = _level_score(char["level"]) + _const_score(char) + _weapon_score(char) + _artifact_score(char)
    if total > 100.0:
        return 100.0
    if total < 0.1:
        return 0.1
    return total


def char_total_score(char: MihoyoAvatar) -> float:
    return pool_factor(char) * char_build_score(char) + _fetter_adj(char)
