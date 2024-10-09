from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .draw_new_collection_card import draw_explore
from .draw_collection_card import draw_explora_img, draw_collection_img

sv_cp = SV('查询完成度')
sv_sj = SV('查询收集')
sv_ts = SV('查询探索')


@sv_cp.on_command(('查询完成度', 'wcd'), block=True)
async def send_cp_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询完成度信息]')
    # user_id = ev.at if ev.at else ev.user_id

    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色面板]uid: {}'.format(uid))

    im = await draw_explore(uid)
    a = Button('🔍查询探索', '查询探索')
    b = Button('🔍查询收集', '查询收集')
    await bot.send_option(im, [a, b])


@sv_sj.on_command(('查询收集', 'sj', '收集'), block=True)
async def send_collection_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询收集信息]')

    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色面板]uid: {}'.format(uid))

    im = await draw_collection_img(ev, uid)
    a = Button('🔍查询探索', '查询探索')
    b = Button('🔍查询收集', '查询收集')
    await bot.send_option(im, [a, b])


@sv_ts.on_command(('查询探索', 'ts'), block=True)
async def send_explora_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询探索信息]')

    # 获取uid
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色面板]uid: {}'.format(uid))

    im = await draw_explora_img(ev, uid)
    a = Button('🔍查询探索', '查询探索')
    b = Button('🔍查询收集', '查询收集')
    await bot.send_option(im, [a, b])
