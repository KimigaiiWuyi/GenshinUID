import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .usage_service import refresh_usage, build_usage_image
from ..utils.message import GButton as Button

sv_get_abyss_database = SV("查询深渊数据库", priority=4)
sv_hard_usage = SV("查询危战使用率", priority=4)


@scheduler.scheduled_job("interval", hours=3)
async def scheduled_refresh_usage():
    await asyncio.sleep(random.randint(0, 60))
    await refresh_usage("abyss")
    await refresh_usage("hard")


@sv_get_abyss_database.on_fullmatch(
    (
        "深渊队伍",
        "深渊概览",
        "深渊统计",
        "深渊使用率",
        "深渊队伍统计",
        "深渊队伍推荐",
        "深渊组队",
        "深渊配队",
    ),
    block=True,
    covers=["深渊怎么打", "深渊配队", "深渊使用率"],
    to_ai="""原神深渊角色与队伍使用率

    当用户说"深渊队伍"、"深渊概览"、"深渊使用率"、"深渊配队"时调用。
    同一张图：上半、下半各一栏，栏内是角色出场和热门队伍。
    这是全服统计，不是某个 UID 的成绩，也不是深渊怪物机制图。
    使用率可能滞后于当期深渊。返回文本的「状态」会写明样本窗口是否对齐。
    状态为滞后时，图上的队伍是旧期样本，要配合当期怪物和历史缓存判断。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_abyss_team_pic(bot: Bot, ev: Event):
    img = await build_usage_image("abyss")
    logger.info(t("log.genshinuid.usage_abyss_ok"))
    if isinstance(img, str):
        await bot.send(img)
        return
    await bot.send_option(img, [Button("深渊信息", "深渊信息")])


@sv_hard_usage.on_fullmatch(
    (
        "危战队伍",
        "危战概览",
        "危战统计",
        "危战使用率",
        "幽境队伍",
        "幽境概览",
    ),
    block=True,
    covers=["危战配队", "危战怎么打", "危战使用率"],
    to_ai="""原神危战角色与队伍使用率

    当用户说"危战队伍"、"危战概览"、"幽境队伍"、"危战使用率"时调用。
    同一张图：上路、中路、下路各一栏，栏内是角色出场和热门队伍。
    这是全服统计，不是某个 UID 的成绩，也不是危战怪物机制图。
    使用率可能滞后于当期危战。返回文本的「状态」会写明样本窗口是否对齐。
    状态为滞后时，图上的队伍是旧期样本，要配合当期怪物和历史缓存判断。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_hard_usage(bot: Bot, ev: Event):
    img = await build_usage_image("hard")
    logger.info(t("log.genshinuid.usage_hard_ok"))
    if isinstance(img, str):
        await bot.send(img)
        return
    await bot.send_option(img, [Button("危战信息", "危战信息")])
