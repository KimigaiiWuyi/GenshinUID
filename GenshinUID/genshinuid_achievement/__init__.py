from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .get_achi_desc import get_achi, get_daily_achi


@SV('成就委托查询').on_prefix('查委托')
async def send_task_info(bot: Bot, ev: Event):
    await bot.logger.info(f'[查委托] 参数：{ev.text}')
    im = await get_daily_achi(ev.text)
    await bot.send(im)


@SV('成就委托查询').on_prefix('查成就')
async def send_achi_info(bot: Bot, ev: Event):
    await bot.logger.info(f'[查成就] 参数：{ev.text}')
    im = await get_achi(ev.text)
    await bot.send(im)
