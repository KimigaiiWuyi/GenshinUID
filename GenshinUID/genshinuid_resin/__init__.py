from .notice import get_noic_list
from .resin_text import get_resin_text
from .draw_resin_card import get_resin_img
from ..all_import import *  # noqa: F403,F401
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import *  # noqa: F403,F401


@sv.on_fullmatch('当前状态')
async def send_daily_info(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[每日信息文字版]')
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return

    if at:
        qid = at.group(1)

    logger.info('[每日信息文字版]QQ号: {}'.format(qid))

    uid: str = await select_db(qid, mode='uid')  # type: ignore
    logger.info('[每日信息文字版]UID: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await get_resin_text(uid)
    await bot.send(ev, im)


@sv.scheduled_job('cron', minute='*/30')
async def notice_job():
    bot = get_bot()
    result = await get_notice_list()
    logger.info('[推送检查]完成!等待消息推送中...')
    # 执行私聊推送
    bot_ids = bot._wsr_api_clients.keys()
    for qid in result[0]:
        send_success = False
        for sid in bot_ids:
            try:
                await bot.send_private_msg(
                    self_id=sid,
                    user_id=qid,
                    message=result[0][qid],
                )
                send_success = True
                break
            except:
                logger.info(f'[推送检查(轮推)] BOT {sid} 没有 {qid} 好友，已跳过')
        if not send_success:
            logger.warning(f'[推送检查] QQ {qid} 私聊推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]私聊推送完成')
    # 执行群聊推送
    for group_id in result[1]:
        send_success = False
        for sid in bot_ids:
            try:
                await bot.send_group_msg(
                    self_id=sid,
                    group_id=group_id,
                    message=result[1][group_id],
                )
                send_success = True
                break
            except:
                logger.info(f'[推送检查(轮推)] BOT {sid} 没有 {group_id}群，已跳过')
        if not send_success:
            logger.warning(f'[推送检查] 群 {group_id} 推送失败!')
        await asyncio.sleep(0.5)
    logger.info('[推送检查]群聊推送完成')

# @sv.on_fullmatch(('人工开启推送检查任务'))
# async def  manual_notice_job(bot: HoshinoBot, ev: CQEvent):
#     if ev.user_id != 1102566608:
#         return
#     await notice_job()
#     await bot.send(ev, '推送检查任务已执行')

@sv.on_fullmatch(('每日', 'mr', '实时便笺', '便笺', '便签'))
async def send_daily_info_pic(bot: HoshinoBot, ev: CQEvent):
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

    im = await get_resin_img(qid)
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')
