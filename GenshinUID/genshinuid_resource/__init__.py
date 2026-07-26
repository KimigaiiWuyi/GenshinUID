from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.resource.download_all_resource import download_all_resource

sv_download_config = SV("gs下载资源", pm=2)


@sv_download_config.on_fullmatch(
    ("下载全部资源"),
    to_ai="""下载GenshinUID所需的全部资源文件（管理员功能）

    当管理员说"下载资源"、"更新资源"、"下载全部资源"时调用。
    下载角色、武器、圣遗物等图片资源，耗时较长。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_download_resource_msg(bot: Bot, ev: Event):
    await bot.send("正在开始下载~可能需要较久的时间!")
    im = await download_all_resource()
    await bot.send(im)


async def startup():
    logger.info(t("log.genshinuid.genshin_a81245"))
    logger.info(t("log.genshinuid.genshin_p0_0bc845", p0=await download_all_resource()))
