from __future__ import annotations

from typing import Dict, List, Union, Literal, Optional, TypedDict


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


class AmbrMonsterAffix(TypedDict):
    name: str
    description: str
    abilityName: List[str]
    isCommon: bool


class AmbrHpDrop(TypedDict):
    id: int
    hpPercent: int


class AmbrReward(TypedDict):
    rank: int
    icon: str
    count: str


class AmbrEntry(TypedDict):
    id: str
    type: str
    affix: List[AmbrMonsterAffix]
    hpDrops: List[AmbrHpDrop]
    prop: List[AmbrProp]
    resistance: Dict[str, float]
    reward: Dict[str, AmbrReward]


class AmbrMonster(TypedDict):
    id: int
    name: str
    icon: str
    route: str
    title: str
    specialName: str
    description: str
    entries: Dict[str, AmbrEntry]
    tips: Optional[str]


class AmbrMonsterSimple(TypedDict):
    id: int
    name: str
    icon: str
    route: str
    type: str


class AmbrGCGList(TypedDict):
    types: Dict[str, Literal['characterCard', 'actionCard']]
    items: Dict[str, AmbrGCGCard]


class AmbrGCGCard(TypedDict):
    id: int
    name: str
    type: Literal['characterCard', 'actionCard']
    tags: Dict[str, str]
    props: Dict[str, int]
    icon: str
    route: str
    sortOrder: int


class AmbrGCGDict(TypedDict):
    name: str
    description: str


class AmbrGCGTalent(TypedDict):
    name: str
    description: str
    cost: Dict[str, int]
    params: Dict[str, Union[int, str]]
    tags: Dict[str, str]
    icon: str
    subSkills: Optional[str]
    keywords: Dict[str, str]


class AmbrGCGEntry(TypedDict):
    id: int
    name: str
    type: Literal['gcg']
    icon: str


class AmbrGCGDetail(AmbrGCGCard):
    storyTitle: str
    storyDetail: str
    source: str
    dictionary: Dict[str, AmbrGCGDict]
    talent: Dict[str, AmbrGCGTalent]
    relatedEntries: List[AmbrGCGCard]


class AmbrMonsterList(TypedDict):
    types: Dict[str, str]
    items: Dict[str, AmbrMonsterSimple]
