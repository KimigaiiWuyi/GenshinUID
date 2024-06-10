from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .get_my_pack import draw_my_pack

sv_pack = SV('查询背包')


@sv_pack.on_command(('我的背包'))
async def my_bag(bot: Bot, ev: Event):
    uid, user_id = await get_uid(bot, ev, True)
    if not uid:
        return await bot.send(UID_HINT)

    im = await draw_my_pack(uid, ev)
    await bot.send(im)
