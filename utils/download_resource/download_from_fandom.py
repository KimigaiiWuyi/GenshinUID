import re
import random
import asyncio

import aiofiles  # type: ignore
from bs4 import BeautifulSoup
from nonebot.log import logger
from aiohttp.client import ClientSession

MAX_TASKS = 4
from .RESOURCE_PATH import *  # noqa: E501
from ..alias.avatarId_and_name_covert import name_to_avatar_id

baseurl = 'https://genshin-impact.fandom.com/wiki/Genshin_Impact_Wiki'


async def get_url(url: str, sess: ClientSession):
    req = await sess.get(url=url)
    return await req.read()


async def _download(
    url: str,
    sess: ClientSession,
    sem: asyncio.Semaphore,
    file_name: str,
    file_path: Path,
    log_prefix: str,
):
    async with sem:
        logger.info(f'{log_prefix}正在下载 {file_name} ,URL为{url}')
        async with sess.get(url, timeout=60) as res:
            content = await res.read()

        if res.status != 200:
            logger.info(f"{log_prefix}{file_name} 下载失败: {res.status}")

        async with aiofiles.open(file_path / file_name, "+wb") as f:
            await asyncio.sleep(random.randint(0, 3))
            await f.write(content)
            logger.info(f"{log_prefix}{file_name} 下载成功: {res.status}")


async def get_char_url_list():
    async with ClientSession() as sess:
        base_data = await get_url(baseurl, sess)
        content_bs = BeautifulSoup(base_data, 'lxml')
        raw_data_5star = content_bs.find_all(
            "div", class_='card_container card_5 hidden'
        )
        raw_data_4star = content_bs.find_all(
            "div", class_='card_container card_4 hidden'
        )
        raw_data_5astar = content_bs.find_all(
            "div", class_='card_container card_5a hidden'
        )
        raw_data = raw_data_5star + raw_data_4star + raw_data_5astar
        char_list = {}
        for i in raw_data:
            char_url = (
                "https://genshin-impact.fandom.com"
                + i.find("a")["href"]
                + "/Media"
            )
            if i.find("a")["title"] != "Traveler":
                char_list[i.find("a")["title"]] = char_url
        return char_list


async def download_by_fandom(char_list: dict):
    # 判断需要下载哪些名片和抽卡图片
    if len(list(CHAR_NAMECARD_PATH.iterdir())) < len(char_list) or len(
        list(CHAR_STAND_PATH.iterdir())
    ) < len(char_list):
        logger.info(f'[fandom] 本次需要下载图片')
        await get_namecard_and_gacha_pic(char_list)
    else:
        logger.info('[fandom] 无需下载名片和抽卡图片!')
    return ''


async def get_namecard_and_gacha_pic(char_list: dict):
    tasks = []
    sem = asyncio.Semaphore(MAX_TASKS)
    async with ClientSession() as sess:
        li = char_list.keys()
        for index, i in enumerate(li):
            log_prefix = f'[fandom {index + 1}/{len(li)}] '

            char_data = await get_url(char_list[i], sess)
            char_info_data = await get_url(char_list[i][:-6], sess)
            info_bs = BeautifulSoup(char_info_data, 'lxml')
            chinese_name = info_bs.find_all("span", lang='zh-Hans')[0].text
            avatar_id = await name_to_avatar_id(chinese_name)
            logger.info(f'{log_prefix}正在下载{chinese_name}的图片资源...')
            char_data_bs = BeautifulSoup(char_data, 'lxml')

            gachaImg_data = char_data_bs.find_all(
                "img", {'data-caption': 'Full Wish'}
            )
            namecard_data = char_data_bs.find_all(
                "div", class_='wikia-gallery-item'
            )

            # 特殊排除
            if i == "Gorou":
                namecard = namecard_data[-3].find_all("img")[0]["src"]
            else:
                namecard = namecard_data[-2].find_all("img")[0]["src"]

            gachaImg_url = re.search(r"[\s\S]+.png", gachaImg_data[0]['src'])
            if gachaImg_url:
                gachaImg_url = gachaImg_url.group(0)
            else:
                continue
            namecard_url = re.search(r"[\s\S]+.png", namecard)
            if namecard_url:
                namecard_url = namecard_url.group(0)
            else:
                continue

            # 添加任务
            logger.info(f'{log_prefix}添加{chinese_name}的名片资源下载任务...')
            tasks.append(
                asyncio.wait_for(
                    _download(
                        namecard_url,
                        sess,
                        sem,
                        f'{chinese_name}.png',
                        CHAR_NAMECARD_PATH,
                        log_prefix,
                    ),
                    timeout=30,
                )
            )
            logger.info(f'{log_prefix}添加{chinese_name}的抽卡图片资源下载任务...')
            tasks.append(
                asyncio.wait_for(
                    _download(
                        gachaImg_url,
                        sess,
                        sem,
                        f'{chinese_name}.png',
                        GACHA_IMG_PATH,
                        log_prefix,
                    ),
                    timeout=30,
                )
            )
            if len(tasks) >= MAX_TASKS:
                await asyncio.gather(*tasks)
                tasks = []

        await asyncio.gather(*tasks)
        logger.info('全部下载完成！')
        return '资源下载成功!'
