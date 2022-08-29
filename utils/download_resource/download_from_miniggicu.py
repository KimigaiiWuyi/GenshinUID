from pathlib import Path

from bs4 import BeautifulSoup
from nonebot.log import logger
from aiohttp.client import ClientSession

from .download_url import PATH_MAP, download_file

MINIGG_FILE = 'https://file.minigg.icu/genshin/KimigaiiWuyi/resource/'
NAMECARD_FILE = MINIGG_FILE + 'char_namecard'
SIDE_FILE = MINIGG_FILE + 'char_side'
STAND_FILE = MINIGG_FILE + 'char_stand'
CHARS_FILE = MINIGG_FILE + 'chars'
GACHA_FILE = MINIGG_FILE + 'gacha_img'
ICON_FILE = MINIGG_FILE + 'icon'
REL_FILE = MINIGG_FILE + 'reliquaries'
WEAPON_FILE = MINIGG_FILE + 'weapon'

FILE_TO_PATH = {
    NAMECARD_FILE: 6,
    SIDE_FILE: 3,
    STAND_FILE: 2,
    CHARS_FILE: 1,
    GACHA_FILE: 4,
    ICON_FILE: 8,
    REL_FILE: 7,
    WEAPON_FILE: 5,
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
}


async def _get_url(url: str, sess: ClientSession):
    req = await sess.get(url=url)
    return await req.read()


async def download_all_file_from_miniggicu():
    async with ClientSession() as sess:
        for file in [
            NAMECARD_FILE,
            SIDE_FILE,
            STAND_FILE,
            CHARS_FILE,
            GACHA_FILE,
            ICON_FILE,
            REL_FILE,
            WEAPON_FILE,
        ]:
            base_data = await _get_url(file, sess)
            content_bs = BeautifulSoup(base_data, 'lxml')
            pre_data = content_bs.find_all('pre')[0]
            data_list = pre_data.find_all('a')
            logger.info(
                f'[minigg.icu]数据库[{FILE_TO_NAME[file]}]中存在{len(data_list)}个内容!'
            )
            temp_num = 0
            for data in data_list:
                url = f'{file}/{data["href"]}'
                name = data.text
                path = Path(PATH_MAP[FILE_TO_PATH[file]] / name)
                if not path.exists():
                    logger.info(
                        f'[minigg.icu]开始下载[{FILE_TO_NAME[file]}]_[{name}]...'
                    )
                    temp_num += 1
                    await download_file(url, FILE_TO_PATH[file], name)
                    logger.info('[minigg.icu]下载完成!')
            if temp_num == 0:
                im = f'[minigg.icu]数据库[{FILE_TO_NAME[file]}]无需下载!'
            else:
                im = f'[minigg.icu]数据库[{FILE_TO_NAME[file]}]已下载{temp_num}个内容!'
            temp_num = 0
            logger.info(im)
