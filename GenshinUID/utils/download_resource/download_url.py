import aiofiles
from aiohttp.client import ClientSession

from .RESOURCE_PATH import (
    REL_PATH,
    CHAR_PATH,
    ICON_PATH,
    WEAPON_PATH,
    CHAR_SIDE_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
    CHAR_NAMECARD_PATH,
)

PATH_MAP = {
    1: CHAR_PATH,
    2: CHAR_STAND_PATH,
    3: CHAR_SIDE_PATH,
    4: GACHA_IMG_PATH,
    5: WEAPON_PATH,
    6: CHAR_NAMECARD_PATH,
    7: REL_PATH,
    8: ICON_PATH,
}


async def download_file(url: str, path: int, name: str):
    """
    :说明:
      下载URL保存入目录
    :参数:
      * url (str): 资源下载地址。
      * path (int): 资源保存路径
        '''
        1: CHAR_PATH,
        2: CHAR_STAND_PATH,
        3: CHAR_SIDE_PATH,
        4: GACHA_IMG_PATH,
        5: WEAPON_PATH,
        6: CHAR_NAMECARD_PATH,
        7: REL_PATH
        '''
      * name (str): 资源保存名称
    """
    async with ClientSession() as sess:
        async with sess.get(url) as res:
            content = await res.read()
    async with aiofiles.open(PATH_MAP[path] / name, "+wb") as f:
        await f.write(content)
