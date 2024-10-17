from typing import List, Tuple, TypedDict


class TeyvatChar(TypedDict):
    name: str
    star: int
    avatar: str
    use: int
    own: int
    use_rate: float
    own_rate: float
    rank_class: str


class TeyvatSelect(TypedDict):
    title: str
    value: str


class TeyvatRestart(TypedDict):
    intro: str
    rate: float
    width: int


class CharacterUsage(TypedDict):
    name: str
    star: int
    avatar: str
    use: int
    own: int
    use_rate: float
    own_rate: float
    rank_class: str
    use_rate_old: float
    use_rate_change: float


class CharacterRank(TypedDict):
    name: str
    ename: str
    star: int
    avatar: str
    use: int
    own: int
    use_rate: float
    own_rate: float


class TeyvatRank(TypedDict):
    rank_name: str  # S/S+
    rank_class: str  # s1
    list: List[CharacterRank]


class FakeTeyvatRank(TypedDict):
    rank_name: str  # S/S+
    rank_class: str  # s1
    list: List[CharacterUsage]


class Role(TypedDict):
    avatar: str
    star: int


class TeyvatTeam(TypedDict):
    role: List[Role]
    use: int
    use_rate: float
    has: int
    has_rate: float
    attend_rate: float
    up_use: int
    down_use: int
    up_use_num: int
    down_use_num: int


class TeyvatAbyssRank(TypedDict):
    code: int
    title: str
    rank_btn: str
    version: str
    now_version: str
    old_version: str
    last_update: str
    update: str
    top_own: int
    tips: str
    tips2: str
    select_list: List[TeyvatSelect]
    has_list: List[TeyvatChar]
    star36_rate: str
    star36_once_rate: str
    restart_times_avg: float
    nandu: int
    restart_info: List[TeyvatRestart]
    result: Tuple[
        List[TeyvatRank],
        List[CharacterUsage],
        List[CharacterUsage],
        List[TeyvatTeam],
    ]
