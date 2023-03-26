from __future__ import annotations

import sys
from typing import List, Literal, Optional, TypedDict

# https://peps.python.org/pep-0655/#usage-in-python-3-11
if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired


# Response about
# https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index
# https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/character
# 玩家、武器、圣遗物、角色模型


class MihoyoRole(TypedDict):
    AvatarUrl: str
    nickname: str
    region: str
    level: int


class MihoyoWeapon(TypedDict):
    id: int
    name: str
    icon: str
    type: int
    rarity: int
    level: int
    promote_level: int
    type_name: Literal['单手剑', '双手剑', '长柄武器', '弓', '法器']
    desc: str
    affix_level: int


class ReliquaryAffix(TypedDict):
    activation_number: int
    effect: str


class ReliquarySet(TypedDict):
    id: int
    name: str
    affixes: List[ReliquaryAffix]


class MihoyoReliquary(TypedDict):
    id: int
    name: str
    icon: str
    pos: int
    rarity: int
    level: int
    set: ReliquarySet
    pos_name: str


class MihoyoConstellation(TypedDict):
    id: int
    name: str
    icon: str
    effect: str
    is_actived: bool
    pos: int


class MihoyoCostume(TypedDict):
    id: int
    name: str
    icon: str


class MihoyoAvatar(TypedDict):
    id: int
    image: str
    icon: str
    '''在api/character接口有'''
    name: str
    element: Literal[
        'Geo', 'Anemo', 'Dendro', 'Electro', 'Pyro', 'Cryo', 'Hydro'
    ]
    fetter: int
    level: int
    rarity: int
    weapon: MihoyoWeapon
    '''在api/character接口有'''
    reliquaries: List[MihoyoReliquary]
    '''在api/character接口有'''
    constellations: List[MihoyoConstellation]
    '''在api/character接口有'''
    actived_constellation_num: int
    costumes: List[MihoyoCostume]
    '''在api/character接口有'''
    card_image: str
    '''在api/index接口有'''
    is_chosen: bool
    '''在api/index接口有'''


# Response
# https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/spiralAbyss


class AbyssAvatar(TypedDict):
    avatar_id: int
    avatar_icon: str
    value: int
    rarity: int


class AbyssBattleAvatar(TypedDict):
    id: int
    icon: str
    level: int
    rarity: int


class AbyssBattle(TypedDict):
    index: int
    timestamp: str
    avatars: List[AbyssBattleAvatar]


class AbyssLevel(TypedDict):
    index: int
    star: int
    max_star: int
    battles: List[AbyssBattle]


class AbyssFloor(TypedDict):
    index: int
    icon: str
    is_unlock: bool
    settle_time: str
    star: int
    max_star: int
    levels: List[AbyssLevel]


class AbyssData(TypedDict):
    schedule_id: int
    start_time: str
    end_time: str
    total_battle_times: int
    total_win_times: int
    max_floor: str
    reveal_rank: List[AbyssAvatar]
    defeat_rank: List[AbyssAvatar]
    damage_rank: List[AbyssAvatar]
    take_damage_rank: List[AbyssAvatar]
    normal_skill_rank: List[AbyssAvatar]
    energy_skill_rank: List[AbyssAvatar]
    floors: List[AbyssFloor]
    total_star: int
    is_unlock: bool


# Response
# https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote


class Expedition(TypedDict):
    avatar_side_icon: str
    status: Literal['Ongoing', 'Finished']
    remained_time: int


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


class DailyNoteData(TypedDict):
    current_resin: int
    max_resin: int
    resin_recovery_time: int
    finished_task_num: int
    total_task_num: int
    is_extra_task_reward_received: bool
    remain_resin_discount_num: int
    resin_discount_num_limit: int
    current_expedition_num: int
    max_expedition_num: int
    expeditions: List[Expedition]
    current_home_coin: int
    max_home_coin: int
    home_coin_recovery_time: int
    calendar_url: str
    transformer: Transformer


# Response from https://api-takumi.mihoyo.com/game_record/app/genshin/api/index


class Stats(TypedDict):
    active_day_number: int
    achievement_number: int
    anemoculus_number: int
    geoculus_number: int
    avatar_number: int
    way_point_number: int
    domain_number: int
    spiral_abyss: str
    precious_chest_number: int
    luxurious_chest_number: int
    exquisite_chest_number: int
    common_chest_number: int
    electroculus_number: int
    magic_chest_number: int
    dendroculus_number: int


class Offering(TypedDict):
    name: str
    level: int
    icon: str


class WorldExploration(TypedDict):
    level: int
    exploration_percentage: int
    icon: str
    name: str
    type: str
    offerings: List[Offering]
    id: int
    parent_id: int
    map_url: str
    strategy_url: str
    background_image: str
    inner_icon: str
    cover: str


class Home(TypedDict):
    level: int
    visit_num: int
    comfort_num: int
    item_num: int
    name: str
    icon: str
    comfort_level_name: str
    comfort_level_icon: str


