import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .draw_char_abyss import draw_char_abyss_info
from .draw_teyvat_img import draw_teyvat_team_img, draw_teyvat_abyss_img

# from .draw_abyss_total import TOTAL_IMG, draw_xk_abyss_img
from .get_all_char_data import save_all_char_info, save_all_abyss_rank

sv_get_abyss_database = SV("查询深渊数据库", priority=4)


@scheduler.scheduled_job("interval", hours=3)
async def scheduled_draw_abyss():
    await asyncio.sleep(random.randint(0, 60))
    await draw_teyvat_abyss_img()


@scheduler.scheduled_job("interval", hours=11)
async def scheduled_get_xk_data():
    await asyncio.sleep(random.randint(0, 60))
    await save_all_char_info()
    await asyncio.sleep(random.randint(2, 60))
    await save_all_abyss_rank()


@sv_get_abyss_database.on_fullmatch(
    ("深渊概览", "深渊统计", "深渊使用率"),
    block=True,
    to_ai="""查看当前深渊的角色使用率概览统计图

    当用户说"深渊概览"、"深渊统计"、"深渊使用率"时调用。
    以图片形式返回当前版本深渊各角色的使用率和出场率统计。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_abyss_pic(bot: Bot, ev: Event):
    img = await draw_teyvat_abyss_img()
    logger.info(t("log.genshinuid.msg_4fdad0"))
    await bot.send(img)


@sv_get_abyss_database.on_fullmatch(
    ("深渊队伍", "深渊队伍统计", "深渊队伍推荐", "深渊组队", "深渊配队"),
    block=True,
    to_ai="""查看当前深渊的队伍推荐和组队统计图

    当用户说"深渊队伍"、"深渊配队"、"深渊组队推荐"时调用。
    以图片形式返回当前版本深渊的热门队伍搭配和使用率。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_abyss_team_pic(bot: Bot, ev: Event):
    img = await draw_teyvat_team_img()
    logger.info(t("log.genshinuid.msg_bdd204"))
    await bot.send(img)


@sv_get_abyss_database.on_prefix(
    ("角色深渊详情", "角色深渊"),
    block=True,
    to_ai="""查看指定角色的深渊使用详情数据

    当用户说"角色深渊详情 甘雨"、"角色深渊 胡桃"时调用。
    以图片形式返回该角色在深渊中的详细使用数据。

    Args:
        text: 角色名称，例如 "甘雨"、"胡桃"、"雷电将军"
              支持角色昵称，例如 "雷神"、"小草神"
    """,
)
async def send_char_abyss_pic(bot: Bot, ev: Event):
    im = await draw_char_abyss_info(ev.text)
    await bot.send(im)
