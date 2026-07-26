import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from .get_regtime import calc_reg_time
from .draw_all_char import draw_char_pic
from ..utils.buttons import a, b, c, s, t as btn_t, u, v, x, y
from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_roleinfo_card import draw_pic

sv_get_regtime = SV("查询注册时间")
sv_get_info = SV("查询原神信息")

__all__ = ["ai_return"]


@sv_get_regtime.on_command(
    ("原神注册时间", "注册时间", "查询注册时间"),
    block=True,
    to_ai="""查询原神账号注册时间

    当用户说"注册时间"、"什么时候开始玩"、"查询注册时间"时调用。
    以文字形式返回账号注册日期和游玩天数。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def regtime(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_7db258"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_3c0770", uid=uid))

    im = await calc_reg_time(uid)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_get_info.on_command(
    ("查询", "uid", "UID"),
    to_ai="""查询原神角色信息面板

    当用户说"查询"、"uid"时调用。
    以图片形式返回当前UID的角色信息面板。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可。查询特定角色请使用"查询 角色名"命令
    """,
)
async def send_role_info(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    if name:
        return
    logger.info(t("log.genshinuid.msg_ca4978"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_f71cbf", uid=uid))

    im = await draw_pic(ev, uid)
    await bot.send_option(im, [[a, b, c], [btn_t, s, u], [v, x, y]])


@sv_get_info.on_command(
    ("角色列表"),
    to_ai="""查询原神全部角色列表

    当用户说"角色列表"、"有哪些角色"、"我有哪些角色"时调用。
    以图片形式返回当前UID拥有的全部角色列表。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_charlist_info(bot: Bot, ev: Event):
    name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text))
    if name:
        return
    logger.info(t("log.genshinuid.msg_1a09e7"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_26a2eb", uid=uid))

    im = await draw_char_pic(uid)
    await bot.send_option(im, [[a, b, c], [btn_t, s, u], [v, x, y]])
