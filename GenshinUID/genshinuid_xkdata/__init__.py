import random
import asyncio
import threading

from ..base import sv, logger
from .draw_abyss_total import TOTAL_IMG, draw_xk_abyss_img
from ..utils.draw_image_tools.send_image_tool import convert_img


@sv.scheduled_job('interval', hours=3)
async def scheduled_draw_abyss():
    await asyncio.sleep(random.randint(0, 60))
    await draw_xk_abyss_img()


@sv.on_fullmatch(('深渊概览', '深渊统计', '深渊使用率'))
async def send_abyss_pic(bot, ev):
    img = await convert_img(TOTAL_IMG)
    logger.info('获得gs帮助图片成功！')
    await bot.send(ev, img)


threading.Thread(
    target=lambda: asyncio.run(draw_xk_abyss_img()), daemon=True
).start()
