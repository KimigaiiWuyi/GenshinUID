import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger
from gsuid_core.segment import MessageSegment

from ..utils.convert import get_uid
from .notice import get_notice_list
from .resin_text import get_resin_text
from ..utils.error_reply import UID_HINT
from .draw_resin_card import get_resin_img

sv_get_resin = SV('查询体力')
sv_get_resin_admin = SV('强制推送', pm=1)


@sv_get_resin.on_fullmatch(('当前状态'))
async def send_daily_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[每日信息文字版]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[每日信息文字版]UID: {}'.format(uid))

    im = await get_resin_text(uid)
    await bot.send(im)


@sv_get_resin_admin.on_fullmatch(('强制推送体力提醒'))
async def force_notice_job(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[强制推送体力信息]')
    await notice_job()


@scheduler.scheduled_job('cron', minute='*/30')
async def notice_job():
    result = await get_notice_list()
    logger.info('[推送检查]完成!等待消息推送中...')
    logger.debug(result)

    # 执行私聊推送
    for bot_id in result:
        for BOT_ID in gss.active_bot:
            bot = gss.active_bot[BOT_ID]
            for user_id in result[bot_id]['direct']:
                msg = result[bot_id]['direct'][user_id]
                await bot.target_send(msg, 'direct', user_id, bot_id, '', '')
                await asyncio.sleep(0.5)
            logger.info('[推送检查] 私聊推送完成')
            for gid in result[bot_id]['group']:
                msg_list = []
                for user_id in result[bot_id]['group'][gid]:
                    msg_list.append(MessageSegment.at(user_id))
                    msg = result[bot_id]['group'][gid][user_id]
                    msg_list.append(MessageSegment.text(msg))
                await bot.target_send(msg_list, 'group', gid, bot_id, '', '')
                await asyncio.sleep(0.5)
            logger.info('[推送检查] 群聊推送完成')


@sv_get_resin.on_fullmatch(('每日', 'mr', '实时便笺', '便笺', '便签'))
async def send_daily_info_pic(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[每日信息]')
    user_id = ev.at if ev.at else ev.user_id
    await bot.logger.info('[每日信息]QQ号: {}'.format(user_id))

    im = await get_resin_img(bot.bot_id, user_id)
    await bot.send(im)
