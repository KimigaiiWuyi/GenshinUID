from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import MessageEvent

from .note_text import award
from ..config import priority
from ..utils.nonebot2.rule import FullCommand
from ..utils.db_operation.db_operation import select_db
from ..utils.message.error_reply import CK_HINT, UID_HINT
from ..utils.exception.handle_exception import handle_exception

monthly_data = on_command('每月统计', priority=priority, rule=FullCommand())
# get_genshin_info = on_command('当前信息', priority=priority)


# 群聊内 每月统计 功能
@monthly_data.handle()
@handle_exception('每月统计', '获取/发送每月统计失败', '@未找到绑定信息\n' + CK_HINT)
async def send_monthly_data(
    event: MessageEvent,
    matcher: Matcher,
):
    qid = event.sender.user_id
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        if '未找到绑定的UID' in uid:
            await matcher.finish(UID_HINT)
    else:
        await matcher.finish('发生未知错误...')
    im = await award(uid)
    await matcher.finish(im, at_sender=True)
