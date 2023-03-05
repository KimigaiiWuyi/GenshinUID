from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from .draw_gcginfo import draw_gcg_info
from ..utils.error_reply import UID_HINT


@SV('查询七圣').on_command(('七圣召唤', 'qszh'))
async def send_gcg_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[七圣召唤]uid: {}'.format(uid))

    im = await draw_gcg_info(uid)
    await bot.send(im)
