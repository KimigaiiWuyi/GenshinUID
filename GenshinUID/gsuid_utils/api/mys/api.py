# flake8: noqa
OLD_URL = 'https://api-takumi.mihoyo.com'
NEW_URL = 'https://api-takumi-record.mihoyo.com'
BBS_URL = 'https://bbs-api.mihoyo.com'
HK4_URL = 'https://hk4e-api.mihoyo.com'
NEW_BBS_URL = 'https://bbs-api.miyoushe.com'

OLD_URL_OS = 'https://api-os-takumi.mihoyo.com'
NEW_URL_OS = 'https://bbs-api-os.hoyolab.com'
BBS_URL_OS = 'https://bbs-api-os.hoyolab.com'
HK4_URL_OS = 'https://hk4e-api-os.hoyoverse.com'
SIGN_URL_OS = 'https://sg-hk4e-api.hoyolab.com'
ACT_URL_OS = 'https://sg-hk4e-api.hoyoverse.com'

HK4E_LOGIN_URL = f'{OLD_URL}/common/badge/v1/login/account'
HK4E_LOGIN_URL_OS = f'{OLD_URL_OS}/common/badge/v1/login/account'

BBS_TASKLIST = f'{BBS_URL}/apihub/sapi/getUserMissionsState'

PASSPORT_URL = 'https://passport-api.mihoyo.com'
HK4_SDK_URL = 'https://hk4e-sdk.mihoyo.com'

'''GT'''
# AJAX 无感验证
GT_TEST = 'https://api.geetest.com/ajax.php?'
GT_TEST_V6 = 'https://apiv6.geetest.com/ajax.php?'
GT_QUERY = 'gt={}&challenge={}&lang=zh-cn&pt=3&client_type=web_mobile'

GT_TEST_URL = GT_TEST + GT_QUERY
GT_TEST_URL_V6 = GT_TEST_V6 + GT_QUERY

GT_TPYE_URL = 'https://api.geetest.com/gettype.php?gt={}'
VERIFICATION_URL = (
    f'{NEW_URL}/game_record/app/card/wapi/createVerification?is_high=false'
)
BBS_VERIFICATION_URL = (
    f'{NEW_BBS_URL}/game_record/app/card/wapi/createVerification?is_high=false'
)
VERIFY_URL = f'{NEW_URL}/game_record/app/card/wapi/verifyVerification'

'''账号相关'''
# 通过LoginTicket获取Stoken
GET_STOKEN_URL = f'{OLD_URL}/auth/api/getMultiTokenByLoginTicket'
# 通过Stoken获取Cookie_token
GET_COOKIE_TOKEN_URL = f'{OLD_URL}/auth/api/getCookieAccountInfoBySToken'
# 通过Stoken获取AuthKey
GET_AUTHKEY_URL = f'{OLD_URL}/binding/api/genAuthKey'
# 通过AuthKey获取gachalogs
GET_GACHA_LOG_URL = f'{HK4_URL}/event/gacha_info/api/getGachaLog'
GET_GACHA_LOG_URL_OS = f'{HK4_URL_OS}/event/gacha_info/api/getGachaLog'
# 通过GameToken获取Stoken
GET_STOKEN = f'{PASSPORT_URL}/account/ma-cn-session/app/getTokenByGameToken'
# 创建登录URL
CREATE_QRCODE = f'{HK4_SDK_URL}/hk4e_cn/combo/panda/qrcode/fetch'
# 检查二维码扫描状态
CHECK_QRCODE = f'{HK4_SDK_URL}/hk4e_cn/combo/panda/qrcode/query'
# 通过GameToken获取Cookie_token
GET_COOKIE_TOKEN_BY_GAME_TOKEN = (
    f'{OLD_URL}/auth/api/getCookieAccountInfoByGameToken'
)

'''米游社相关'''
# 获取签到列表
SIGN_LIST_URL = f'{OLD_URL}/event/bbs_sign_reward/home'
SIGN_LIST_URL_OS = f'{SIGN_URL_OS}/event/sol/home'
# 获取签到信息
SIGN_INFO_URL = f'{OLD_URL}/event/bbs_sign_reward/info'
SIGN_INFO_URL_OS = f'{SIGN_URL_OS}/event/sol/info'
# 执行签到
SIGN_URL = f'{OLD_URL}/event/bbs_sign_reward/sign'
SIGN_URL_OS += '/event/sol/sign'

