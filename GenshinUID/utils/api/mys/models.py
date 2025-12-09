from typing import Any, Dict, List, Union, Literal, Optional, TypedDict


class PoetryAbyssDateTime(TypedDict):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int


class AvatarPool(TypedDict):
    id: int
    icon: str
    name: str
    element: str
    rarity: int
    is_invisible: bool


class WeaponPool(TypedDict):
    id: int
    icon: str
    rarity: int
    name: str
    wiki_url: str


class RewardItem(TypedDict):
    item_id: int
    name: str
    icon: str
    wiki_url: str
    num: int
    rarity: str
    homepage_show: bool


class Act(TypedDict):
    id: int
    name: str
    type: str
    start_timestamp: int
    start_time: PoetryAbyssDateTime
    end_timestamp: int
    end_time: PoetryAbyssDateTime
    desc: str
    strategy: str
    countdown_seconds: int
    status: int
    reward_list: List[RewardItem]
    is_finished: bool
    x: int
    y: int


class RoleCombatDetail(TypedDict):
    is_unlock: bool
    max_round_id: int
    has_data: bool


class TowerDetail(TypedDict):
    is_unlock: bool
    max_star: int
    total_star: int
    has_data: bool


class SubHardDetail(TypedDict):
    seconds: int
    x: int
    y: int


class HardChallengeDetail(TypedDict):
    is_unlock: bool
    difficulty: int
    second: int
    icon: str
    sub: SubHardDetail


class ExploreDetail(TypedDict):
    explore_percent: int
    is_finished: bool


class FixedAct(TypedDict):
    id: int
    name: str
    type: str
    start_timestamp: int
    start_time: PoetryAbyssDateTime
    end_timestamp: int
    end_time: PoetryAbyssDateTime
    desc: str
    strategy: str
    countdown_seconds: int
    status: int
    reward_list: List[RewardItem]
    is_finished: bool
    role_combat_detail: Optional[RoleCombatDetail]
    tower_detail: Optional[TowerDetail]
    hard_challenge_detail: Optional[HardChallengeDetail]
    explore_detail: Optional[ExploreDetail]

    x: int
    y: int


class Pool(TypedDict):
    pool_id: int
    version_name: str
    pool_name: str
    pool_type: int
    avatars: List[AvatarPool]
    weapon: List[WeaponPool]
    start_timestamp: int
    start_time: PoetryAbyssDateTime
    end_timestamp: int
    end_time: PoetryAbyssDateTime
    jump_url: str
    pool_status: int
    countdown_seconds: int


class CalendarData(TypedDict):
    avatar_card_pool_list: List[Pool]
    weapon_card_pool_list: List[Pool]
    mixed_card_pool_list: List[Pool]
    selected_avatar_card_pool_list: List[Pool]
    selected_mixed_card_pool_list: List[Pool]
    act_list: List[Act]
    fixed_act_list: List[FixedAct]  # Updated to include FixedAct
    selected_act_list: List[Act]


class Expedition(TypedDict):
    avatar_side_icon: str
    status: Literal["Ongoing", "Finished"]


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
    tarot_finished_cnt: int


class PoetryEnemy(TypedDict):
    name: str
    icon: str
    level: int


class RoundAvatar(TypedDict):
    avatar_id: int
    avatar_type: int
    name: str
    element: str
    image: str
    level: int
    rarity: int


class DetailStat(TypedDict):
    difficulty_id: int
    max_round_id: int
    heraldry: int
    get_medal_round_list: List[int]
    medal_num: int
    coin_num: int
    avatar_bonus_num: int
    rent_cnt: int


class BackupAvatar(TypedDict):
    avatar_id: int
    avatar_type: int
    name: str
    element: str
    image: str
    level: int
    rarity: int


class StatisticAvatar(TypedDict):
    avatar_id: int
    avatar_icon: str
    value: Union[str, int]
    rarity: int


class FightStatistic(TypedDict):
    max_defeat_avatar: StatisticAvatar
    max_damage_avatar: StatisticAvatar
    max_take_damage_avatar: StatisticAvatar
    total_coin_consumed: StatisticAvatar
    shortest_avatar_list: List[StatisticAvatar]
    total_use_time: int
    is_show_battle_stats: bool


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


# 季报


# TypedDicts for nested objects
class DateTime(TypedDict):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int


class Link(TypedDict):
    id: int
    name: str
    desc: str


class LevelEffect(TypedDict):
    icon: str
    name: str
    desc: str
    links: Dict[str, Link]


class Buff(TypedDict):
    name: str
    icon: str
    level: int
    level_effect: List[LevelEffect]


class BuffSummary(TypedDict):
    total_level: int
    desc: str


class SplendourBuff(TypedDict):
    summary: BuffSummary
    buffs: List[Buff]


class Enemy(TypedDict):
    name: str
    icon: str
    level: int


class ChoiceCard(TypedDict):
    icon: str
    name: str
    desc: str
    is_enhanced: bool
    id: int


class CombatStat(TypedDict):
    difficulty_id: int
    max_round_id: int
    heraldry: int
    get_medal_round_list: List[int]
    medal_num: int
    coin_num: int
    avatar_bonus_num: int
    rent_cnt: int


class ScheduleInfo(TypedDict):
    start_time: str
    end_time: str
    schedule_type: int
    schedule_id: int
    start_date_time: DateTime
    end_date_time: DateTime


