import asyncio

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.ai_core.trigger_bridge import ai_return

from .get_mys_data import get_region_task, get_task_detail
from .get_lots_data import get_lots_msg
from .get_meme_card import get_meme_img

sv_find_task = SV("查询游戏攻略")
sv_fun = SV("娱乐功能")


@sv_find_task.on_prefix(
    ("原神任务", "任务详情", "qszh"),
    to_ai="""查询原神任务详情或区域任务列表

    当用户说"原神任务 须弥"、"任务详情 某某任务"时调用。
    输入区域名返回该区域任务列表，输入任务名返回任务详情。

    Args:
        text: 区域名或任务名称
              - 区域名（返回任务列表）："须弥"、"层岩"、"海岛"
              - 任务名称（返回任务详情）：具体的任务名
    """,
)
async def send_task_adv(bot: Bot, ev: Event):
    if ev.text in ["须弥", "层岩", "海岛"]:
        im = await get_region_task(ev.text)
        for i in im:
            mes = [MessageSegment.text(_msg) for _msg in i]
            await bot.send(MessageSegment.node(mes))
            await asyncio.sleep(1)
        return
    else:
        im = await get_task_detail(ev.text)
        if isinstance(im, str):
            ai_return(im)
        await bot.send(im)


@sv_fun.on_fullmatch(
    ("抽表情"),
    to_ai="""随机抽取一个原神表情包

    当用户说"抽表情"、"来个表情"、"给我表情包"时调用。
    随机返回一张原神表情包图片。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_meme_card(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[抽表情]")
    await bot.send(await get_meme_img())


@sv_fun.on_fullmatch(
    ("御神签"),
    to_ai="""抽取今日原神御神签（每日运势）

    当用户说"御神签"、"今日运势"、"抽签"时调用。
    根据用户ID和日期生成今日运势结果。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_lots_data(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[御神签]")
    result = await get_lots_msg(ev.user_id)
    if isinstance(result, str):
        ai_return(result)
    await bot.send(result)
