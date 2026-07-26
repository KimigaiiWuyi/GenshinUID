from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.help.utils import register_help

from .get_help import get_core_help
from ..utils.image.image_tools import get_ICON

PREFIX = get_plugin_available_prefix("GenshinUID")

sv_gs_help = SV("gs帮助")


@sv_gs_help.on_fullmatch(
    ("帮助"),
    to_ai="""获取GenshinUID插件的帮助信息和功能列表

    当用户说"帮助"、"有什么功能"、"怎么使用"时调用。
    以图片形式返回插件的完整功能列表和使用说明。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_help_img(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.gs_bf50ca"))
    im = await get_core_help()
    await bot.send(im)


register_help("GenshinUID", f"{PREFIX}帮助", get_ICON())