class IndexData(TypedDict):
    role: MihoyoRole
    avatars: List[MihoyoAvatar]
    stats: Stats
    city_explorations: List
    world_explorations: List[WorldExploration]
    homes: List[Home]


class CharDetailData(TypedDict):
    avatars: List[MihoyoAvatar]


################
# Token Models #
################


class CookieTokenInfo(TypedDict):
    uid: str
    cookie_token: str


class StokenInfo(TypedDict):
    token_type: NotRequired[int]
    name: NotRequired[str]
    token: str


class GameTokenInfo(TypedDict):
    token: StokenInfo
    user_info: UserInfo


class LoginTicketInfo(TypedDict):
    list: List[StokenInfo]


class AuthKeyInfo(TypedDict):
    sign_type: int
    authkey_ver: int
    authkey: str


class Hk4eLoginInfo(TypedDict):
    game: str
    region: str
    game_uid: str
    game_biz: str
    level: int
    nickname: str
    region_name: str


################
# 扫码登录相关 #
################


class QrCodeUrl(TypedDict):
    url: str


class QrPayload(TypedDict):
    proto: str
    raw: str
    ext: str


class QrCodeStatus(TypedDict):
    stat: Literal['Init', 'Scanned', 'Confirmed']
    payload: QrPayload


################
# UserInfo相关 #
################


class UserLinks(TypedDict):
    thirdparty: str
    union_id: str
    nickname: str


class UserInfo(TypedDict):
    aid: str
    mid: str
    account_name: str
    email: str
    is_email_verify: int
    area_code: str
    mobile: str
    safe_area_code: str
    safe_mobile: str
    realname: str
    identity_code: str
    rebind_area_code: str
    rebind_mobile: str
    rebind_mobile_time: str
    links: List[UserLinks]


################
# 抽卡记录相关 #
################


class SingleGachaLog(TypedDict):
    uid: str
    gacha_type: str
    item_id: str
    count: str
    time: str
    name: str
    lang: str
    item_type: str
    rank_type: str
    id: str


class GachaLog(TypedDict):
    page: str
    size: str
    total: str
    list: List[SingleGachaLog]
    region: str


################
# 注册时间相关 #
################


class CardOpts(TypedDict):
    adjs: List[int]
    titles: List[int]
    items: List[int]
    data_version: str


Props = TypedDict(
    'Props',
    {
        '66a': str,
        '50a': str,
        '53b': str,
        'pre_69b': str,
        '49a': str,
        '52b': str,
        'pre_71b': str,
        '37': str,
        '48a': str,
        '57': str,
    },
)


class RegTime(TypedDict):
    data: str
    card_opts: CardOpts
    props: Props
    data_version: int
    prop_version: int


################
# 七圣召唤相关 #
################


class CardCovers(TypedDict):
    id: int
    image: str


class GcgInfo(TypedDict):
    level: int
    nickname: str
    avatar_card_num_gained: int
    avatar_card_num_total: int
    action_card_num_gained: int
    action_card_num_total: int
    covers: List[CardCovers]


################
# 每月札记相关 #
################


class DayData(TypedDict):
    current_primogems: int
    current_mora: int
    last_primogems: int
    last_mora: int


class GroupBy(TypedDict):
    action_id: int
    action: str
    num: int
    percent: int


class MonthData(TypedDict):
    current_primogems: int
    current_mora: int
    last_primogems: int
    last_mora: int
    current_primogems_level: int
    primogems_rate: int
    mora_rate: int
    group_by: List[GroupBy]


class MonthlyAward(TypedDict):
    uid: int
    region: str
    account_id: str
    nickname: str
    date: str
    month: str
    optional_month: List[int]
    data_month: int
    data_last_month: int
    day_data: DayData
    month_data: MonthData
    lantern: bool


################
# 签到相关 #
################


class MysSign(TypedDict):
    code: str
    risk_code: int
    gt: str
    challenge: str
    success: int
    message: str


class SignInfo(TypedDict):
    total_sign_day: int
    today: str
    is_sign: bool
    first_bind: bool
    is_sub: bool
    month_first: bool
    sign_cnt_missed: int
    month_last_day: bool


class SignAward(TypedDict):
    icon: str
    name: str
    cnt: int


class SignList(TypedDict):
    month: int
    awards: List[SignAward]
    resign: bool


################
# 养成计算器部分 #
################


class CalculateInfo(TypedDict):
    skill_list: List[CalculateSkill]
    weapon: CalculateWeapon
    reliquary_list: List[CalculateReliquary]


class CalculateBaseData(TypedDict):
    id: int
    name: str
    icon: str
    max_level: int
    level_current: int


class CalculateWeapon(CalculateBaseData):
    weapon_cat_id: int
    weapon_level: int


class CalculateReliquary(CalculateBaseData):
    reliquary_cat_id: int
    reliquary_level: int


