from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .draw_gcgdesk import draw_deck_img
from .draw_gcginfo import draw_gcg_info
from ..utils.convert import get_uid
from ..utils.message import UID_HINT, GButton as Button

sv_gcg = SV("查询七圣")


@sv_gcg.on_command(
    ("七圣召唤", "qszh", "七圣数据总览"),
    to_ai="""查询原神七圣召唤数据总览

    当用户说"七圣召唤"、"七圣数据总览"时调用。
    以图片形式返回七圣召唤的对局统计、胜率等数据。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_gcg_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_516c34", uid=uid))

    im = await draw_gcg_info(uid)
    await bot.send_option(im, [Button("✅我的卡组", "我的卡组")])


@sv_gcg.on_command(
    ("我的卡组", "我的牌组"),
    to_ai="""查询原神七圣召唤卡组详情

    当用户说"我的卡组"、"我的牌组"时调用。
    以图片形式返回指定卡组的卡牌配置详情。需要用户已绑定UID。

    Args:
        text: 可选的卡组序号数字，默认为1，例如 "1"、"2"、"3"
    """,
)
async def send_deck_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_b2c5dd", uid=uid))
    if not ev.text:
        deck_id = 1
    elif ev.text.strip().isdigit():
        deck_id = int(ev.text.strip())
    else:
        return bot.send("请输入正确的序号, 例如我的卡组1...")
    im = await draw_deck_img(ev, uid, deck_id)
    await bot.send_option(im, [Button("✅七圣数据总览", "七圣召唤")])
