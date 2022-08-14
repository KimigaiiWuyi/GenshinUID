import asyncio
from typing import Any, List, Tuple, Union

import aiofiles  # type: ignore
from nonebot.log import logger
from aiohttp.client import ClientSession

from .RESOURCE_PATH import *  # noqa: E501
from ..alias.alias_to_char_name import alias_to_char_name
from ..alias.avatarId_and_name_covert import name_to_avatar_id
from .resource_list import REL_ALL_LIST, CHAR_ALL_LIST, WEAPON_ALL_LIST
from ..minigg_api.get_minigg_data import (
    get_char_info,
    get_misc_info,
    get_weapon_info,
)

MAX_TASKS = 5


async def _download(
    url: str,
    sess: ClientSession,
    sem: asyncio.Semaphore,
    file_name: str,
    file_path: Path,
):
    async with sem:
        logger.info(f'正在下载{file_name},URL为{url}')
        async with sess.get(url) as res:
            content = await res.read()

        if res.status != 200:
            logger.info(f"下载失败: {res.status}")

        async with aiofiles.open(file_path / file_name, "+wb") as f:
            await f.write(content)
            logger.info(f"下载成功: {res.status}")


async def download_by_minigg():
    # 判断需要下载哪些角色图片
    char_download_list = []
    return_str = ''
    for char in CHAR_ALL_LIST:
        char_id = await name_to_avatar_id(char)
        char_path = CHAR_PATH / f'{char_id}.png'
        char_side_path = CHAR_SIDE_PATH / f'{char_id}.png'
        char_stand_path = CHAR_STAND_PATH / f'{char_id}.png'
        if not char_path.exists() or not char_side_path.exists():
            char_download_list.append(char)
    if char_download_list:
        logger.info(f'本次需要下载{",".join(char_download_list)}的图片')
        char_faild = await get_char_pic(char_download_list)
        if char_faild:
            return_str += f'下载{",".join(char_faild)}的图片失败'
            logger.info(f'下载{",".join(char_faild)}的图片失败')
    else:
        logger.info('无需下载角色图片!')

    # 判断需要下载哪些武器图片
    weapon_download_list = []
    for weapon in WEAPON_ALL_LIST:
        weapon_path = WEAPON_PATH / f'{weapon}.png'
        if not weapon_path.exists():
            weapon_download_list.append(weapon)
    if weapon_download_list:
        logger.info(f'本次需要下载{",".join(weapon_download_list)}的图片')
        weapon_faild = await get_weapon_pic(weapon_download_list)
        if weapon_faild:
            return_str += f'下载{",".join(weapon_faild)}的图片失败'
            logger.info(f'下载{",".join(weapon_faild)}的图片失败')
    else:
        logger.info('无需下载武器图片!')

    # 判断需要下载哪些圣遗物图片
    rel_download_list = []
    for rel in REL_ALL_LIST:
        rel_path = REL_PATH / f'{rel}.png'
        if not rel_path.exists():
            rel_download_list.append(rel)
    if rel_download_list:
        logger.info(f'本次需要下载{",".join(rel_download_list)}的图片')
        rel_faild = await get_rel_pic(rel_download_list)
        if rel_faild:
            return_str += f'下载{",".join(rel_faild)}的图片失败'
            logger.info(f'下载{",".join(rel_faild)}的图片失败')
    else:
        logger.info('无需下载圣遗物图片!')

    return return_str


