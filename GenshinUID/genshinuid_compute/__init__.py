from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .get_my_pack import draw_my_pack

sv_pack = SV('查询背包')


@sv_pack.on_command(('我的背包', '我的物品'))
async def my_bag(bot: Bot, ev: Event):
    uid, user_id = await get_uid(bot, ev, True)
    if not uid:
        return await bot.send(UID_HINT)

    im = await draw_my_pack(uid, ev)
    await bot.send(im)
