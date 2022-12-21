import asyncio
import threading
from typing import List
from pathlib import Path

from ..all_import import *
from .get_card import get_gs_card
from .get_guide import get_gs_guide
from ..version import Genshin_version
from .get_abyss_data import get_review, generate_data
from ..utils.alias.alias_to_char_name import alias_to_char_name

IMG_PATH = Path(__file__).parent / 'img'


@sv.on_rex('([\u4e00-\u9fa5]+)(推荐|攻略)')
async def send_guide_pic(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        name = name = str(ev['match'].group(1))
    else:
        return

    if name == '':
        return

    im = await get_gs_guide(name)

    if im:
        logger.info('获得{}攻略成功！'.format(name))
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        logger.warning('未找到{}攻略图片'.format(name))


@sv.on_prefix('参考面板')
async def send_bluekun_pic(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    if message == '':
        return

    if str(message) in ['冰', '水', '火', '草', '雷', '风', '岩']:
        name = str(message)
    else:
        name = await alias_to_char_name(str(message))
    img = IMG_PATH / '{}.jpg'.format(name)
    if img.exists():
        img = await convert_img(img)
        logger.info('获得{}参考面板图片成功！'.format(name))
        await bot.send(ev, img)
    else:
        logger.warning('未找到{}参考面板图片'.format(name))


@sv.on_prefix('原牌')
async def send_gscard_pic(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        name = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    if name == '':
        return

    im = await get_gs_card(name)

    if im:
        logger.info('获得{}原牌成功！'.format(name))
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        logger.warning('未找到{}原牌图片'.format(name))


@sv.on_prefix('版本深渊')
async def send_abyss_review(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        version = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    if version == '':
        version = Genshin_version[:-2]

    im = await get_review(version)

    if isinstance(im, List):
        mes = []
        for msg in im:
            mes.append(
                {
                    'type': 'node',
                    'data': {
                        'name': '小仙',
                        'uin': '3399214199',
                        'content': msg,
                    },
                }
            )
        await hoshino_bot.send_group_forward_msg(
            group_id=ev.group_id, messages=mes
        )
    elif isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


threading.Thread(
    target=lambda: asyncio.run(generate_data()), daemon=True
).start()
