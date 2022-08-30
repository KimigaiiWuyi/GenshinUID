from pathlib import Path

import httpx

from ..all_import import *
from ..utils.alias.alias_to_char_name import alias_to_char_name

IMG_PATH = Path(__file__).parent / 'img'


@sv.on_rex('([\u4e00-\u9fa5]+)(推荐|攻略)')
async def send_guide_pic(bot: HoshinoBot, ev: CQEvent):
    name = str(ev['match'].group(1))
    if not name:
        return
    name = await alias_to_char_name(name)
    if name.startswith('旅行者'):
        name = f'{name[:3]}-{name[-1]}'
    url = 'https://img.genshin.minigg.cn/guide/{}.jpg'.format(name)
    if httpx.head(url).status_code == 200:
        logger.info('获得{}推荐图片成功！'.format(name))
        await bot.send(ev, MessageSegment.image(url))
    else:
        logger.warning('未获得{}推荐图片。'.format(name))


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
