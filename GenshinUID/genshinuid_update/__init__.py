from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .draw_update_log import get_all_update_log, draw_update_log_img

sv_gs_config = SV("GS管理", pm=1)
sv_update_history = SV("Core更新记录")


@sv_update_history.on_fullmatch(
    ("更新记录"),
    to_ai="""查看GenshinUID插件的更新记录

    当用户说"更新记录"、"更新日志"、"最近更新了什么"时调用。
    以图片形式返回插件的版本更新历史。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_updatelog_msg(bot: Bot, ev: Event):
    await bot.logger.info("正在执行[更新记录]...")
    im = await draw_update_log_img(is_update=False)
    await bot.send(im)


@sv_gs_config.on_fullmatch(
    ("gs更新", "gs强制更新", "gs强行强制更新", "gs全部更新"),
    to_ai="""执行GenshinUID插件更新（管理员功能）

    当管理员说"gs更新"、"gs强制更新"时调用。
    支持不同更新等级：普通更新、强制更新、强行强制更新、全部更新。

    Args:
        text: 无需参数，留空即可。更新等级由命令本身决定：
              - "gs更新"：普通更新
              - "gs强制更新"：强制更新
              - "gs强行强制更新"：强行强制更新
              - "gs全部更新"：查看全部更新日志
    """,
)
async def send_update_msg(bot: Bot, ev: Event):
    await bot.logger.info("[gs更新] 正在执行 ...")
    level = 2
    if "全部" in ev.command:
        im = await get_all_update_log()
        return await bot.send(MessageSegment.node(im))
    if "强制" not in ev.command:
        level -= 1
    if "强行" not in ev.command:
        level -= 1
    await bot.logger.info(f"[gs更新] 更新等级为{level}")
    await bot.send(f"开始执行[gs更新], 执行等级为{level}")

    im = await draw_update_log_img(level)
    await bot.send(im)
