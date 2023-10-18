BASE = 'https://akasha.cv'

MAIN_API = BASE + '/api/filters/accounts/'
RANK_API = BASE + '/api/getCalculationsForUser/{}'
DATA_API = BASE + '/api/user/{}'
REFRESH_API = BASE + '/api/user/refresh/{}'
LEADERBOARD_API = BASE + '/api/v2/leaderboards/categories?characterId={}'

SORT_PROMOT = 'sort=calculation.result&order=-1&size=20'
SORT_API = (
    BASE
    + '/api/leaderboards?'
    + SORT_PROMOT
    + '&page=1&filter=&uids=&p=&fromId=&calculationId={}'
)
