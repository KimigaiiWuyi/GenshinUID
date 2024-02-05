from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .draw_update_log import get_all_update_log, draw_update_log_img

sv_gs_config = SV('GS管理', pm=1)
sv_update_history = SV('Core更新记录')


@sv_update_history.on_fullmatch(('更新记录'))
async def send_updatelog_msg(bot: Bot, ev: Event):
    await bot.logger.info('正在执行[更新记录]...')
    im = await draw_update_log_img(is_update=False)
    await bot.send(im)


@sv_gs_config.on_fullmatch(
    ('gs更新', 'gs强制更新', 'gs强行强制更新', 'gs全部更新')
)
async def send_update_msg(bot: Bot, ev: Event):
    await bot.logger.info('[gs更新] 正在执行 ...')
    level = 2
    if '全部' in ev.command:
        im = await get_all_update_log()
        return await bot.send(MessageSegment.node(im))
    if '强制' not in ev.command:
        level -= 1
    if '强行' not in ev.command:
        level -= 1
    await bot.logger.info(f'[gs更新] 更新等级为{level}')
    await bot.send(f'开始执行[gs更新], 执行等级为{level}')

    im = await draw_update_log_img(level)
    await bot.send(im)