class GCGChallenge(TypedDict):
    honor_avatar_list: List[Any]
    max_win_games: int
    begin: DateTime
    end: DateTime
    name: str


class GCGInfo(TypedDict):
    avatar_card_list: List[Any]
    cur_avatar_card_num: int
    new_avatar_card_num: int
    action_card_list: List[Any]
    cur_action_card_num: int
    new_action_card_num: int
    challenge_list: List[GCGChallenge]
    has_data: bool


class AbyssRank(TypedDict):
    avatar_id: int
    avatar_icon: str
    value: int
    rarity: int


class SpiralAbyssInfo(TypedDict):
    schedule_id: int
    start_time: str
    end_time: str
    total_battle_times: int
    max_floor: str
    reveal_rank: List[AbyssRank]
    damage_rank: List[AbyssRank]
    defeat_rank: List[AbyssRank]
    take_damage_rank: List[AbyssRank]
    total_star: int
    name: str
    normal_skill_rank: List[AbyssRank]
    energy_skill_rank: List[AbyssRank]
    is_just_skipped_floor: bool


class Achievement(TypedDict):
    name: str


class HistoryStatInfo(TypedDict):
    login_days: int
    task_num: int
    cur_achievement_num: int
    new_achievement_num: int
    achievement_list: List[Achievement]
    mostly_visit_dungeon_name: str
    mostly_visit_dungeon_times: int
    mostly_visit_weekly_boss_name: str
    mostly_visit_weekly_boss_times: int
    has_data: bool


class HCoinSource(TypedDict):
    type: int
    percent: int


class ResinConsume(TypedDict):
    type: str
    percent: int


class ResourceInfo(TypedDict):
    gain_scoin: int
    gain_hcoin: int
    hcoin_source_list: List[HCoinSource]
    consume_resin: int
    resin_consume_list: List[ResinConsume]
    has_data: bool


class WorldExploration(TypedDict):
    cur_number: int
    new_number: int
    icon: str
    name: str


class Crystal(TypedDict):
    cur_number: int
    new_number: int
    icon: str
    name: str


class Chest(TypedDict):
    cur_number: int
    new_number: int
    icon: str
    name: str


class TransPoint(TypedDict):
    cur_number: int
    new_number: int
    has_data: bool


class DungeonPoint(TypedDict):
    cur_number: int
    new_number: int
    has_data: bool


class ExplorationInfo(TypedDict):
    world_exploration_list: List[WorldExploration]
    crystal_list: List[Crystal]
    chest_list: List[Chest]
    trans_point: TransPoint
    dungeon_point: DungeonPoint
    has_data: bool


class Costume(TypedDict):
    id: int
    name: str
    avatar_name: str
    image: str
    is_new_costume: bool
    wide_image: str


class CostumeInfo(TypedDict):
    cur_costume_count: int
    new_costume_count: int
    costume_list: List[Costume]
    has_data: bool


class ChangedWeapon(TypedDict):
    id: int
    name: str
    image: str
    is_new_weapon: bool
    rarity: int


class WeaponInfo(TypedDict):
    cur_weapon_count: int
    new_weapon_count: int
    changed_weapon_list: List[ChangedWeapon]
    has_data: bool


class ChangedAvatar(TypedDict):
    id: int
    image: str
    is_new_avatar: bool
    start_level: int
    end_level: int
    start_fetter: int
    end_fetter: int
    start_actived_constellation_num: int
    end_actived_constellation_num: int
    rarity: int
    element: str
    name: str
    icon: str


class AvatarInfo(TypedDict):
    cur_avatar_count: int
    new_avatar_count: int
    changed_avatar_list: List[ChangedAvatar]
    has_data: bool


class RoundData(TypedDict):
    avatars: List[PoetryAbyssAvatar]
    choice_cards: List[PoetryAbyssChoiceCard]
    buffs: List[PoetryAbyssBuff]
    is_get_medal: bool
    round_id: int
    finish_time: int
    finish_date_time: PoetryAbyssDateTime
    enemies: List[PoetryEnemy]
    splendour_buff: SplendourBuff
    is_tarot: bool
    tarot_serial_no: int


class PoetryAbyssDetail(TypedDict):
    rounds_data: List[RoundData]
    detail_stat: PoetryAbyssDetailStat
    backup_avatars: List[PoetryAbyssAvatar]
    fight_statisic: FightStatistic


class ScheduleDetail(TypedDict):
    rounds_data: List[RoundData]
    detail_stat: DetailStat
    lineup_link: str
    backup_avatars: List[BackupAvatar]
    fight_statisic: FightStatistic


class Schedule(TypedDict):
    detail: ScheduleDetail
    stat: CombatStat
    schedule: ScheduleInfo
    has_data: bool
    has_detail_data: bool


class RoleCombat(TypedDict):
    schedule_list: List[Schedule]
    is_unlock: bool


class SeasonPostData(TypedDict):
    avatar_info: AvatarInfo
    weapon_info: WeaponInfo
    costume_info: CostumeInfo
    exploration_info: ExplorationInfo
    resource_info: ResourceInfo
    history_stat_info: HistoryStatInfo
    spiral_abyss_info: List[SpiralAbyssInfo]
    gcg_info: GCGInfo
    role_combat: RoleCombat


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
