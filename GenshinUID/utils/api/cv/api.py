BASE = "https://akasha.cv/api"

MAIN_API = BASE + "/filters/accounts/"
RANK_API = BASE + "/getCalculationsForUser/{}"
BUILDS_API = BASE + "/builds?uid={}"
DATA_API = BASE + "/user/{}"
REFRESH_API = BASE + "/user/refresh/{}"
LEADERBOARD_API = BASE + "/v2/leaderboards/categories?characterId={}"

stygian_prompt = "sort=playerInfo.stygianScore"
SORT_PROMPT = "sort=calculation.result"
UNI_PROMPT = "order=-1&size=20&page=1&filter=&uids=&fromId="
SORT_API = BASE + "/leaderboards?" + SORT_PROMPT + "&calculationId={}&" + UNI_PROMPT
ARTI_SORT_API = BASE + "/artifacts?sort={}&p=&" + UNI_PROMPT

STYGIAN_API = BASE + "/accounts?" + f"{stygian_prompt}&{UNI_PROMPT}"
HASH_ROW_API = BASE + "/getCollectionSize/?variant=accounts&hash="
