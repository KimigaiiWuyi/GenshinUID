from typing import Any, Tuple, Union

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .get_gachalogs import save_gachalogs
from .draw_gachalogs import draw_gachalogs_img
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception

get_gacha_log = on_command('刷新抽卡记录')
get_gacha_log_card = on_command('抽卡记录')


@get_gacha_log_card.handle()
@handle_exception('抽卡记录')
async def send_gacha_log_card_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = CommandArg(),
):
    logger.info('开始执行[抽卡记录]')
    if args:
        return
    uid = await select_db(event.user_id, mode='uid')
    if isinstance(uid, str):
        im = await draw_gachalogs_img(uid)
        if isinstance(im, bytes):
            await matcher.finish(MessageSegment.image(im))
        else:
            await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)


@get_gacha_log.handle()
@handle_exception('刷新抽卡记录')
async def send_daily_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = CommandArg(),
):
    logger.info('开始执行[刷新抽卡记录]')
    if args:
        return
    uid = await select_db(event.user_id, mode='uid')
    if isinstance(uid, str):
        im = await save_gachalogs(uid)
        await matcher.finish(im)
    else:
        await matcher.finish(UID_HINT)
