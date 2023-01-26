import re
from typing import Union

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, CommandArg
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from .get_regtime import calc_reg_time
from .draw_roleinfo_card import draw_pic
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.exception.handle_exception import handle_exception

get_role_info = on_command('uid', aliases={'查询'})
get_reg_time = on_command(
    '原神注册时间', aliases={'注册时间', '查询注册时间'}, rule=FullCommand()
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
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    raw_mes = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
    if name:
        return
    qid = event.user_id
    at = custom.get_first_at()
    if at:
        qid = at

    # 获取uid
    uid = re.findall(r'\d+', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)

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


@get_reg_time.handle()
async def regtime(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
):
    qid = event.user_id
    at = custom.get_first_at()
    if at:
        qid = at

    uid = await select_db(qid, mode='uid')
    uid = str(uid)

    logger.info('开始执行[查询注册时间]')
    logger.info('[查询注册时间]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await calc_reg_time(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
