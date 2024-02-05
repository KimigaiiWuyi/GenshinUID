import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .get_regtime import calc_reg_time
from .draw_roleinfo_card import draw_pic

sv_get_regtime = SV('查询注册时间')
sv_get_info = SV('查询原神信息')


@sv_get_regtime.on_command(
    ('原神注册时间', '注册时间', '查询注册时间'), block=True
)
async def regtime(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询注册时间]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return bot.send(UID_HINT)
    await bot.logger.info('[查询注册时间]uid: {}'.format(uid))

    im = await calc_reg_time(uid)
    await bot.send(im)


@sv_get_info.on_command(('查询', 'uid', 'UID'))
async def send_role_info(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    if name:
        return
    await bot.logger.info('开始执行[查询角色信息]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询角色信息]uid: {}'.format(uid))

    a = Button('🔍查询探索', '查询探索')
    b = Button('🔍查询收集', '查询收集')
    c = Button('💖刷新面板', '刷新面板')
    t = Button('🌌查询深渊', '查询深渊')
    s = Button('✨查询体力', '每日')
    u = Button('🆚查询七圣', '七圣召唤')
    v = Button('✉原石札记', '原石札记')
    x = Button('⏱注册时间', '原神注册时间')
    y = Button('💗抽卡记录', '抽卡记录')

    im = await draw_pic(uid)
    await bot.send_option(im, [[a, b, c], [t, s, u], [v, x, y]])
