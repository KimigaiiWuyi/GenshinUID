from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .notice import send_notice_list
from .resin_text import get_resin_text
from .draw_resin_card import get_resin_img
from ..genshinuid_config.gs_config import gsconfig

sv_get_resin = SV('查询体力')
sv_get_resin_admin = SV('强制推送', pm=1)

is_check_resin = gsconfig.get_config('SchedResinPush').data


@sv_get_resin.on_fullmatch(('当前状态'))
async def send_daily_info(bot: Bot, ev: Event):
    logger.info('🔨 [GenshinUID]\n🌱 开始执行[每日信息文字版]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info('[每日信息文字版]UID: {}'.format(uid))

    im = await get_resin_text(uid)
    await bot.send(im)


@sv_get_resin_admin.on_fullmatch(('强制推送体力提醒'))
async def force_notice_job(bot: Bot, ev: Event):
    await bot.send('🔨 [GenshinUID]\n🌱 开始执行强制推送体力提醒!')
    await notice_job(True)
    await bot.send('🔨 [GenshinUID]\n✅ 强制推送体力提醒执行完成!')


@scheduler.scheduled_job('cron', minute='*/30')
async def notice_job(force: bool = False):
    if is_check_resin or force:
        await send_notice_list()


@sv_get_resin.on_fullmatch(('每日', 'mr', '实时便笺', '便笺', '便签'))
async def send_daily_info_pic(bot: Bot, ev: Event):
    logger.info('开始执行[每日信息]')
    user_id = ev.at if ev.at else ev.user_id
    logger.info('[每日信息]QQ号: {}'.format(user_id))

    im = await get_resin_img(bot.bot_id, user_id)
    await bot.send(im)
