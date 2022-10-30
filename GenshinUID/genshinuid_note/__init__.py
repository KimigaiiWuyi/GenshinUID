from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment

from .note_text import award
from ..config import priority
from .draw_note_card import draw_note_img
from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from ..utils.db_operation.db_operation import select_db
from ..utils.message.error_reply import CK_HINT, UID_HINT
from ..utils.exception.handle_exception import handle_exception

monthly_data = on_command('每月统计', priority=priority, rule=FullCommand())
get_genshin_info = on_command(
    '当前信息', aliases={'zj', '札记', '原石札记'}, priority=priority, rule=FullCommand()
)


# 群聊内 每月统计 功能
@monthly_data.handle()
@handle_exception('每月统计', '获取/发送每月统计失败', '@未找到绑定信息\n' + CK_HINT)
@register_menu(
    '文字札记',
    '每月统计',
    '文字形式米游社札记',
    detail_des=(
        '介绍：\n'
        '文字形式米游社札记\n'
        ' \n' 
        '指令：\n'
        '- <ft color=(238,120,0)>每月统计</ft>'
    ),
)
async def send_monthly_data(
    event: MessageEvent,
    matcher: Matcher,
):
    qid = event.user_id
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        if '未找到绑定的UID' in uid:
            await matcher.finish(UID_HINT)
    else:
        await matcher.finish('发生未知错误...')
    im = await award(uid)
    await matcher.finish(im, at_sender=True)


# 群聊内 每月统计 功能
@get_genshin_info.handle()
@handle_exception('每月统计', '获取/发送每月统计失败', '@未找到绑定信息\n' + CK_HINT)
@register_menu(
    '图片札记',
    '当前信息',
    '图片形式米游社札记',
    detail_des=(
        '介绍：\n'
        '图片形式米游社札记\n'
        ' \n' 
        '指令：\n'
        '- <ft color=(238,120,0)>当前信息</ft>\n'
        '- <ft color=(125,125,125)>(原石)</ft><ft color=(238,120,0)>札记</ft>\n'
        '- <ft color=(238,120,0)>zj</ft>'
    ),
)
async def send_monthly_pic(
    event: MessageEvent,
    matcher: Matcher,
):
    qid = event.user_id
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        if '未找到绑定的UID' in uid:
            await matcher.finish(UID_HINT)
    else:
        await matcher.finish('发生未知错误...')
    logger.info(f'[原石札记] 开始绘制,UID: {uid}')
    im = await draw_note_img(uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