async def get_char_pic(name_list: List):
    """
    :说明:
      接受角色名称保存图片至RESOURCE目录
      RESOURCE_PATH / 'chars'
      RESOURCE_PATH / 'char_stand'
      RESOURCE_PATH / 'char_side'
      保存立绘、侧视图、头像Icon
      保存为f'{avatar_id}.png'
    :参数:
      * name_list (str): 角色名称列表。
    """
    tasks = []
    faild = []
    sem = asyncio.Semaphore(MAX_TASKS)
    async with ClientSession() as sess:
        for name in name_list:
            logger.info(f'正在下载角色{name}的图片')
            name = await alias_to_char_name(name)
            avatar_id = await name_to_avatar_id(name)

            char_path = CHAR_PATH / f'{avatar_id}.png'
            char_side_path = CHAR_SIDE_PATH / f'{avatar_id}.png'
            char_stand_path = CHAR_STAND_PATH / f'{avatar_id}.png'

            raw_data = await get_char_info(name)
            if name in ['空', '荧']:
                pass
            else:
                if not char_stand_path.exists():
                    stand_url = raw_data['images']['cover1']
                    tasks.append(
                        asyncio.wait_for(
                            _download(
                                stand_url,
                                sess,
                                sem,
                                f'{avatar_id}.png',
                                CHAR_STAND_PATH,
                            ),
                            timeout=35,
                        )
                    )
            if not char_side_path.exists():
                side_url = raw_data['images']['sideicon']
                tasks.append(
                    asyncio.wait_for(
                        _download(
                            side_url,
                            sess,
                            sem,
                            f'{avatar_id}.png',
                            CHAR_SIDE_PATH,
                        ),
                        timeout=30,
                    )
                )
            if not char_path.exists():
                icon_url = raw_data['images']['icon']
                tasks.append(
                    asyncio.wait_for(
                        _download(
                            icon_url,
                            sess,
                            sem,
                            f'{avatar_id}.png',
                            CHAR_PATH,
                        ),
                        timeout=30,
                    )
                )
            if len(tasks) > MAX_TASKS:
                faild.extend(await _gather(tasks, faild, name))
                tasks = []
        faild.extend(await _gather(tasks, faild, '最后一个'))
    return faild


async def _gather(tasks: List, faild: List, name: str):
    try:
        await asyncio.gather(*tasks)
        await asyncio.sleep(1)
    except asyncio.exceptions.TimeoutError:
        logger.warning(f'{name}超时了!')
        faild.append(name)
    return faild


async def get_weapon_pic(name_list: List):
    """
    :说明:
      接受武器名称保存图片至RESOURCE目录
      会在RESOURCE_PATH / 'weapon'下
      保存为f'{weapon_name}.png'
    :参数:
      * name_list (str): 武器名称列表。
    """
    tasks = []
    faild = []
    sem = asyncio.Semaphore(MAX_TASKS)
    async with ClientSession() as sess:
        for name in name_list:
            logger.info(f'正在下载武器{name}的图片')
            raw_data = await get_weapon_info(name)
            icon_url = raw_data['images']['icon']
            tasks.append(
                asyncio.wait_for(
                    _download(
                        icon_url,
                        sess,
                        sem,
                        f'{name}.png',
                        WEAPON_PATH,
                    ),
                    timeout=30,
                )
            )
            if len(tasks) > MAX_TASKS:
                faild.extend(await _gather(tasks, faild, name))
                tasks = []
        faild.extend(await _gather(tasks, faild, '最后一个'))
    return faild


async def get_rel_pic(name_list: List):
    """
    :说明:
      接受圣遗物套装名称保存图片至RESOURCE目录
      会在RESOURCE_PATH / 'reliquaries'下
      一次性保存五个部件的PNG图片
    :参数:
      * name_list (str): 武器套装名称列表。
    """
    tasks = []
    faild = []
    sem = asyncio.Semaphore(MAX_TASKS)
    async with ClientSession() as sess:
        for name in name_list:
            logger.info(f'正在下载圣遗物{name}的图片')
            raw_data = await get_misc_info('artifacts', name)
            if '之人' in name:
                part_list = ['circlet']
            else:
                part_list = ['flower', 'plume', 'sands', 'goblet', 'circlet']
            for i in part_list:
                url = raw_data['images'][i]
                p_name = raw_data[i]['name']
                path = REL_PATH / f'{p_name}.png'
                if not path.exists():
                    tasks.append(
                        asyncio.wait_for(
                            _download(
                                url,
                                sess,
                                sem,
                                f'{p_name}.png',
                                REL_PATH,
                            ),
                            timeout=30,
                        )
                    )
            if len(tasks) > MAX_TASKS:
                faild.extend(await _gather(tasks, faild, name))
                tasks = []
        faild.extend(await _gather(tasks, faild, '最后一个'))
        return faild
