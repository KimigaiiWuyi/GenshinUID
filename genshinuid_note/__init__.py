from .note_text import award
from ..all_import import *  # noqa


# 群聊内 每月统计 功能
@sv.on_fullmatch('每月统计')
async def send_monthly_data(bot: HoshinoBot, ev: CQEvent):
    qid = int(ev.sender['user_id'])  # type: ignore
    uid = await select_db(qid, mode='uid')
    if isinstance(uid, str):
        if '未找到绑定的UID' in uid:
            await bot.send(ev, UID_HINT)
    else:
        await bot.send(ev, '发生未知错误...')
    im = await award(uid)
    await bot.send(ev, im, at_sender=True)
