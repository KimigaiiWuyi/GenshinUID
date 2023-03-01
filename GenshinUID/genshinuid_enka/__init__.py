import re
from typing import Tuple

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .to_data import switch_api
from .to_card import enka_to_card
from ..utils.convert import get_uid
from .get_enka_img import draw_enka_img
from ..utils.error_reply import UID_HINT
from .draw_char_rank import draw_cahrcard_list


@SV('面板设置', pm=2).on_fullmatch('切换api')
async def send_change_api_info(bot: Bot):
    await bot.send(await switch_api())


@SV('面板查询', priority=10).on_prefix('查询')
async def send_char_info(bot: Bot, ev: Event):
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    await bot.logger.info('开始执行[查询角色面板]')
    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色面板]uid: {}'.format(uid))

    im = await draw_enka_img(msg, uid, ev.image)
    if isinstance(im, str):
        await bot.send(im)
    elif isinstance(im, Tuple):
        await bot.send(im[0])
    else:
        await bot.send('发生未知错误')


@SV('面板查询', priority=10).on_command('强制刷新')
async def send_card_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[强制刷新]uid: {}'.format(uid))
    im = await enka_to_card(uid)
    await bot.logger.info(f'UID{uid}获取角色数据成功！')
    await bot.send(im)


@SV('面板查询', priority=10).on_command('毕业度统计')
async def send_charcard_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    user_id = ev.at if ev.at else ev.user_id
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_cahrcard_list(str(uid), user_id)
    await bot.logger.info(f'UID{uid}获取角色数据成功！')
    await bot.send(im)
