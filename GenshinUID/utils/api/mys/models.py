from typing import List, Literal, TypedDict


class Expedition(TypedDict):
    avatar_side_icon: str
    status: Literal['Ongoing', 'Finished']


class RecoveryTime(TypedDict):
    Day: int
    Hour: int
    Minute: int
    Second: int
    reached: bool


class Transformer(TypedDict):
    obtained: bool
    recovery_time: RecoveryTime
    wiki: str
    noticed: bool
    latest_job_id: str


class TaskStatus(TypedDict):
    status: str


class DayilyTask(TypedDict):
    total_num: int
    finished_num: int
    is_extra_task_reward_received: bool
    task_rewards: List[TaskStatus]
    attendance_rewards: List[TaskStatus]


class ArchonStatus(TypedDict):
    status: str
    chapter_num: str
    chapter_title: str
    id: int


class ArchonProgress(TypedDict):
    list: List[ArchonStatus]
    is_open_archon_quest: bool
    is_finish_all_mainline: bool
    is_finish_all_interchapter: bool
    wiki_url: str


class WidgetResin(TypedDict):
    current_resin: int
    max_resin: int
    resin_recovery_time: str
    finished_task_num: int
    total_task_num: int
    is_extra_task_reward_received: bool
    current_expedition_num: int
    max_expedition_num: int
    expeditions: List[Expedition]
    current_home_coin: int
    max_home_coin: int
    has_signed: bool
    sign_url: str
    home_url: str
    note_url: str


class FakeResin(WidgetResin):
    remain_resin_discount_num: int
    resin_discount_num_limit: int
    transformer: Transformer
    daily_task: DayilyTask
    archon_quest_progress: ArchonProgress


class PoetryAbyssLinks(TypedDict):
    lineup_link: str
    lineup_link_pc: str
    strategy_link: str
    lineup_publish_link: str
    lineup_publish_link_pc: str


class PoetryAbyssAvatar(TypedDict):
    avatar_id: int
    avatar_type: int
    name: str
    element: str
    image: str
    level: int
    rarity: int


class PoetryAbyssChoiceCard(TypedDict):
    icon: str
    name: str
    desc: str
    is_enhanced: bool
    id: int


class PoetryAbyssBuff(TypedDict):
    icon: str
    name: str
    desc: str
    is_enhanced: bool
    id: int


class PoetryAbyssDateTime(TypedDict):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int


class PoetryAbyssSchedule(TypedDict):
    start_time: int
    end_time: int
    schedule_type: int
    schedule_id: int
    start_date_time: PoetryAbyssDateTime
    end_date_time: PoetryAbyssDateTime


class PoetryAbyssDetailStat(TypedDict):
    difficulty_id: int
    max_round_id: int
    heraldry: int
    get_medal_round_list: List[int]
    medal_num: int
    coin_num: int
    avatar_bonus_num: int
    rent_cnt: int


class RoundData(TypedDict):
    avatars: List[PoetryAbyssAvatar]
    choice_cards: List[PoetryAbyssChoiceCard]
    buffs: List[PoetryAbyssBuff]
    is_get_medal: bool
    round_id: int
    finish_time: int
    finish_date_time: PoetryAbyssDateTime
    detail_stat: PoetryAbyssDetailStat


class PoetryAbyssDetail(TypedDict):
    rounds_data: List[RoundData]
    detail_stat: PoetryAbyssDetailStat
    backup_avatars: List[PoetryAbyssAvatar]


class PoetryAbyssData(TypedDict):
    detail: PoetryAbyssDetail
    stat: PoetryAbyssDetailStat
    schedule: PoetryAbyssSchedule
    has_data: bool
    has_detail_data: bool


class PoetryAbyssDatas(TypedDict):
    data: List[PoetryAbyssData]
    is_unlock: bool
    links: PoetryAbyssLinks


class MainProperty(TypedDict):
    property_type: int
    base: str
    add: str
    final: str


class SubProperty(TypedDict):
    property_type: int
    base: str
    add: str
    final: str


class RelicMainProperty(TypedDict):
    property_type: int
    value: str
    times: int


class RelicSubProperty(TypedDict):
    property_type: int
    value: str
    times: int


class RelicSet(TypedDict):
    id: int
    name: str
    affixes: List[dict]


class Relic(TypedDict):
    id: int
    name: str
    icon: str
    pos: int
    rarity: int
    level: int
    set: RelicSet
    pos_name: str
    main_property: RelicMainProperty
    sub_property_list: List[RelicSubProperty]


class Constellation(TypedDict):
    id: int
    name: str
    icon: str
    effect: str
    is_actived: bool
    pos: int


class Property(TypedDict):
    property_type: int
    base: str
    add: str
    final: str


class Weapon(TypedDict):
    id: int
    name: str
    icon: str
    type: int
    rarity: int
    level: int
    promote_level: int
    type_name: str
    desc: str
    affix_level: int
    main_property: MainProperty
    sub_property: SubProperty


class CharacterBase(TypedDict):
    id: int
    icon: str
    name: str
    element: str
    fetter: int
    level: int
    rarity: int
    actived_constellation_num: int
    image: str
    is_chosen: bool
    side_icon: str
    weapon_type: int
    weapon: Weapon


class SkillAffix(TypedDict):
    name: str
    value: str


class Skill(TypedDict):
    skill_id: int
    skill_type: int
    level: int
    desc: str
    skill_affix_list: List[SkillAffix]
    icon: str
    is_unlock: bool
    name: str


class Character(TypedDict):
    base: CharacterBase
    weapon: Weapon
    relics: List[Relic]
    constellations: List[Constellation]
    costumes: List[dict]
    selected_properties: List[Property]
    base_properties: List[Property]
    extra_properties: List[Property]
    element_properties: List[Property]
    skills: List[Skill]
