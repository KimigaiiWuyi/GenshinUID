from .update import update_genshinuid
from ..all_import import *  # noqa: F403,F401
from .restart import restart_message, restart_genshinuid

bot = get_bot()


@bot.on_startup
async def _():
    logger.info('检查遗留信息...')
    bot = get_bot()
    update_log = await restart_message()
    if update_log == {}:
        return
    if update_log['send_type'] == 'group':
        await bot.send_group_msg(
            group_id=update_log['send_to'],
            message=update_log['msg'],
        )
    else:
        await bot.send_private_msg(
            user_id=update_log['send_to'],
            message=update_log['msg'],
        )
    logger.info('遗留信息检查完毕!')


@sv.on_fullmatch('gs重启')
async def send_restart_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    logger.warning('开始执行[重启]')

    if ev.group_id:
        send_id = str(ev.group_id)
        send_type = 'group'
    else:
        send_id = qid
        send_type = 'private'
    await bot.send(ev, '正在执行[gs重启]...')
    await restart_genshinuid(send_type, str(send_id))


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
    await bot.send(ev, f'开始执行[gs更新], 执行等级为{level}')
    im = await update_genshinuid(level)
    await bot.send(ev, im)
