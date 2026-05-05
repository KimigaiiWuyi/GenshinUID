from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind

from .note_text import award
from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_note_card import draw_note_img

sv_get_monthly_data = SV("查询札记")


# 群聊内 每月统计 功能
@sv_get_monthly_data.on_fullmatch(
    ("每月统计"),
    to_ai="""查询原神本月原石和莫拉收入统计

    当用户说"每月统计"、"本月收入"、"这个月赚了多少原石"时调用。
    以文字形式返回本月的原石和莫拉获取统计。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_monthly_data(bot: Bot, ev: Event):
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return UID_HINT
    await bot.send(await award(uid))


@sv_get_monthly_data.on_fullmatch(
    ("当前信息", "zj", "札记"),
    to_ai="""查询原神当前实时便笺信息

    当用户说"当前信息"、"札记"、"zj"时调用。
    以图片形式返回树脂、洞天宝钱、派遣等实时便笺信息。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_monthly_pic(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[每日信息]")
    uid = await get_uid(bot, ev)
    if uid is None:
        return UID_HINT
    im = await draw_note_img(str(uid), ev)
    await bot.send(im)
