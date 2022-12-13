from pathlib import Path

from ..all_import import *
from .get_card import get_gs_card
from .get_guide import get_gs_guide
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
