from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .data_source import get_code_msg

sv_gs_code = SV("原神前瞻兑换码")


@sv_gs_code.on_fullmatch(
    "兑换码",
    to_ai="""获取原神最新前瞻直播兑换码

    当用户说"兑换码"、"前瞻兑换码"、"直播兑换码"时调用。
    返回当前可用的前瞻直播兑换码列表。

    Args:
        text: 无需参数，留空即可
    """,
)
async def get_sign_func(bot: Bot, ev: Event):
    try:
        codes = await get_code_msg()
    except Exception:
        logger.exception(t("log.genshinuid.code_fetch_fail"))
        codes = "获取前瞻兑换码失败"
    await bot.send(codes)
