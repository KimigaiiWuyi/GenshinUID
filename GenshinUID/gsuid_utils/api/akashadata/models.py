from __future__ import annotations

from typing import TypedDict


class TeamListItem(TypedDict):
    ac: int
    mr: str
    uc: str
    dc: str
    ud: str
    umr: str
    dmr: str
    tl: list[int]


class AbyssTotalView(TypedDict):
    avg_star: str
    avg_battle_count: str
    avg_maxstar_battle_count: str
    pass_rate: str
    maxstar_rate: str
    maxstar_12_rate: str
    person_war: str
    person_pass: int
    maxstar_person: int


class LastRate(TypedDict):
    avg_star: str
    pass_rate: str
    maxstar_rate: str
    avg_battle_count: str
    avg_maxstar_battle_count: str
    maxstar_12_rate: str


class MaxstarPlayerData(TypedDict):
    title: str
    y_list: list[str]
    x_list: list[str]


class PassPlayerData(TypedDict):
    title: str
    y_list: list[str]
    x_list: list[str]


class PlayerLevelData(TypedDict):
    maxstar_player_data: MaxstarPlayerData
    pass_player_data: PassPlayerData


class PalyerCountLevelData(TypedDict):
    player_count_data: list[int]
    level_data: list[str]


class LevelData(TypedDict):
    player_level_data: PlayerLevelData
    palyer_count_level_data: PalyerCountLevelData


class CharacterUsedListItem(TypedDict):
    avatar_id: int
    maxstar_person_had_count: int
    maxstar_person_use_count: int
    value: float
    used_index: int
    name: str
    en_name: str
    icon: str
    element: str
    rarity: int


class AkashaAbyssData(TypedDict):
    schedule_id: int
    modify_time: str
    schedule_version_desc: str
    team_list: list[TeamListItem]
    team_up_list: list[TeamListItem]
    team_down_list: list[TeamListItem]
    abyss_total_view: AbyssTotalView
    last_rate: LastRate
    level_data: LevelData
    character_used_list: list[CharacterUsedListItem]
