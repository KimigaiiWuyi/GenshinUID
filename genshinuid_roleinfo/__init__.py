from typing import Any, Tuple, Union

from nonebot import on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, RegexGroup
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .draw_roleinfo_card import draw_pic
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid
from ..utils.exception.handle_exception import handle_exception

get_role_info = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
    block=True,
)


@get_role_info.handle()
@handle_exception('查询角色信息')
async def send_role_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询角色信息]')
    logger.info('[查询角色信息]参数: {}'.format(args))
    qid = event.user_id

    at = custom.get_first_at()
    if at:
        qid = at

    # 判断uid
    if args[2] != 'mys':
        if args[3] is None:
            if args[2] is None:
                logger.info('[查询角色信息]uid为空, 直接结束~')
                return
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])

    logger.info('[查询角色信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_pic(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
