from __future__ import annotations

import sys
from typing import List, Literal, TypedDict

# https://peps.python.org/pep-0655/#usage-in-python-3-11
if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


class EnkaData(TypedDict):
    playerInfo: PlayerInfo
    avatarInfoList: List[AvatarInfoListItem]
    ttl: int
    uid: str


class PlayerInfo(TypedDict):
    nickname: str
    level: int
    signature: str
    worldLevel: int
    nameCardId: int
    finishAchievementNum: int
    towerFloorIndex: int
    towerLevelIndex: int
    showAvatarInfoList: List[ShowAvatarInfoListItem]
    showNameCardIdList: List[int]
    profilePicture: ProfilePicture


class ShowAvatarInfoListItem(TypedDict):
    avatarId: int
    level: int
    costumeId: NotRequired[int]


class ProfilePicture(TypedDict):
    avatarId: int


class AvatarInfoListItem(TypedDict):
    avatarId: int
    propMap: dict[str, PropMap]
    talentIdList: List[int]
    fightPropMap: dict[str, float]
    skillDepotId: int
    inherentProudSkillList: List[int]
    skillLevelMap: dict[str, int]
    equipList: List[Equip]
    fetterInfo: FetterInfo


class Equip(TypedDict):
    itemId: int
    reliquary: Reliquary
    weapon: Weapon
    flat: Flat


class Flat(TypedDict):
    # l10n
    nameTextMapHash: str
    setNameTextMapHash: str

    # artifact
    reliquaryMainstat: Stat
    reliquarySubstats: List[Stat]
    equipType: Literal[
        "EQUIP_BRACER",
        "EQUIP_NECKLACE",
        "EQUIP_SHOES",
        "EQUIP_RING",
        "EQUIP_DRESS",
    ]

    # weapon
    weaponStats: List[Stat]

    rankLevel: Literal[3, 4, 5]
    itemType: Literal["ITEM_WEAPON", "ITEM_RELIQUARY"]
    icon: str  # https://enka.network/ui/{Icon}.png


class Stat(TypedDict):
    mainPropId: str
    appendPropId: str
    statName: str
    statValue: float | int


class Weapon(TypedDict):
    level: int
    promoteLevel: int
    affixMap: dict[str, int]


class Reliquary(TypedDict):
    level: int
    mainPropId: int
    appendPropIdList: List[int]


class PropMap(TypedDict):
    type: int
    ival: str  # Ignore It!
    val: str


class FetterInfo(TypedDict):
    expLevel: int
