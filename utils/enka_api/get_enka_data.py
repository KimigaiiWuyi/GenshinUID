from asyncio.log import logger
import json

from httpx import AsyncClient

from .enka_api import ENKA_DATA_URL, MICROGG_DATA_URL, MINIGG_DATA_URL


ENKA_API = [MINIGG_DATA_URL, ENKA_DATA_URL, MICROGG_DATA_URL]
HEADER = {'User-Agent': 'GenshinUID/3.1'}


async def switch_api():
    """
    :说明:
      切换api。
    :返回:
      * str: 当前api。
    """
    global ENKA_API
    ENKA_API = [ENKA_API[-1]] + ENKA_API[:-1]
    return f'切换成功!当前api为{ENKA_API[0].replace("{}/__data.json","")}'


async def get_enka_info(uid: str):
    """
    :说明:
      返回角色信息。
    :参数:
      * uid (str): 玩家uid。
    :返回:
      * dict: 角色信息。
    """
    url = ENKA_API[0].format(uid)
    async with AsyncClient() as client:
        req = await client.get(url=url, headers=HEADER)
    try:
        data = json.loads(req.text)
    except:
        logger.exception(req.text)
        data = {}
    return data
