import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_hard_rank import draw_hard_rank
from .draw_hard_challenge import draw_hard_challenge_img

sv_hard_abyss = SV("查询幽境危战")
sv_hard_abyss_rank = SV("查询幽境危战排行榜", priority=2)


@sv_hard_abyss.on_command(
    (
        "查询幽境危战",
        "幽境危战",
        "肃靖险乱",
        "新新深渊",
        "三路深渊",
        "yjwz",
    ),
    block=True,
    to_ai="""查询原神幽境危战（三路深渊）战斗信息

    当用户说"幽境危战"、"新新深渊"、"三路深渊"时调用。
    以图片形式返回幽境危战的战斗详情。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_hard_abyss_info(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    if name:
        return

    logger.info(t("log.genshinuid.msg_4cb1d0"))
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info("[幽境危战] uid: {}".format(uid))

    im = await draw_hard_challenge_img(uid, ev)

    await bot.send(im)


@sv_hard_abyss_rank.on_fullmatch(
    (
        "幽境危战排行榜",
        "幽境排行榜",
        "新新深渊排行榜",
    ),
    block=True,
    to_ai="""查看原神幽境危战（三路深渊）的排行榜数据

    当用户说"幽境危战排行榜"、"幽境排行榜"时调用。
    以图片形式返回幽境危战的全服排行榜数据。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_hard_abyss_rank_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_5279ac"))
    im = await draw_hard_rank()
    logger.info(t("log.genshinuid.msg_a641c7"))

    await bot.send(im)
