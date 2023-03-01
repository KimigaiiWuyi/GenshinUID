from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.error_reply import UID_HINT
from .get_gachalogs import save_gachalogs
from .draw_gachalogs import draw_gachalogs_img


@SV('抽卡记录').on_fullmatch(('抽卡记录'))
async def send_gacha_log_card_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[抽卡记录]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_gachalogs_img(uid, ev.user_id)
    await bot.send(im)


@SV('抽卡记录').on_fullmatch(('刷新抽卡记录', '强制刷新抽卡记录'))
async def send_daily_info(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[刷新抽卡记录]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    is_force = False
    if ev.command.startswith('强制'):
        await bot.logger.info('[WARNING]本次为强制刷新')
        is_force = True
    im = await save_gachalogs(uid, None, is_force)
    await bot.send(im)
