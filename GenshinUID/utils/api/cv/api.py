BASE = 'https://akasha.cv/api'

MAIN_API = BASE + '/filters/accounts/'
RANK_API = BASE + '/getCalculationsForUser/{}'
DATA_API = BASE + '/user/{}'
REFRESH_API = BASE + '/user/refresh/{}'
LEADERBOARD_API = BASE + '/v2/leaderboards/categories?characterId={}'

SORT_PROMOT = 'sort=calculation.result&'
UNI_PROMOT = 'order=-1&size=20&page=1&filter=&uids=&fromId='
SORT_API = (
    BASE + '/leaderboards?' + SORT_PROMOT + 'p=&calculationId={}' + UNI_PROMOT
)
ARTI_SORT_API = BASE + '/artifacts?sort={}&p=' + UNI_PROMOT
