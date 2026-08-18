import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from ..utils.convert import get_uid
from ..utils.message import UID_HINT, GButton as Button
from .draw_abyss_card import draw_abyss_img

sv_abyss = SV("查询深渊")

__all__ = ["ai_return"]


@sv_abyss.on_command(
    ("查询深渊", "sy", "查询上期深渊", "sqsy", "上期深渊", "深渊"),
    block=True,
    to_ai="""查询原神深渊战斗信息

    当用户说"查询深渊"、"深渊12"、"上期深渊"、"深渊战绩"时调用。
    以图片形式返回深渊各层战斗详情。需要用户已绑定UID。

    Args:
        text: 可选参数，格式为 "[上期] [层数]"
              - "上期"/"sq"前缀：查询上期深渊，例如 "上期12"、"sq12"
              - 层数：9/10/11/12 或中文数字，例如 "12"、"十一"
              - 留空：显示当前期全部层数概览
    """,
)
async def send_abyss_info(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    if name:
        return

    await bot.logger.info(t("log.genshinuid.abyss_query_start"))
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info(t("log.genshinuid.abyss_query_uid", uid=uid))

    if "sq" in ev.command or "上期" in ev.command:
        schedule_type = "2"
    else:
        schedule_type = "1"
    await bot.logger.info(t("log.genshinuid.abyss_query_schedule", schedule_type=schedule_type))

    if ev.text in ["九", "十", "十一", "十二"]:
        floor = ev.text.replace("九", "9").replace("十一", "11").replace("十二", "12").replace("十", "10")
    else:
        floor = ev.text
    if floor and floor.isdigit():
        floor = int(floor)
    else:
        floor = None

    await bot.logger.info(t("log.genshinuid.abyss_query_floor", floor=floor))

    im = await draw_abyss_img(ev, uid, floor, schedule_type)
    a = Button("🔍查询深渊11", "查询深渊11")
    b = Button("🔚查询上期深渊", "查询上期深渊")
    c = Button("♾️深渊概览", "深渊概览")
    d = Button("👾怪物阵容", "版本深渊")
    await bot.send_option(im, [a, b, c, d])
