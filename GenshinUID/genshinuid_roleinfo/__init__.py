from typing import Any, Tuple, Union

from nonebot import on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, RegexGroup
from nonebot.adapters.ntchat import MessageSegment, TextMessageEvent

from .draw_roleinfo_card import draw_pic
from ..genshinuid_meta import register_menu
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
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
@register_menu(
    '查询帐号信息',
    '查询',
    '帐号基础数据与角色信息总览',
    detail_des=(
        '介绍：\n'
        '查询帐号探索度、声望、宝箱收集、角色总览等等基础数据\n'
        '未绑定CK时最多只能查询8个角色信息\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>{查询|uid}</ft>'
        '<ft color=(125,125,125)>({@某人|[UID]})</ft>\n'
        '- <ft color=(238,120,0)>mys</ft>'
        '<ft color=(125,125,125)>({@某人|[米游社ID]})</ft>\n'
        '- <ft color=(238,120,0)>直接发送九位数UID</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>查询</ft>\n'
        '- <ft color=(238,120,0)>查询</ft><ft color=(0,123,67)>@无疑Wuyi</ft>\n'
        '- <ft color=(238,120,0)>uid123456789</ft>\n'
        '- <ft color=(238,120,0)>123456789</ft>'
    ),
)
async def send_role_info(
    event: TextMessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    if event.at_user_list:
        qid = event.at_user_list[0]
    else:
        qid = event.from_wxid

    # 判断uid
    if args[2] != 'mys':
        if args[3] is None:
            if args[2] is None:
                await matcher.finish()
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])
    logger.info('开始执行[查询角色信息]')
    logger.info('[查询角色信息]参数: {}'.format(args))
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
