from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_cale_pic import draw_cale_img
from ..utils.buttons import a, b, c, s, t, u, v, x, y

sv_cale = SV('个人日历')


@sv_cale.on_command(
    ('个人日历', '日历', '查询个人日历', '查询日历'), block=True
)
async def send_cale_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[个人日历] uid: {uid}')

    im = await draw_cale_img(ev, uid)
    await bot.send_option(im, [[a, b, c], [t, s, u], [v, x, y]])
