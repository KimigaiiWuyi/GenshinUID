from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_season_post import get_season_post_draw

sv_seasonpost = SV("原神季报")


@sv_seasonpost.on_fullmatch(
    ("季报"),
    to_ai="""查询原神季度报告

    当用户说"季报"、"季度报告"时调用。
    以图片形式返回本季度的游戏数据统计报告。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_seasonpost(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_a5cebe"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_10c7fc", uid=uid))

    img = await get_season_post_draw(uid, ev)
    return await bot.send(img)
