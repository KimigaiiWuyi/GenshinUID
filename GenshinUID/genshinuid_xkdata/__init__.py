import random
import asyncio
import threading

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot_plugin_apscheduler import scheduler
from nonebot.adapters.onebot.v11 import MessageSegment

from .draw_abyss_total import TOTAL_IMG, draw_xk_abyss_img
from ..utils.exception.handle_exception import handle_exception

draw_total_scheduler = scheduler
get_abyss_total = on_command('深渊概览', aliases={'深渊统计', '深渊使用率'})


@draw_total_scheduler.scheduled_job('interval', hours=3)
async def scheduled_draw_abyss():
    await asyncio.sleep(random.randint(0, 60))
    await draw_xk_abyss_img()


@get_abyss_total.handle()
@handle_exception('深渊概览')
async def send_guide_pic(matcher: Matcher):
    if TOTAL_IMG.exists():
        logger.info('获得深渊概览成功！')
        with open(TOTAL_IMG, 'rb') as f:
            await matcher.finish(MessageSegment.image(f.read()))
    else:
        await matcher.finish('深渊概览图不存在!')


threading.Thread(
    target=lambda: asyncio.run(draw_xk_abyss_img()), daemon=True
).start()
