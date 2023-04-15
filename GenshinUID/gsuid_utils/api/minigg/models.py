"""
MiniGG API 响应模型。
"""
# TODO: - @KimigaiiWuyi 补文档
from __future__ import annotations

import sys
from typing import Dict, List, Literal, TypedDict

# https://peps.python.org/pep-0655/#usage-in-python-3-11
if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

# https://peps.python.org/pep-0613
if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

R: TypeAlias = List[str]


class FandomUrl(TypedDict):
    fandom: str


class WeaponImage(TypedDict):
    image: str
    nameicon: str
    namegacha: str
    icon: str
    nameawakenicon: str
    awakenicon: str


class AscendItem(TypedDict):
    name: str
    count: int


class Costs(TypedDict):
    ascend1: List[AscendItem]
    ascend2: List[AscendItem]
    ascend3: List[AscendItem]
    ascend4: List[AscendItem]
    ascend5: List[AscendItem]
    ascend6: List[AscendItem]


class Weapon(TypedDict):
    name: str
    description: str
    weapontype: str
    rarity: str
    baseatk: int
    substat: str
    subvalue: str
    effectname: str
    effect: str
    r1: R
    r2: R
    r3: R
    r4: R
    r5: R
    weaponmaterialtype: str
    images: WeaponImage
    url: NotRequired[FandomUrl]
    version: str
    costs: Costs


class WeaponStats(TypedDict):
    level: int
    ascension: int
    attack: float
    specialized: float


class Character(TypedDict):
    name: str
    fullname: str
    title: str
    description: str
    rarity: str
    element: str
    weapontype: str
    substat: str
    gender: Literal['男', '女']
    body: str
    association: str
    region: Literal['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '穆纳塔']
    affiliation: str
    birthdaymmdd: str
    birthday: str
    constellation: str
    cv: CharacterCv
    costs: Costs
    image: CharacterImage
    url: FandomUrl
    version: str


class CharacterCv(TypedDict):
    english: str
    chinese: str
    japanese: str
    korean: str


class CharacterImage(TypedDict):
    card: str
    portrait: str
    icon: str
    sideicon: str
    cover1: str
    cover2: str
    hoyolab_avatar: str
    nameicon: str
    nameiconcard: str
    namegachasplash: str
    namegachaslice: str
    namesideicon: str


class CharacterStats(TypedDict):
    level: int
    ascension: int
    hp: float
    attack: float
    defense: float
    specialized: float


class CharacterConstellations(TypedDict):
    name: str
    c1: CharacterConstellation
    c2: CharacterConstellation
    c3: CharacterConstellation
    c4: CharacterConstellation
    c5: CharacterConstellation
    c6: CharacterConstellation
    images: ConstellationsImage
    version: str


class CharacterConstellation(TypedDict):
    name: str
    effect: str


class ConstellationsImage(TypedDict):
    c1: str
    c2: str
    c3: str
    c4: str
    c5: str
    c6: str


class MiniGGError(TypedDict):
    retcode: int
    error: str


class CharacterTalents(TypedDict):
    name: str
    combat1: TalentCombat
    combat2: TalentCombat
    combat3: TalentCombat
    passive1: TalentPassive
    passive2: TalentPassive
    passive3: TalentPassive
    passive4: NotRequired[TalentPassive]
    costs: TalentsCosts
    images: TalentsImages


class TalentsCosts(TypedDict):
    lvl2: List[AscendItem]
    lvl3: List[AscendItem]
    lvl4: List[AscendItem]
    lvl5: List[AscendItem]
    lvl6: List[AscendItem]
    lvl7: List[AscendItem]
    lvl8: List[AscendItem]
    lvl9: List[AscendItem]
    lvl10: List[AscendItem]


class TalentsImages(TypedDict):
    combat1: str
    combat2: str
    combat3: str
    passive1: str
    passive2: str
    passive3: str
    passive4: NotRequired[str]


class TalentCombat(TypedDict):
    name: str
    info: str
    description: NotRequired[str]
    attributes: TalentAttr


class TalentPassive(TypedDict):
    name: str
    info: str


class TalentAttr(TypedDict):
    labels: List[str]
    parameters: Dict[str, List[float]]


class Food(TypedDict):
    name: str
    rarity: str
    foodtype: str
    foodfilter: str
    foodcategory: str
    effect: str
    description: str
    suspicious: FoodEffect
    normal: FoodEffect
    delicious: FoodEffect
    ingredients: List[AscendItem]
    images: Image
    url: FandomUrl
    version: str


class FoodEffect(TypedDict):
    effect: str
    description: str


class Image(TypedDict):
    nameicon: str


class Enemy(TypedDict):
    name: str
    specialname: str
    enemytype: str
    category: str
    description: str
    investigation: EnemyInvest
    rewardpreview: List[EnemyReward]
    images: Image
    version: str


class EnemyReward(TypedDict):
    name: str
    count: NotRequired[float]


class EnemyInvest(TypedDict):
    name: str
    category: str
    description: str


class Domain(TypedDict):
    name: str
    region: Literal['蒙德', '璃月', '稻妻', '须弥', '枫丹', '纳塔', '至冬', '穆纳塔']
    domainentrance: str
    domaintype: str
    description: str
    recommendedlevel: int
    recommendedelements: List[
        Literal['冰元素', '火元素', '雷元素', '水元素', '草元素', '岩元素', '风元素']
    ]
    daysofweek: List[Literal['周日', '周一', '周二', '周三', '周四', '周五', '周六']]
    unlockrank: int
    rewardpreview: List[EnemyReward]
    disorder: List[str]
    monsterlist: List[str]
    images: Image
    version: str


class Piece(TypedDict):
    name: str
    description: str
    story: str


class PieceFlower(Piece):
    relictype: Literal['生之花']


class PiecePlume(Piece):
    relictype: Literal['死之羽']


class PieceSands(Piece):
    relictype: Literal['时之沙']


class PieceGoblet(Piece):
    relictype: Literal['空之杯']


class PieceCirclet(Piece):
    relictype: Literal['理之冠']


class PieceImages(TypedDict):
    flower: str
    plume: str
    sands: str
    goblet: str
    circlet: str
    nameflower: str
    nameplume: str
    namesands: str
    namegoblet: str
    namecirclet: str


Artifact = TypedDict(
    'Artifact',
    {
        'name': str,
        'rarity': List[str],
        '1pc': str,
        '2pc': str,
        '4pc': str,
        'flower': PieceFlower,
        'plume': PiecePlume,
        'sands': PieceSands,
        'goblet': PieceGoblet,
        'circlet': PieceCirclet,
        'images': PieceImages,
        'url': FandomUrl,
        'version': str,
    },
)


class MaterialImage(TypedDict):
    nameicon: str
    redirect: str


class Material(TypedDict):
    name: str
    description: str
    sortorder: int
    rarity: str
    category: str
    materialtype: str
    source: List[str]
    images: MaterialImage
    version: str
    # 下面两个当且仅当materialtype是xx突破素材的情况才有
    dropdomain: str
    daysofweek: List[str]
