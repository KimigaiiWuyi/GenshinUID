from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_season_post import get_season_post_draw

sv_seasonpost = SV('原神季报')


@sv_seasonpost.on_fullmatch(('季报'))
async def send_seasonpost(bot: Bot, ev: Event):
    logger.info('[原神] 开始执行[查询季报]')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(f'[原神] [查询季报] uid: {uid}')

    img = await get_season_post_draw(uid, ev)
    return await bot.send(img)