class CalculateSkill(CalculateBaseData):
    group_id: int


################
#  RecordCard  #
################


class MysGame(TypedDict):
    has_role: bool
    game_id: int  # 2是原神
    game_role_id: str  # UID
    nickname: str
    region: str
    level: int
    background_image: str
    is_public: bool
    data: List[MysGameData]
    region_name: str
    url: str
    data_switches: List[MysGameSwitch]
    h5_data_switches: Optional[List]
    background_color: str  # 十六进制颜色代码


class MysGameData(TypedDict):
    name: str
    type: int
    value: str


class MysGameSwitch(TypedDict):
    switch_id: int
    is_public: bool
    switch_name: str


'''支付相关'''


class MysGoods(TypedDict):
    goods_id: str
    goods_name: str
    goods_name_i18n_key: str
    goods_desc: str
    goods_desc_i18n_key: str
    goods_type: Literal['Normal', 'Special']
    goods_unit: str
    goods_icon: str
    currency: Literal['CNY']
    price: str
    symbol: Literal['￥']
    tier_id: Literal['Tier_1']
    bonus_desc: MysGoodsBonus
    once_bonus_desc: MysGoodsBonus
    available: bool
    tips_desc: str
    tips_i18n_key: str
    battle_pass_limit: str


class MysGoodsBonus(TypedDict):
    bonus_desc: str
    bonus_desc_i18n_key: str
    bonus_unit: int
    bonus_goods_id: str
    bonus_icon: str


class MysOrderCheck(TypedDict):
    status: int  # 900为成功
    amount: str
    goods_title: str
    goods_num: str
    order_no: str
    pay_plat: Literal['alipay', 'weixin']


class MysOrder(TypedDict):
    goods_id: str
    order_no: str
    currency: Literal['CNY']
    amount: str
    redirect_url: str
    foreign_serial: str
    encode_order: str
    account: str  # mysid
    create_time: str
    ext_info: str
    balance: str
    method: str
    action: str
    session_cookie: str


'''七圣召唤牌组'''


class GcgDeckInfo(TypedDict):
    deck_list: List[GcgDeck]
    role_id: str  # uid
    level: int  # 世界等级
    nickname: str


class GcgDeck(TypedDict):
    id: int
    name: str
    is_valid: bool
    avatar_cards: List[GcgAvatar]
    action_cards: List[GcgAction]


class GcgAvatarSkill(TypedDict):
    id: int
    name: str
    desc: str
    tag: Literal['普通攻击', '元素战技', '元素爆发', '被动技能']


class GcgAvatar(TypedDict):
    id: int
    name: str
    image: str
    desc: str
    card_type: Literal['CardTypeCharacter']
    num: int
    tags: List[str]  # 元素和武器类型icon
    proficiency: int
    use_count: int
    hp: int
    card_skills: List[GcgAvatarSkill]
    action_cost: List[GcgCost]
    card_sources: List[str]
    rank_id: int
    deck_recommend: str
    card_wiki: str


class GcgCost(TypedDict):
    cost_type: Literal['CostTypeSame', 'CostTypeVoid']
    cost_value: int


class GcgAction(TypedDict):
    id: int
    name: str
    image: str
    desc: str
    card_type: str
    num: int
    tags: List[str]  # 元素和武器类型icon
    proficiency: int
    use_count: int
    hp: int
    card_skills: List[GcgAvatarSkill]
    action_cost: List[GcgCost]
    card_sources: List[str]
    rank_id: int
    deck_recommend: str
    card_wiki: str


# 留影叙佳期
class GsRoleBirthDay(TypedDict):
    role_id: int
    name: str
    jump_tpye: str
    jump_target: str
    jump_start_time: str
    jump_end_time: str
    role_gender: int
    take_picture: str
    gal_xml: str
    gal_resource: str
    is_partake: bool
    bgm: str


class BsIndex(TypedDict):
    nick_name: str
    uid: int
    region: str
    role: List[GsRoleBirthDay]
    draw_notice: bool
    CurrentTime: str
    gender: int
    is_show_remind: bool


class RolesCalendar(TypedDict):
    calendar_role_infos: MonthlyRoleCalendar
    is_pre: bool
    is_next: bool
    is_year_subscribe: bool


class RoleCalendar(TypedDict):
    role_id: int
    name: str
    role_birthday: str
    head_icon: str
    is_subscribe: bool


MonthlyRoleCalendar = TypedDict(
    'MonthlyRoleCalendar',
    {
        '1': List[RoleCalendar],
        '2': List[RoleCalendar],
        '3': List[RoleCalendar],
        '4': List[RoleCalendar],
        '5': List[RoleCalendar],
        '6': List[RoleCalendar],
        '7': List[RoleCalendar],
        '8': List[RoleCalendar],
        '9': List[RoleCalendar],
        '10': List[RoleCalendar],
        '11': List[RoleCalendar],
        '12': List[RoleCalendar],
    },
)
