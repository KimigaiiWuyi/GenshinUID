import json

from httpx import AsyncClient

from .enka_api import ENKA_DATA_URL

HEADER = {'User-Agent': 'GenshinUID/3.0'}


async def get_enka_info(uid: str):
    """
    :说明:
      返回角色信息。
    :参数:
      * uid (str): 玩家uid。
    :返回:
      * dict: 角色信息。
    """
    url = ENKA_DATA_URL.format(uid)
    async with AsyncClient() as client:
        req = await client.get(url=url, headers=HEADER)
    data = json.loads(req.text)
    return data
