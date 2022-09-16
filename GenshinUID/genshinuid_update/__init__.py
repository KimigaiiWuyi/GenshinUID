from .update import update_genshinuid
from ..all_import import *  # noqa: F403,F401


@sv.on_rex(r'^(gs)(强行)?(强制)?(更新)$')
async def send_update_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return

    args = ev['match'].groups()
    logger.info('[gs更新] 正在执行 ...')
    level = 2
    if args[1] is None:
        level -= 1
    if args[2] is None:
        level -= 1
    logger.info(f'[gs更新] 更新等级为{level}')

    im = await update_genshinuid(level)
    await bot.send(ev, im)
