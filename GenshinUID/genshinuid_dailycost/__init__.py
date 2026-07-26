from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .draw_daily_cost import draw_daily_cost_img

sv_daily_cost = SV("查询每日材料")


@sv_daily_cost.on_command(
    ("每日材料", "今日材料", "每日素材", "今日素材"),
    block=True,
    to_ai="""查看今日原神角色和武器突破所需材料

    当用户说"每日材料"、"今日材料"、"今天刷什么"时调用。
    以图片形式返回今天可刷的突破材料及对应角色/武器。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_collection_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_cffadd"))
    im = await draw_daily_cost_img()
    await bot.send(im)


# 每日四点出头执行刷新材料图
@scheduler.scheduled_job("cron", hour=4, minute=1)
async def refresh_daily_cost():
    await draw_daily_cost_img(True)
