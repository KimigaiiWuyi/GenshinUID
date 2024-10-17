import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.aps import scheduler
from gsuid_core.logger import logger

from .draw_char_abyss import draw_char_abyss_info
from .draw_teyvat_img import draw_teyvat_abyss_img

# from .draw_abyss_total import TOTAL_IMG, draw_xk_abyss_img
from .get_all_char_data import save_all_char_info, save_all_abyss_rank

sv_get_abyss_database = SV('查询深渊数据库', priority=4)


@scheduler.scheduled_job('interval', hours=3)
async def scheduled_draw_abyss():
    await asyncio.sleep(random.randint(0, 60))
    await draw_teyvat_abyss_img()


@scheduler.scheduled_job('interval', hours=11)
async def scheduled_get_xk_data():
    await asyncio.sleep(random.randint(0, 60))
    await save_all_char_info()
    await asyncio.sleep(random.randint(2, 60))
    await save_all_abyss_rank()


@sv_get_abyss_database.on_fullmatch(
    ('深渊概览', '深渊统计', '深渊使用率'), block=True
)
async def send_abyss_pic(bot: Bot, ev: Event):
    # await draw_xk_abyss_img()
    img = await draw_teyvat_abyss_img()
    # img = await convert_img(TOTAL_IMG)
    logger.info('获得深渊概览图片成功!')
    await bot.send(img)


@sv_get_abyss_database.on_prefix(('角色深渊详情', '角色深渊'), block=True)
async def send_char_abyss_pic(bot: Bot, ev: Event):
    im = await draw_char_abyss_info(ev.text)
    await bot.send(im)