'''原神相关'''
# 每日信息 树脂 派遣等
DAILY_NOTE_URL = f'{NEW_URL}/game_record/app/genshin/api/dailyNote'
DAILY_NOTE_URL_OS = f'{NEW_URL_OS}/game_record/genshin/api/dailyNote'
# 每月札记
MONTHLY_AWARD_URL = f'{HK4_URL}/event/ys_ledger/monthInfo'
MONTHLY_AWARD_URL_OS = f'{HK4_URL_OS}/event/ysledgeros/month_info'
# 获取角色基本信息
PLAYER_INFO_URL = f'{NEW_URL}/game_record/app/genshin/api/index'
PLAYER_INFO_URL_OS = f'{NEW_URL_OS}/game_record/genshin/api/index'
# 获取深渊信息
PLAYER_ABYSS_INFO_URL = f'{NEW_URL}/game_record/app/genshin/api/spiralAbyss'
PLAYER_ABYSS_INFO_URL_OS = f'{NEW_URL_OS}/game_record/genshin/api/spiralAbyss'
# 获取详细角色信息
PLAYER_DETAIL_INFO_URL = f'{NEW_URL}/game_record/app/genshin/api/character'
PLAYER_DETAIL_INFO_URL_OS = f'{NEW_URL_OS}/game_record/genshin/api/character'
# 天赋计算器API 获取天赋等级信息
CALCULATE_INFO_URL = (
    f'{OLD_URL}/event/e20200928calculate/v1/sync/avatar/detail'
)
CALCULATE_INFO_URL_OS = (
    'https://sg-public-api.hoyoverse.com/event/calculateos/sync/avatar/detail'
)
# 获取米游社内的角色信息 mysid -> uid
MIHOYO_BBS_PLAYER_INFO_URL = (
    f'{NEW_URL}/game_record/card/wapi/getGameRecordCard'
)
MIHOYO_BBS_PLAYER_INFO_URL_OS = (
    f'{NEW_URL_OS}/game_record/card/wapi/getGameRecordCard'
)

# 获取七圣召唤相关信息
GCG_INFO = f'{NEW_URL}/game_record/app/genshin/api/gcg/basicInfo'
GCG_INFO_OS = f'{NEW_URL_OS}/game_record/genshin/api/gcg/basicInfo'
GCG_DECK_URL = f'{NEW_URL}/game_record/app/genshin/api/gcg/deckList'
GCG_DECK_URL_OS = f'{NEW_URL_OS}/game_record/app/genshin/api/gcg/deckList'

# 获取注册时间API 绘忆星辰
REG_TIME = f'{HK4_URL}/event/e20220928anniversary/game_data?'
REG_TIME_OS = f'{ACT_URL_OS}/event/e20220928anniversary/game_data?'

# 米游社的API列表
BBS_TASKS_LIST = f'{BBS_URL}/apihub/sapi/getUserMissionsState'
BBS_SIGN_URL = f'{BBS_URL}/apihub/app/api/signIn'
BBS_LIST_URL = (
    BBS_URL + '/post/api/getForumPostList?'
    'forum_id={}&is_good=false&is_hot=false&page_size=20&sort_type=1'
)
BBS_DETAIL_URL = BBS_URL + '/post/api/getPostFull?post_id={}'
BBS_SHARE_URL = BBS_URL + '/apihub/api/getShareConf?entity_id={}&entity_type=1'
BBS_LIKE_URL = f'{BBS_URL}/apihub/sapi/upvotePost'

# 原神充值中心
fetchGoodsurl = f'{HK4_SDK_URL}/hk4e_cn/mdk/shopwindow/shopwindow/fetchGoods'
CreateOrderurl = f'{HK4_SDK_URL}/hk4e_cn/mdk/atropos/api/createOrder'
CheckOrderurl = f'{HK4_SDK_URL}/hk4e_cn/mdk/atropos/api/checkOrder'
PriceTierurl = f'{HK4_SDK_URL}/hk4e_cn/mdk/shopwindow/shopwindow/listPriceTier'

# 留影叙佳期
DRAW_BASE_URL = f'{HK4_URL}/event/birthdaystar/account'
CALENDAR_URL = f'{DRAW_BASE_URL}/calendar'
RECEIVE_URL = f'{DRAW_BASE_URL}/post_my_draw'
BS_INDEX_URL = f'{DRAW_BASE_URL}/index'

_API = locals()
