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

from ..genshinuid_meta import register_menu
from ..utils.message.error_reply import UID_HINT
from .draw_collection_card import draw_collection_img
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid
from ..utils.exception.handle_exception import handle_exception

get_collection_info = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?'
    r'(收集|宝箱|sj|bx)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
    block=True,
)


@get_collection_info.handle()
@handle_exception('查询收集信息')
@register_menu(
    '查询收集信息',
    '查询(@某人)收集',
    '查询你的或者指定人的宝箱收集度',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>[查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>/uidxxx/mysxxx]</ft>'
        '<ft color=(238,120,0)>[收集/宝箱/sj/bx]</ft>\n'
        ' \n'
        '可以用来查看你的或者指定人的宝箱收集度\n'
        '可以在命令文本后带一张图以自定义背景图\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>查询收集</ft>；\n'
        '<ft color=(238,120,0)>uid123456789宝箱</ft>；\n'
        '<ft color=(238,120,0)>查询</ft><ft color=(0,148,200)>@无疑Wuyi'
        '</ft> <ft color=(238,120,0)>bx</ft>'
    ),
)
async def send_collection_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询收集信息]')
    logger.info('[查询收集信息]参数: {}'.format(args))
    at = custom.get_first_at()
    if at:
        qid = at
    else:
        qid = event.user_id

    if args[2] != 'mys':
        if args[3] is None:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])
    logger.info('[查询收集信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_collection_img(uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
