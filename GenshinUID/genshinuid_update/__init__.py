import os

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment

from .restart import restart_message, restart_genshinuid
from .draw_update_log import get_all_update_log, draw_update_log_img

sv_gs_config = SV('GS管理', pm=1)
sv_update_history = SV('Core更新记录')


@gss.on_bot_connect
async def check_msg():
    try:
        logger.info('检查遗留信息...')
        update_log = await restart_message()
        if update_log == {}:
            return
        for BOT in gss.active_bot:
            bot = gss.active_bot[BOT]
            if update_log['send_type'] == 'group':
                await bot.target_send(
                    update_log['msg'],
                    'group',
                    update_log['send_to'],
                    update_log['bot_id'],
                    '',
                    '',
                )
            else:
                await bot.target_send(
                    update_log['msg'],
                    'direct',
                    update_log['send_to'],
                    update_log['bot_id'],
                    '',
                    '',
                )
        logger.info('遗留信息检查完毕!')
    except Exception:
        logger.warning('遗留信息检查失败!')


@sv_gs_config.on_fullmatch(('gs重启'))
async def send_restart_msg(bot: Bot, ev: Event):
    await bot.logger.warning('开始执行[重启]')
    if ev.group_id:
        send_id = ev.group_id
        send_type = 'group'
    else:
        send_id = ev.user_id
        send_type = 'direct'
    await bot.send('正在执行[gs重启]...')
    await restart_genshinuid(bot.bot_id, send_type, str(send_id))


@sv_gs_config.on_fullmatch(('GS关闭core', 'GS关闭Core'))
async def send_shutdown_msg(bot: Bot, ev: Event):
    await bot.logger.warning('开始执行[关闭]')
    await bot.send('正在执行[gs关闭Core]...')
    os._exit(0)


@sv_update_history.on_fullmatch(('更新记录'))
async def send_updatelog_msg(bot: Bot, ev: Event):
    await bot.logger.info('正在执行[更新记录]...')
    im = await draw_update_log_img(is_update=False)
    await bot.send(im)


@sv_gs_config.on_fullmatch(('gs更新', 'gs强制更新', 'gs强行强制更新', 'gs全部更新'))
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
