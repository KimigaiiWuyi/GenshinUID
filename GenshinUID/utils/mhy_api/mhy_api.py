OLD_URL = 'https://api-takumi.mihoyo.com'
NEW_URL = 'https://api-takumi-record.mihoyo.com'
BBS_URL = 'https://bbs-api.mihoyo.com'
HK4_URL = 'https://hk4e-api.mihoyo.com'

OLD_URL_OS = 'https://api-os-takumi.mihoyo.com'
NEW_URL_OS = 'https://bbs-api-os.hoyolab.com'
BBS_URL_OS = 'https://bbs-api-os.hoyolab.com'
HK4_URL_OS = 'https://hk4e-api-os.hoyoverse.com'
SIGN_URL_OS = 'https://sg-hk4e-api.hoyolab.com'

BBS_TASKLIST = BBS_URL + '/apihub/sapi/getUserMissionsState'

'''GT'''
# AJAX 无感验证
GT_TEST = 'https://api.geetest.com/ajax.php?'
GT_TEST_V6 = 'https://apiv6.geetest.com/ajax.php?'
GT_QUERY = 'gt={}&challenge={}&lang=zh-cn&pt=3&client_type=web_mobile'

GT_TEST_URL = GT_TEST + GT_QUERY
GT_TEST_URL_V6 = GT_TEST_V6 + GT_QUERY

GT_TPYE_URL = 'https://api.geetest.com/gettype.php?gt={}'
VERIFICATION_URL = (
    NEW_URL + '/game_record/app/card/wapi/createVerification?is_high=false'
)
VERIFY_URL = NEW_URL + '/game_record/app/card/wapi/verifyVerification'

'''账号相关'''
# 通过LoginTicket获取Stoken
GET_STOKEN_URL = OLD_URL + '/auth/api/getMultiTokenByLoginTicket'
# 通过Stoken获取Cookie_token
GET_COOKIE_TOKEN_URL = OLD_URL + '/auth/api/getCookieAccountInfoBySToken'
# 通过Stoken获取AuthKey
GET_AUTHKEY_URL = OLD_URL + '/binding/api/genAuthKey'
# 通过AuthKey获取gachalogs
GET_GACHA_LOG_URL = HK4_URL + '/event/gacha_info/api/getGachaLog'
GET_GACHA_LOG_URL_OS = HK4_URL_OS + '/event/gacha_info/api/getGachaLog'

'''米游社相关'''
# 获取签到列表
SIGN_LIST_URL = OLD_URL + '/event/bbs_sign_reward/home'
SIGN_LIST_URL_OS = SIGN_URL_OS + '/event/sol/home'
# 获取签到信息
SIGN_INFO_URL = OLD_URL + '/event/bbs_sign_reward/info'
SIGN_INFO_URL_OS = SIGN_URL_OS + '/event/sol/info'
# 执行签到
SIGN_URL = OLD_URL + '/event/bbs_sign_reward/sign'
SIGN_URL_OS = SIGN_URL_OS + '/event/sol/sign'

'''原神相关'''
# 每日信息 树脂 派遣等
DAILY_NOTE_URL = NEW_URL + '/game_record/app/genshin/api/dailyNote'
DAILY_NOTE_URL_OS = NEW_URL_OS + '/game_record/genshin/api/dailyNote'
# 每月札记
MONTHLY_AWARD_URL = HK4_URL + '/event/ys_ledger/monthInfo'
MONTHLY_AWARD_URL_OS = HK4_URL_OS + '/event/ysledgeros/month_info'
# 获取角色基本信息
PLAYER_INFO_URL = NEW_URL + '/game_record/app/genshin/api/index'
PLAYER_INFO_URL_OS = NEW_URL_OS + '/game_record/genshin/api/index'
# 获取深渊信息
PLAYER_ABYSS_INFO_URL = NEW_URL + '/game_record/app/genshin/api/spiralAbyss'
PLAYER_ABYSS_INFO_URL_OS = NEW_URL_OS + '/game_record/genshin/api/spiralAbyss'
# 获取详细角色信息
PLAYER_DETAIL_INFO_URL = NEW_URL + '/game_record/app/genshin/api/character'
PLAYER_DETAIL_INFO_URL_OS = NEW_URL_OS + '/game_record/genshin/api/character'
# 天赋计算器API 获取天赋等级信息
CALCULATE_INFO_URL = (
    OLD_URL + '/event/e20200928calculate/v1/sync/avatar/detail'
)
CALCULATE_INFO_URL_OS = (
    'https://sg-public-api.hoyoverse.com/event/calculateos/sync/avatar/detail'
)
# 获取米游社内的角色信息 mysid -> uid
MIHOYO_BBS_PLAYER_INFO_URL = (
    NEW_URL + '/game_record/card/wapi/getGameRecordCard'
)
MIHOYO_BBS_PLAYER_INFO_URL_OS = (
    NEW_URL_OS + '/game_record/card/wapi/getGameRecordCard'
)

# 获取七圣召唤相关信息
GCG_INFO = NEW_URL + '/game_record/app/genshin/api/gcg/basicInfo'
GCG_INFO_OS = NEW_URL_OS + '/game_record/genshin/api/gcg/basicInfo'

# 米游社的API列表
bbs_Taskslist = BBS_URL + '/apihub/sapi/getUserMissionsState'  # 获取任务列表
bbs_Signurl = BBS_URL + '/apihub/app/api/signIn'  # post
bbs_Listurl = (
    BBS_URL + '/post/api/getForumPostList?'
    'forum_id={}&is_good=false&is_hot=false&page_size=20&sort_type=1'
)
bbs_Detailurl = BBS_URL + '/post/api/getPostFull?post_id={}'
bbs_Shareurl = BBS_URL + '/apihub/api/getShareConf?entity_id={}&entity_type=1'
bbs_Likeurl = BBS_URL + '/apihub/sapi/upvotePost'  # post json
