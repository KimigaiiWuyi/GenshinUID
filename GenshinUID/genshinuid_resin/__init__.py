import asyncio
from typing import Union

from nonebot.log import logger
from nonebot.params import Depends
from nonebot.matcher import Matcher
from nonebot import get_bot, require, on_command
from nonebot.adapters.qqguild import MessageEvent

from .notice import get_notice_list
from .resin_text import get_resin_text
from .draw_resin_card import get_resin_img
from ..utils.nonebot2.rule import FullCommand
from ..utils.nonebot2.send import local_image
from ..utils.message.error_reply import UID_HINT
from ..utils.message.cast_type import cast_to_int
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.exception.handle_exception import handle_exception

notice_scheduler = require('nonebot_plugin_apscheduler').scheduler
get_resin_info = on_command(
    '每日',
    aliases={'mr', '状态', '实时便笺', '便笺', '便签'},
    block=True,
    rule=FullCommand(),
)
get_daily_info = on_command('当前状态', rule=FullCommand())


@get_daily_info.handle()
@handle_exception('每日信息文字版')
async def send_daily_info(
    event: MessageEvent,
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[每日信息文字版]')

    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    if at:
        qid = at
    logger.info('[每日信息文字版]QQ号: {}'.format(qid))

    uid: str = await select_db(qid, mode='uid')  # type: ignore
    logger.info('[每日信息文字版]UID: {}'.format(uid))

    if not uid:
        await matcher.finish(UID_HINT)

    im = await get_resin_text(uid)
    await matcher.finish(im)


@notice_scheduler.scheduled_job('cron', minute='*/30')
async def notice_job():
    bot = get_bot()
    result = await get_notice_list()
    logger.info('[推送检查]完成!等待消息推送中...')
    # 执行私聊推送
    for qid in result[0]:
        try:
            await bot.call_api(
                api='send_private_msg',
                user_id=qid,
                message=result[0][qid],
            )
        except Exception:
            logger.warning(f'[推送检查] QQ {qid} 私聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]私聊推送完成')
    # 执行群聊推送
    for group_id in result[1]:
        try:
            await bot.call_api(
                api='send_group_msg',
                group_id=group_id,
                message=result[1][group_id],
            )
        except Exception:
            logger.warning(f'[推送检查] 群 {group_id} 群聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]群聊推送完成')


@get_resin_info.handle()
@handle_exception('每日信息')
async def send_uid_info(
    event: MessageEvent,
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[每日信息]')

    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    if at:
        qid = at
    logger.info('[每日信息]QQ号: {}'.format(qid))
    qid = int(qid)
    im = await get_resin_img(qid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(local_image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
