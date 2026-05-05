from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .get_my_pack import draw_my_pack
from ..utils.convert import get_uid
from ..utils.message import UID_HINT

sv_pack = SV("查询背包")


@sv_pack.on_command(
    ("我的背包", "我的物品"),
    to_ai="""查询原神背包物品列表

    当用户说"我的背包"、"我的物品"、"背包里有什么"时调用。
    以图片形式返回当前UID的背包物品清单。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def my_bag(bot: Bot, ev: Event):
    uid, user_id = await get_uid(bot, ev, True)
    if not uid:
        return await bot.send(UID_HINT)

    im = await draw_my_pack(uid, ev)
    await bot.send(im)
