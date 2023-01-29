import re

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.ntchat.message import Message
from nonebot.adapters.ntchat import MessageSegment, TextMessageEvent

from ..config import priority
from .draw_gcginfo import draw_gcg_info
from ..utils.db_operation.db_operation import select_db
from ..utils.message.error_reply import CK_HINT, UID_HINT
from ..utils.exception.handle_exception import handle_exception

get_gcg_info = on_command('七圣召唤', aliases={'七圣', '召唤'}, priority=priority)


# 群聊内 每月统计 功能
@get_gcg_info.handle()
@handle_exception('七圣召唤', '获取/发送七圣召唤失败', '@未找到绑定信息\n' + CK_HINT)
async def send_gcg_pic(
    event: TextMessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    raw_mes = args.extract_plain_text().strip().replace(' ', '')
    if "@" in raw_mes:
        name = ''.join(re.findall('^[\u4e00-\u9fa5]+', raw_mes.split("@")[0]))
        if name:
            return
    else:
        name = ''.join(re.findall('^[\u4e00-\u9fa5]+', raw_mes))
        if name:
            return
    logger.info('开始执行[七圣召唤]')
    qid = event.from_wxid
    if event.at_user_list:
        for user in event.at_user_list:
            user = user.strip()
            if user != "":
                qid = user
    logger.info('[七圣召唤]WXID: {}'.format(qid))

    # 获取uid
    uid = re.findall(r'\d+', raw_mes.split("@")[0])
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    logger.info('[七圣召唤]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_gcg_info(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
