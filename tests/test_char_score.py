from __future__ import annotations

from char_score import CHAR_SCORE_FLOOR, pool_factor, char_build_score, char_total_score

from gsuid_core.utils.api.mys.models import MihoyoAvatar, MihoyoWeapon, ReliquarySet, MihoyoReliquary


def _weapon(*, rarity: int, level: int, affix: int) -> MihoyoWeapon:
    return {
        "id": 0,
        "name": "测",
        "icon": "",
        "type": 1,
        "rarity": rarity,
        "level": level,
        "promote_level": 0,
        "type_name": "单手剑",
        "desc": "",
        "affix_level": affix,
    }


def _relic(*, rarity: int, level: int, set_name: str) -> MihoyoReliquary:
    s: ReliquarySet = {"id": 1, "name": set_name, "affixes": []}
    return {
        "id": 1,
        "name": "r",
        "icon": "",
        "pos": 1,
        "rarity": rarity,
        "level": level,
        "set": s,
        "pos_name": "",
    }


def _char(
    *,
    name: str = "胡桃",
    char_id: int = 10000046,
    rarity: int = 5,
    level: int = 90,
    const: int = 0,
    fetter: int = 10,
    weapon: MihoyoWeapon | None = None,
    relics: list[MihoyoReliquary] | None = None,
) -> MihoyoAvatar:
    if weapon is None:
        weapon = _weapon(rarity=5, level=90, affix=1)
    if relics is None:
        relics = []
    return {
        "id": char_id,
        "image": "",
        "icon": "",
        "name": name,
        "element": "Pyro",
        "fetter": fetter,
        "level": level,
        "rarity": rarity,
        "weapon": weapon,
        "reliquaries": relics,
        "constellations": [],
        "actived_constellation_num": const,
        "costumes": [],
        "card_image": "",
        "is_chosen": False,
    }


def test_pool_standard_seven_by_name() -> None:
    for name in ("琴", "迪卢克", "莫娜", "七七", "提纳里", "刻晴", "迪西娅"):
        assert pool_factor(_char(name=name, rarity=5)) == 0.86


def test_pool_traveler_not_standard() -> None:
    assert pool_factor(_char(name="旅行者", char_id=10000007, rarity=5)) == 0.72
    assert pool_factor(_char(name="荧", char_id=10000007, rarity=5)) == 0.72


def test_pool_limited_and_four() -> None:
    assert pool_factor(_char(name="胡桃", rarity=5)) == 1.00
    assert pool_factor(_char(name="香菱", rarity=4)) == 0.72


def _weapon_only(rarity: int, affix: int) -> float:
    char = _char(
        level=90,
        const=0,
        fetter=0,
        weapon=_weapon(rarity=rarity, level=90, affix=affix),
        relics=[],
    )
    return char_build_score(char) - 22.0


def test_weapon_anchors() -> None:
    assert round(_weapon_only(5, 1), 1) == 22.4
    assert round(_weapon_only(5, 5), 1) == 26.0
    assert round(_weapon_only(4, 1), 1) == 17.4
    assert round(_weapon_only(4, 5), 0) == 23.0
    assert round(_weapon_only(3, 5), 0) == 16.0


def test_usable_build_around_sixty() -> None:
    relics = [_relic(rarity=5, level=16, set_name="绝缘") for _ in range(4)]
    relics.append(_relic(rarity=5, level=16, set_name="绝缘"))
    limited = _char(
        name="胡桃",
        rarity=5,
        level=80,
        const=0,
        fetter=10,
        weapon=_weapon(rarity=4, level=90, affix=1),
        relics=relics,
    )
    standard = _char(
        name="琴",
        rarity=5,
        level=80,
        const=0,
        fetter=10,
        weapon=_weapon(rarity=4, level=90, affix=1),
        relics=relics,
    )
    four = _char(
        name="香菱",
        rarity=4,
        level=80,
        const=6,
        fetter=10,
        weapon=_weapon(rarity=4, level=90, affix=5),
        relics=relics,
    )
    b_lim = char_build_score(limited)
    assert 58.0 <= b_lim <= 66.0
    assert char_total_score(limited) > char_total_score(standard)
    assert char_total_score(limited) >= CHAR_SCORE_FLOOR
    assert char_total_score(four) >= CHAR_SCORE_FLOOR


def test_sort_uses_total_not_build() -> None:
    relics = [_relic(rarity=5, level=20, set_name="绝缘") for _ in range(5)]
    weak_limited = _char(
        name="胡桃",
        rarity=5,
        level=20,
        const=0,
        fetter=0,
        weapon=_weapon(rarity=3, level=20, affix=1),
        relics=[],
    )
    strong_four = _char(
        name="香菱",
        rarity=4,
        level=90,
        const=6,
        fetter=10,
        weapon=_weapon(rarity=4, level=90, affix=5),
        relics=relics,
    )
    assert char_build_score(strong_four) > char_build_score(weak_limited)
    assert char_total_score(strong_four) > char_total_score(weak_limited)


def test_bright_follows_total_score() -> None:
    assert CHAR_SCORE_FLOOR == 40.0
    relics = [_relic(rarity=5, level=20, set_name="绝缘") for _ in range(5)]
    high = _char(name="胡桃", rarity=5, level=90, const=6, weapon=_weapon(rarity=5, level=90, affix=5), relics=relics)
    low = _char(
        name="香菱",
        rarity=4,
        level=20,
        const=0,
        fetter=0,
        weapon=_weapon(rarity=3, level=1, affix=1),
        relics=[],
    )
    assert char_total_score(high) >= CHAR_SCORE_FLOOR
    assert char_total_score(low) < CHAR_SCORE_FLOOR
    assert char_total_score(high) > char_total_score(low)
