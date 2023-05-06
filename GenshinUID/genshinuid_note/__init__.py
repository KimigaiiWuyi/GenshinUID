from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import UID_HINT

from .note_text import award
from ..utils.convert import get_uid
from ..utils.database import get_sqla
from .draw_note_card import draw_note_img

sv_get_monthly_data = SV('查询札记')


# 群聊内 每月统计 功能
@sv_get_monthly_data.on_fullmatch(('每月统计'))
async def send_monthly_data(bot: Bot, ev: Event):
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return UID_HINT
    await bot.send(await award(uid))


@sv_get_monthly_data.on_fullmatch(('当前信息', 'zj', '札记'))
async def send_monthly_pic(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[每日信息]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return UID_HINT
    im = await draw_note_img(str(uid))
    await bot.send(im)
