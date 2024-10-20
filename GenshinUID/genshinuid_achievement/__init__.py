from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .draw_achi import draw_achi_img
from .get_achi_desc import get_achi, get_daily_achi

sv_task_achi = SV('成就委托查询')
sv_achi_search = SV('成就完成查询')


@sv_achi_search.on_command(('我的成就', '成就列表', '成就一览'))
async def send_achi_img(bot: Bot, ev: Event):
    logger.info(f'[成就列表] 参数：{ev.text}')
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_achi_img(ev, uid)
    await bot.send(im)


@sv_task_achi.on_prefix('查委托')
async def send_task_info(bot: Bot, ev: Event):
    logger.info(f'[查委托] 参数：{ev.text}')
    im = await get_daily_achi(ev.text)
    await bot.send(im)


@sv_task_achi.on_prefix('查成就')
async def send_achi_info(bot: Bot, ev: Event):
    logger.info(f'[查成就] 参数：{ev.text}')
    im = await get_achi(ev.text)
    await bot.send(im)
