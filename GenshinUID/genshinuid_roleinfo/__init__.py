import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from .get_regtime import calc_reg_time
from ..utils.error_reply import UID_HINT
from .draw_roleinfo_card import draw_pic

sv_get_regtime = SV('查询注册时间')
sv_get_info = SV('查询原神信息')


@sv_get_regtime.on_command(('原神注册时间', '注册时间', '查询注册时间'), block=True)
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
        return bot.send(UID_HINT)
    await bot.logger.info('[查询角色信息]uid: {}'.format(uid))

    im = await draw_pic(uid)
    await bot.send(im)
