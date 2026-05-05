from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .backup_data import data_backup
from ..genshinuid_map.draw_genshinmap_card import MAP_DATA

sv_data_manger = SV("数据管理", pm=2)


@scheduler.scheduled_job("cron", hour=0, minute=6)
async def daily_refresh_charData():
    await data_backup()


@sv_data_manger.on_fullmatch(
    ("清除缓存"),
    to_ai="""清除GenshinUID的缓存数据并备份数据库（管理员功能）

    当管理员说"清除缓存"、"清理缓存"时调用。
    执行数据库备份并清除地图等缓存文件。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_backup_msg(bot: Bot, ev: Event):
    await data_backup()
    for item in MAP_DATA.glob("*"):
        if item.is_file():
            item.unlink()
    await bot.send("操作成功完成!")
