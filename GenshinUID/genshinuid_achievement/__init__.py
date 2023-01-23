from hoshino.typing import CQEvent, HoshinoBot

from ..base import sv, logger
from .get_achi_desc import get_achi, get_daily_achi


@sv.on_prefix('查委托')
async def send_task_info(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    if message == '':
        return

    name = str(message)
    logger.info(f'[查委托] 参数：{name}')
    im = await get_daily_achi(name)
    await bot.send(ev, im)


@sv.on_prefix('查成就')
async def send_achi_info(bot: HoshinoBot, ev: CQEvent):
    if ev.message:
        message = ev.message.extract_plain_text().replace(' ', '')
    else:
        return

    if message == '':
        return

    name = str(message)
    logger.info(f'[查成就] 参数：{name}')
    im = await get_achi(name)
    await bot.send(ev, im)
