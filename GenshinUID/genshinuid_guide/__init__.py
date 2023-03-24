from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .get_guide import get_gs_guide
from ..version import Genshin_version
from .get_abyss_data import get_review
from ..utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import REF_PATH
from ..utils.map.name_covert import alias_to_char_name

sv_char_guide = SV('查询角色攻略')
sv_abyss_review = SV('查询深渊阵容')


@sv_char_guide.on_suffix(('攻略', '推荐'))
async def send_guide_pic(bot: Bot, ev: Event):
    im = await get_gs_guide(ev.text)

    if im:
        await bot.logger.info('获得{}攻略成功！'.format(ev.text))
        await bot.send(im)
    else:
        await bot.logger.warning('未找到{}攻略图片'.format(ev.text))


@sv_char_guide.on_prefix(('参考面板'))
async def send_bluekun_pic(bot: Bot, ev: Event):
    if ev.text in ['冰', '水', '火', '草', '雷', '风', '岩']:
        name = ev.text
    else:
        name = await alias_to_char_name(ev.text)
    img = REF_PATH / '{}.jpg'.format(name)
    if img.exists():
        img = await convert_img(img)
        await bot.logger.info('获得{}参考面板图片成功！'.format(name))
        await bot.send(img)
    else:
        await bot.logger.warning('未找到{}参考面板图片'.format(name))


@sv_abyss_review.on_command(('版本深渊', '深渊阵容'))
async def send_abyss_review(bot: Bot, ev: Event):
    if not ev.text:
        version = Genshin_version[:-2]
    else:
        version = ev.text

    im = await get_review(version)

    if isinstance(im, List):
        mes = [MessageSegment.text(msg) for msg in im]
        await bot.send(MessageSegment.node(mes))
    elif isinstance(im, str):
        await bot.send(im)
