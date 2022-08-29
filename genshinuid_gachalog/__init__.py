from typing import Any, Tuple, Union

from nonebot import on_command
from nonebot.adapters.onebot.v11 import (GroupMessageEvent, MessageSegment, PrivateMessageEvent)
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from .draw_gachalogs import draw_gachalogs_img
from .get_gachalogs import save_gachalogs
from ..genshinuid_meta import register_menu
from ..utils.db_operation.db_operation import select_db
from ..utils.exception.handle_exception import handle_exception
from ..utils.message.error_reply import UID_HINT

get_gacha_log = on_command('刷新抽卡记录')
get_gacha_log_card = on_command('抽卡记录')


@get_gacha_log_card.handle()
@handle_exception('抽卡记录')
@register_menu(
    '查询抽卡记录',
    '抽卡记录',
    '查询你的原神抽卡记录',
    detail_des=(
            '指令：'
            '<ft color=(238,120,0)>抽卡记录</ft>\n'
            ' \n'
            '查询你的原神抽卡记录\n'
            '需要<ft color=(238,120,0)>绑定Stoken</ft>'
    ),
)
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
@register_menu(
    '刷新抽卡记录',
    '刷新抽卡记录',
    '刷新你的原神抽卡记录本地缓存',
    detail_des=(
            '指令：'
            '<ft color=(238,120,0)>刷新抽卡记录</ft>\n'
            ' \n'
            '刷新你的原神抽卡记录本地缓存\n'
            '需要<ft color=(238,120,0)>绑定Stoken</ft>'
    ),
)
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
