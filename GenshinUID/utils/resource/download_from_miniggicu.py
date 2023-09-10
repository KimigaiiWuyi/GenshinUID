import os
import asyncio
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup
from aiohttp import TCPConnector
from gsuid_core.logger import logger
from aiohttp.client import ClientSession

from .download_url import PATH_MAP, download_file

# MINIGG_FILE = 'http://file.microgg.cn/KimigaiiWuyi/resource/'
BASE_TAG = '[HKFRP]'
BASE_URL = 'http://hk-1.5gbps-2.lcf.icu:10200/'
RESOURCE_FILE = f'{BASE_URL}/resource/'
WIKI_FILE = f'{BASE_URL}/wiki/'

NAMECARD_FILE = RESOURCE_FILE + 'char_namecard'
SIDE_FILE = RESOURCE_FILE + 'char_side'
STAND_FILE = RESOURCE_FILE + 'char_stand'
CHARS_FILE = RESOURCE_FILE + 'chars'
GACHA_FILE = RESOURCE_FILE + 'gacha_img'
ICON_FILE = RESOURCE_FILE + 'icon'
REL_FILE = RESOURCE_FILE + 'reliquaries'
WEAPON_FILE = RESOURCE_FILE + 'weapon'
GUIDE_FILE = WIKI_FILE + 'guide'
REF_FILE = WIKI_FILE + 'ref'

'''
NAMECARD_FILE = MINIGG_FILE + 'char_namecard'
SIDE_FILE = MINIGG_FILE + 'char_side'
STAND_FILE = MINIGG_FILE + 'char_stand'
CHARS_FILE = MINIGG_FILE + 'chars'
GACHA_FILE = MINIGG_FILE + 'gacha_img'
ICON_FILE = MINIGG_FILE + 'icon'
REL_FILE = MINIGG_FILE + 'reliquaries'
WEAPON_FILE = MINIGG_FILE + 'weapon'
GUIDE_FILE = MINIGG_FILE + 'guide'
REF_FILE = MINIGG_FILE + 'ref_image'
'''


FILE_TO_PATH = {
    NAMECARD_FILE: 6,
    SIDE_FILE: 3,
    STAND_FILE: 2,
    CHARS_FILE: 1,
    GACHA_FILE: 4,
    ICON_FILE: 8,
    REL_FILE: 7,
    WEAPON_FILE: 5,
    GUIDE_FILE: 10,
    REF_FILE: 12,
}

FILE_TO_NAME = {
    NAMECARD_FILE: '角色名片',
    SIDE_FILE: '角色侧视图',
    STAND_FILE: '角色半身照',
    CHARS_FILE: '角色头像',
    GACHA_FILE: '角色立绘',
    ICON_FILE: '图标',
    REL_FILE: '圣遗物',
    WEAPON_FILE: '武器',
    GUIDE_FILE: '攻略',
    REF_FILE: '参考面板',
}


async def _get_url(url: str, sess: ClientSession):
    req = await sess.get(url=url)
    return await req.read()


async def download_all_file_from_miniggicu():
    async def _download(tasks: List[asyncio.Task]):
        failed_list.extend(
            list(filter(lambda x: x is not None, await asyncio.gather(*tasks)))
        )
        tasks.clear()
        logger.info(f'{BASE_TAG}下载完成!')

    failed_list: List[Tuple[str, int, str]] = []
    TASKS = []
    async with ClientSession(connector=TCPConnector(verify_ssl=False)) as sess:
        for file in [
            NAMECARD_FILE,
            SIDE_FILE,
            STAND_FILE,
            CHARS_FILE,
            GACHA_FILE,
            ICON_FILE,
            REL_FILE,
            WEAPON_FILE,
            GUIDE_FILE,
            REF_FILE,
        ]:
            base_data = await _get_url(file, sess)
            content_bs = BeautifulSoup(base_data, 'lxml')
            pre_data = content_bs.find_all('pre')[0]
            data_list = pre_data.find_all('a')
            size_list = [i for i in content_bs.strings]
            logger.info(
                f'{BASE_TAG}数据库[{FILE_TO_NAME[file]}]中存在{len(data_list)}个内容!'
            )
            temp_num = 0
            for index, data in enumerate(data_list):
                if data['href'] == '../':
                    continue
                url = f'{file}/{data["href"]}'
                name = data.text
                size = size_list[index * 2 + 6].split(' ')[-1]
                size = size.replace('\r\n', '')
                path = Path(PATH_MAP[FILE_TO_PATH[file]] / name)
                if path.exists():
                    is_diff = size == str(os.stat(path).st_size)
                else:
                    is_diff = True
                if (
                    not path.exists()
                    or not os.stat(path).st_size
                    or not is_diff
                ):
                    logger.info(
                        f'{BASE_TAG}开始下载[{FILE_TO_NAME[file]}]_[{name}]...'
                    )
                    temp_num += 1
                    TASKS.append(
                        asyncio.wait_for(
                            download_file(url, FILE_TO_PATH[file], name, sess),
                            timeout=60,
                        )
                    )
                    # await download_file(url, FILE_TO_PATH[file], name)
                    if len(TASKS) >= 10:
                        await _download(TASKS)
            else:
                await _download(TASKS)
            if temp_num == 0:
                im = f'{BASE_TAG}数据库[{FILE_TO_NAME[file]}]无需下载!'
            else:
                im = f'{BASE_TAG}数据库[{FILE_TO_NAME[file]}]已下载{temp_num}个内容!'
            temp_num = 0
            logger.info(im)
    if failed_list:
        logger.info(f'{BASE_TAG}开始重新下载失败的{len(failed_list)}个文件...')
        for url, file, name in failed_list:
            TASKS.append(
                asyncio.wait_for(
                    download_file(url, file, name, sess),
                    timeout=60,
                )
            )
            if len(TASKS) >= 10:
                await _download(TASKS)
        else:
            await _download(TASKS)
        if count := len(failed_list):
            logger.error(f'{BASE_TAG}仍有{count}个文件未下载，请使用命令 `下载全部资源` 重新下载')
