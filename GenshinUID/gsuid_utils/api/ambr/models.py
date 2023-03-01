from __future__ import annotations

from typing import Dict, List, Literal, Optional, TypedDict


class AmbrLanguageData(TypedDict):
    EN: str
    RU: str
    CHS: str
    KR: str
    JP: str


class AmbrEvent(TypedDict):
    id: int
    name: AmbrLanguageData
    nameFull: AmbrLanguageData
    description: AmbrLanguageData
    banner: AmbrLanguageData
    endAt: str


class AmbrFetter(TypedDict):
    title: str
    detail: str
    constellation: str
    native: str
    cv: AmbrLanguageData


class AmbrProp(TypedDict):
    propType: str
    initValue: float
    type: str


class AmbrPromote(TypedDict):
    promoteLevel: int
    costItems: Dict[str, int]
    unlockMaxLevel: int
    addProps: Dict[str, float]
    requiredPlayerLevel: int
    coinCost: int


class AmbrUpgrade(TypedDict):
    prop: List[AmbrProp]
    promote: List[AmbrPromote]


class AmbrWeaponUpgrade(AmbrUpgrade):
    awakenCost: List[int]


class AmbrNameCard(TypedDict):
    id: int
    name: str
    description: str
    icon: str


class AmbrFood(TypedDict):
    id: int
    name: str
    rank: int
    effectIcon: str
    icon: str


class AmbrCharOther(TypedDict):
    nameCard: AmbrNameCard
    specialFood: AmbrFood


class AmbrTalentPromote(TypedDict):
    level: int
    costItems: Optional[Dict[str, int]]
    coinCost: Optional[int]
    description: List[str]
    params: List[int]


class AmbrTalent(TypedDict):
    type: int
    name: str
    description: str
    icon: str
    promote: Dict[str, AmbrTalentPromote]
    cooldown: int
    cost: int


class AmbrConstellation(TypedDict):
    name: str
    description: str
    icon: str


class AmbrCharacter(TypedDict):
    id: int
    rank: int
    name: str
    element: Literal[
        'Electric', 'Ice', 'Wind', 'Grass', 'Water', 'Rock', 'Fire'
    ]
    weaponType: Literal[
        'WEAPON_SWORD_ONE_HAND',
        'WEAPON_CATALYST',
        'WEAPON_CLAYMORE',
        'WEAPON_BOW',
        'WEAPON_POLE',
    ]
    icon: str
    birthday: List[int]
    release: int
    route: str
    fetter: AmbrFetter
    upgrade: AmbrUpgrade
    other: AmbrCharOther
    ascension: Dict[str, int]
    talent: Dict[str, AmbrTalent]
    constellation: Dict[str, AmbrConstellation]


class AmbrAffix(TypedDict):
    name: str
    upgrade: Dict[str, str]


class AmbrWeapon(TypedDict):
    id: int
    rank: int
    type: str
    name: str
    description: str
    icon: str
    storyId: int
    affix: Dict[str, AmbrAffix]
    route: str
    upgrade: AmbrWeaponUpgrade
    ascension: Dict[str, int]


class AmbrBook(TypedDict):
    id: int
    name: str
    rank: int
    icon: str
    route: str


class AmbrVolume(TypedDict):
    id: int
    name: str
    description: str
    storyId: str


class AmbrBookDetail(TypedDict):
    id: int
    name: str
    rank: int
    icon: str
    volume: List[AmbrVolume]
    route: str
