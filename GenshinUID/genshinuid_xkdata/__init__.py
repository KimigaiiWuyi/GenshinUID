import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler

from ..utils.image.convert import convert_img
from .draw_abyss_total import TOTAL_IMG, draw_xk_abyss_img

sv_get_abyss_database = SV('查询深渊数据库', priority=4)


@scheduler.scheduled_job('interval', hours=3)
async def scheduled_draw_abyss():
    await asyncio.sleep(random.randint(0, 60))
    await draw_xk_abyss_img()


@sv_get_abyss_database.on_fullmatch(('深渊概览', '深渊统计', '深渊使用率'), block=True)
async def send_abyss_pic(bot: Bot, ev: Event):
    img = await convert_img(TOTAL_IMG)
    await bot.logger.info('获得深渊概览图片成功!')
    await bot.send(img)
