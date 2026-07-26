from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_char_count import draw_char_count_list

sv_get_count = SV("毕业度统计")


@sv_get_count.on_command(
    ("毕业度统计", "毕业都统计", "练度统计"),
    to_ai="""查询原神角色毕业度和练度统计

    当用户说"毕业度统计"、"练度统计"时调用。
    以图片形式返回各角色的毕业度/练度评分。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_charcard_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_char_count_list(str(uid), ev)
    logger.info(t("log.genshinuid.uid_uid_8bbaae", uid=uid))
    await bot.send(im)
