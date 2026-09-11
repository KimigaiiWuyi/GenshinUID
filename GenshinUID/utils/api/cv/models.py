from __future__ import annotations

from typing import TypedDict


class SubstatWeapon(TypedDict):
    name: str
    icon: str
    substat: str
    type: str
    rarity: int
    weaponId: str
    refinement: int


class SubstatCalculation(TypedDict):
    calculationId: str
    name: str
    short: str
    weapon: SubstatWeapon
    variant: str | None
    hidden: bool


class SubstatRoll(TypedDict):
    result: float
    substatValue: float
    newRank: int
    oldRank: int
    outOf: int


class SubstatPriorityItem(TypedDict):
    calculation: SubstatCalculation
    substats: dict[str, SubstatRoll]


class SubstatGain(TypedDict):
    name: str
    roll: float
    result: float
    dmg_gain: float
    pct_gain: float
    old_rank: int
    new_rank: int
    out_of: int
    rank_delta: int


class SubstatPriorityBoard(TypedDict):
    calculation_id: str
    name: str
    short: str
    weapon_name: str
    variant: str | None
    hidden: bool
    base_result: float
    base_rank: int
    out_of: int
    gains: list[SubstatGain]


class TeammateCharacter(TypedDict):
    name: str
    element: str
    rarity: int
    icon: str
    constellation: int | None
    artifact_set: str | None
    artifact_set_icon: str | None


class TeammateWeapon(TypedDict):
    name: str
    icon: str
    rarity: int
    refinement: int
    weapon_id: str


class Teammate(TypedDict):
    character: TeammateCharacter
    weapon: TeammateWeapon | None


class BuildLeaderboardRow(TypedDict):
    calculation_id: str
    short: str
    name: str
    ranking: int
    out_of: int
    result: float
    top_pct: float
    hidden: bool
    priority: int
    label: str | None
    variant_name: str | None
    variant_display: str | None
    weapon: SubstatWeapon
    teammates: list[Teammate]


class DamagePart(TypedDict):
    name: str
    value: float
    quantity: float
    type: str
    total: float
    pct: float


class GlobalRankRow(TypedDict):
    rank: int
    out_of: int
    top_pct: float
    uid: str
    nickname: str
    region: str
    constellation: int
    weapon_name: str
    weapon_id: str
    refinement: int
    result: float
    crit_rate: float
    crit_dmg: float
    cv: float
    hp: float
    atk: float
    character_id: str


class DamageDistributionBoard(TypedDict):
    calculation_id: str
    name: str
    short: str
    weapon_name: str
    weapon_id: str
    hidden: bool
    result: float
    formula_sum: float
    time_sec: float | None
    dps: float | None
    parts: list[DamagePart]
