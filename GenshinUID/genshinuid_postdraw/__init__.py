from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import UID_HINT

from .get_draw import post_my_draw
from ..utils.database import get_sqla

sv_post_my_draw = SV('留影叙佳期')


# 群聊内 每月统计 功能
@sv_post_my_draw.on_fullmatch(('留影叙佳期'))
async def send_postdraw_data(bot: Bot, ev: Event):
    sqla = get_sqla(ev.bot_id)
    uid = await sqla.get_bind_uid(ev.user_id)
    if uid is None:
        return UID_HINT
    await bot.send(await post_my_draw(uid))
