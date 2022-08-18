OLD_URL = 'https://api-takumi.mihoyo.com'
NEW_URL = 'https://api-takumi-record.mihoyo.com'
BBS_URL = 'https://bbs-api.mihoyo.com'
HK4_URL = 'https://hk4e-api.mihoyo.com'

BBS_TASKLIST = BBS_URL + '/apihub/sapi/getUserMissionsState'

'''账号相关'''
# 通过LoginTicket获取Stoken
GET_STOKEN_URL = OLD_URL + '/auth/api/getMultiTokenByLoginTicket'
GET_COOKIE_TOKEN_URL = OLD_URL + '/auth/api/getCookieAccountInfoBySToken'

'''米游社相关'''
# 获取签到列表
SIGN_LIST_URL = OLD_URL + '/event/bbs_sign_reward/home'
# 获取签到信息
SIGN_INFO_URL = OLD_URL + '/event/bbs_sign_reward/info'
# 执行签到
SIGN_URL = OLD_URL + '/event/bbs_sign_reward/sign'

'''原神相关'''
# 每日信息 树脂 派遣等
DAILY_NOTE_URL = NEW_URL + '/game_record/app/genshin/api/dailyNote'
# 每月札记
MONTHLY_AWARD_URL = HK4_URL + '/event/ys_ledger/monthInfo'
# 获取角色基本信息
PLAYER_INFO_URL = NEW_URL + '/game_record/app/genshin/api/index'
# 获取深渊信息
PLAYER_ABYSS_INFO_URL = NEW_URL + '/game_record/app/genshin/api/spiralAbyss'
# 获取详细角色信息
PLAYER_DETAIL_INFO_URL = NEW_URL + '/game_record/app/genshin/api/character'
# 天赋计算器API 获取天赋等级信息
CALCULATE_INFO_URL = (
    OLD_URL + '/event/e20200928calculate/v1/sync/avatar/detail'
)
# 获取米游社内的角色信息 mysid -> uid
MIHOYO_BBS_PLAYER_INFO_URL = (
    NEW_URL + '/game_record/card/wapi/getGameRecordCard'
)

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
