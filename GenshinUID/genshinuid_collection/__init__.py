from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT, GButton as Button
from .draw_collection_card import draw_explora_img, draw_collection_img
from .draw_new_collection_card import draw_explore

sv_cp = SV("查询完成度")
sv_sj = SV("查询收集")
sv_ts = SV("查询探索")


@sv_cp.on_command(
    ("查询完成度", "wcd"),
    block=True,
    to_ai="""查询原神世界探索完成度总览

    当用户说"查询完成度"、"wcd"、"探索进度"时调用。
    以图片形式返回各区域探索完成度总览。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_cp_info(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[查询完成度信息]")

    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info("[查询角色面板]uid: {}".format(uid))

    im = await draw_explore(uid)
    a = Button("🔍查询探索", "查询探索")
    b = Button("🔍查询收集", "查询收集")
    await bot.send_option(im, [a, b])


@sv_sj.on_command(
    ("查询收集", "sj", "收集"),
    block=True,
    to_ai="""查询原神收集物详情（神瞳、宝箱等）

    当用户说"查询收集"、"sj"、"神瞳收集"时调用。
    以图片形式返回神瞳、宝箱等收集物的收集进度。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_collection_info(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[查询收集信息]")

    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info("[查询角色面板]uid: {}".format(uid))

    im = await draw_collection_img(ev, uid)
    a = Button("🔍查询探索", "查询探索")
    b = Button("🔍查询收集", "查询收集")
    await bot.send_option(im, [a, b])


@sv_ts.on_command(
    ("查询探索", "ts"),
    block=True,
    to_ai="""查询原神各区域探索度详情

    当用户说"查询探索"、"ts"、"区域探索"时调用。
    以图片形式返回各区域的探索度百分比。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_explora_info(bot: Bot, ev: Event):
    await bot.logger.info("开始执行[查询探索信息]")

    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info("[查询角色面板]uid: {}".format(uid))

    im = await draw_explora_img(ev, uid)
    a = Button("🔍查询探索", "查询探索")
    b = Button("🔍查询收集", "查询收集")
    await bot.send_option(im, [a, b])
