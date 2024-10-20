from typing import Tuple, Optional

import aiofiles
from gsuid_core.logger import logger
from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientConnectorError

from .RESOURCE_PATH import (
    REF_PATH,
    REL_PATH,
    CARD_PATH,
    CHAR_PATH,
    ICON_PATH,
    WIKI_PATH,
    GUIDE_PATH,
    WEAPON_PATH,
    ACHI_ICON_PATH,
    CHAR_SIDE_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
    CHAR_NAMECARD_PATH,
    CHAR_SIDE_TEMP_PATH,
    CHAR_NAMECARDPIC_PATH,
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
    9: CARD_PATH,
    10: GUIDE_PATH,
    11: WIKI_PATH,
    12: REF_PATH,
    13: CHAR_SIDE_TEMP_PATH,
    14: CHAR_NAMECARDPIC_PATH,
    15: ACHI_ICON_PATH,
}


async def download(
    url: str,
    path: int,
    name: str,
) -> Optional[Tuple[str, int, str]]:
    """
    :说明:
      下载URL保存入目录
    :参数:
      * url: `str`
            资源下载地址。
      * path: `int`
            资源保存路径
        '''
        1: CHAR_PATH,
        2: CHAR_STAND_PATH,
        3: CHAR_SIDE_PATH,
        4: GACHA_IMG_PATH,
        5: WEAPON_PATH,
        6: CHAR_NAMECARD_PATH,
        7: REL_PATH,
        8: ICON_PATH,
        9: CARD_PATH,
        10: GUIDE_PATH,
        11: WIKI_PATH,
        12: REF_PATH,
        13: CHAR_SIDE_TEMP_PATH,
        14: CHAR_NAMECARDPIC_PATH,
        15: ACHI_ICON_PATH,
        '''
      * name: `str`
            资源保存名称
    :返回(失败才会有返回值):
        url: `str`
        path: `int`
        name: `str`
    """
    async with ClientSession() as sess:
        return await download_file(url, path, name, sess)


async def download_file(
    url: str,
    path: int,
    name: str,
    sess: Optional[ClientSession] = None,
) -> Optional[Tuple[str, int, str]]:
    logger.info(f"开始下载: [{name}] - {url}")
    if sess is None:
        sess = ClientSession()
    try:
        async with sess.get(url) as res:
            content = await res.read()
    except ClientConnectorError:
        logger.warning(f"[minigg.icu]{name}下载失败")
        return url, path, name
    async with aiofiles.open(PATH_MAP[path] / name, "wb") as f:
        await f.write(content)
