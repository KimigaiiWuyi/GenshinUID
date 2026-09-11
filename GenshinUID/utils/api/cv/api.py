BASE = "https://akasha.cv/api"

MAIN_API = BASE + "/filters/accounts/"
RANK_API = BASE + "/getCalculationsForUser/{}"
BUILDS_API = BASE + "/builds?uid={}"
DATA_API = BASE + "/user/{}"
REFRESH_API = BASE + "/user/refresh/{}"
LEADERBOARD_API = BASE + "/v2/leaderboards/categories?characterId={}"
CATEGORIES_API = BASE + "/v2/leaderboards/categories"
CHARTS_CALC_API = BASE + "/charts/calculations/{}"
SUBSTAT_PRIORITY_API = BASE + "/substatPriority/{}/{}"
BUILD_LB_API = BASE + "/leaderboards/{}/{}"
DAMAGE_DIST_API = BASE + "/damageDistribution/{}/{}/{}"

stygian_prompt = "sort=playerInfo.stygianScore"
SORT_PROMPT = "sort=calculation.result"
UNI_PROMPT = "order=-1&size=20&page=1&filter=&uids=&fromId="
SORT_API = BASE + "/leaderboards?" + SORT_PROMPT + "&calculationId={}&" + UNI_PROMPT
GLOBAL_LB_API = (
    BASE + "/leaderboards?sort=calculation.result&calculationId={}&order=-1&page=1&filter=&uids=&fromId=&p=&size={}"
)
NEARBY_LB_API = (
    BASE + "/leaderboards?sort=calculation.result&calculationId={}"
    "&order=-1&page=1&filter=&uids=&fromId=&p=lt%7C{}&size={}"
)
ARTI_SORT_API = BASE + "/artifacts?sort={}&p=&" + UNI_PROMPT

STYGIAN_API = BASE + "/accounts?" + f"{stygian_prompt}&{UNI_PROMPT}"
HASH_ROW_API = BASE + "/getCollectionSize/?variant=accounts&hash="
