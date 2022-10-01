from .note_text import award
from ..all_import import *  # noqa
from .draw_note_card import draw_note_img


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


@sv.on_fullmatch(('当前信息', 'zj', '原石札记', '札记'))
async def send_monthly_pic(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[每日信息]')
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    logger.info('[每日信息]QQ号: {}'.format(qid))

    im = await draw_note_img(str(qid))
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')
