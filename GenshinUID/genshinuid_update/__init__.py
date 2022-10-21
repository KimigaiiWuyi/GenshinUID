from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
from nonebot import get_bot, on_regex, get_driver, on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, MessageSegment

from ..utils.nonebot2.rule import FullCommand
from .draw_update_log import draw_update_log_img
from .restart import restart_message, restart_genshinuid

gs_restart = on_command('gs重启', rule=FullCommand())
get_update_log = on_command('更新记录', rule=FullCommand())
gs_update = on_regex(
    r'^(gs)(强行)?(强制)?(更新)$',
    block=True,
)


driver = get_driver()


@driver.on_bot_connect
async def _():
    logger.info('检查遗留信息...')
    bot = get_bot()
    update_log = await restart_message()
    if update_log == {}:
        return
    if update_log['send_type'] == 'group':
        await bot.call_api(
            api='send_group_msg',
            group_id=update_log['send_to'],
            message=update_log['msg'],
        )
    else:
        await bot.call_api(
            api='send_private_msg',
            user_id=update_log['send_to'],
            message=update_log['msg'],
        )
    logger.info('遗留信息检查完毕!')


@get_update_log.handle()
async def send_updatelog_msg(
    matcher: Matcher,
):
    im = await draw_update_log_img(is_update=False)
    logger.info('正在执行[更新记录]...')
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@gs_restart.handle()
async def send_restart_msg(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
):
    if not await SUPERUSER(bot, event):
        return
    logger.warning('开始执行[重启]')
    qid = event.user_id
    if len(event.get_session_id().split('_')) == 3:
        send_id = event.get_session_id().split('_')[1]
        send_type = 'group'
    else:
        send_id = qid
        send_type = 'private'
    await matcher.send('正在执行[gs重启]...')
    await restart_genshinuid(send_type, str(send_id))


@gs_update.handle()
async def send_update_msg(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    if not await SUPERUSER(bot, event):
        return

    logger.info('[gs更新] 正在执行 ...')
    level = 2
    if args[1] is None:
        level -= 1
    if args[2] is None:
        level -= 1
    logger.info(f'[gs更新] 更新等级为{level}')
    await matcher.send(f'开始执行[gs更新], 执行等级为{level}')
    im = await draw_update_log_img(level)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
