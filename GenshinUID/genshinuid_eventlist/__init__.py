from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.message import GButton as Button
from .draw_event_img import get_event_img, get_all_event_img
from ..utils.image.convert import convert_img

sv_event_list = SV("活动列表")


@scheduler.scheduled_job("cron", hour="2")
async def draw_event():
    await get_all_event_img()


@sv_event_list.on_fullmatch(
    "活动列表",
    to_ai="""查看原神当前正在进行的活动列表

    当用户说"活动列表"、"有什么活动"、"当前活动"时调用。
    以图片形式返回当前正在进行和即将开始的活动列表。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_events(bot: Bot, ev: Event):
    img = await get_event_img("EVENT")
    a = Button("📢原神公告列表", "原神公告")
    b = Button("💞卡池列表", "卡池列表")
    await bot.send_option(await convert_img(img), [a, b])


@sv_event_list.on_fullmatch(
    "卡池列表",
    to_ai="""查看原神当前和即将开放的卡池（祈愿）列表

    当用户说"卡池列表"、"当前卡池"、"up池"、"现在抽什么"时调用。
    以图片形式返回当前和即将开放的祈愿卡池信息。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_gachas(bot: Bot, ev: Event):
    img = await get_event_img("GACHA")
    a = Button("📢原神公告列表", "原神公告")
    b = Button("💝活动列表", "活动列表")
    await bot.send_option(await convert_img(img), [a, b])
