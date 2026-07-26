from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.database.models import GsBind

from .lelaer_tools import (
    get_gachaurl,
    get_lelaer_gachalog,
    export_gachalog_to_lelaer,
)
from .get_gachalogs import save_gachalogs, get_full_gachalog
from ..utils.convert import get_uid
from ..utils.message import UID_HINT, GButton as Button
from .draw_gachalogs import draw_gachalogs_img
from .export_and_import import export_gachalogs, import_gachalogs

sv_gacha_log = SV("抽卡记录")
sv_refresh_gacha_log = SV("刷新抽卡记录")
sv_export_gacha_log = SV("导出抽卡记录")
sv_import_gacha_log = SV("导入抽卡记录", area="DIRECT")
sv_import_lelaer_gachalog = SV("从小助手导入抽卡记录")
sv_export_lelaer_gachalog = SV("导出抽卡记录到小助手")
sv_export_gachalogurl = SV("导出抽卡记录链接", area="DIRECT")


@sv_import_gacha_log.on_file("json")
async def send_import_gacha_info(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    if ev.file and ev.file_type:
        await bot.send("正在尝试导入抽卡记录中，请耐心等待……")
        return await bot.send(await import_gachalogs(ev.file, ev.file_type, uid))
    else:
        return await bot.send("导入抽卡记录异常...")


@sv_gacha_log.on_fullmatch(
    ("抽卡记录"),
    to_ai="""查看原神抽卡记录

    当用户说"抽卡记录"、"抽卡历史"、"看看我抽了什么"时调用。
    以图片形式返回抽卡记录统计（各卡池抽数、出货情况等）。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_gacha_log_card_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_19ef2d"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_gachalogs_img(uid, ev)
    a = Button("🔁刷新抽卡记录", "刷新抽卡记录")
    b = Button("🔜导出抽卡记录至提瓦特小助手", "导出抽卡记录到小助手")
    c = Button("🔙从提瓦特小助手导入抽卡记录", "从小助手导入抽卡记录")
    await bot.send_option(im, [[a], [b], [c]])


@sv_refresh_gacha_log.on_fullmatch(
    ("刷新抽卡记录", "强制刷新抽卡记录"),
    to_ai="""刷新原神抽卡记录数据

    当用户说"刷新抽卡记录"、"强制刷新抽卡记录"时调用。
    从米游社API重新获取抽卡记录。加"强制"前缀可强制刷新。

    Args:
        text: 无需参数，留空即可。是否强制由命令本身决定
    """,
)
async def send_refresh_gacha_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_0cebbe"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    is_force = False
    if ev.command.startswith("强制"):
        await bot.logger.info("[WARNING]本次为强制刷新")
        is_force = True
    await bot.send(f"UID{uid}开始执行[刷新抽卡记录],需要一定时间...请勿重复触发！")
    im = await save_gachalogs(uid, None, is_force)
    await bot.send_option(im, [Button("🃏抽卡记录", "抽卡记录")])


@sv_refresh_gacha_log.on_fullmatch(
    ("全量刷新抽卡记录"),
    to_ai="""全量刷新原神抽卡记录（从头获取所有记录）

    当用户说"全量刷新抽卡记录"时调用。
    从头获取所有历史抽卡记录，耗时较长。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_full_refresh_gacha_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_30ab91"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.send(f"UID{uid}开始执行[全量刷新抽卡记录],需要一定时间...请勿重复触发！")
    im = await get_full_gachalog(uid)
    return await bot.send_option(im, [Button("🃏抽卡记录", "抽卡记录")])


@sv_export_gacha_log.on_fullmatch(
    ("导出抽卡记录"),
    to_ai="""导出原神抽卡记录为UIGF格式文件

    当用户说"导出抽卡记录"时调用。
    将抽卡记录导出为标准UIGF格式JSON文件，支持v2和v4版本。

    Args:
        text: 无需参数，留空即可。系统会询问导出版本
    """,
)
async def send_export_gacha_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_e68303"))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)

    resp = await bot.receive_resp(
        "❓请问你要导出哪个版本的UIGF文件？\n➡可选：v2、v4",
    )

    version = "2"
    if resp is not None:
        msg = resp.text.strip()
        if msg in ["v2", "v4", "2", "4"]:
            version = msg.replace("v", "")
        else:
            return await bot.send("❌请输入正确的版本号噢！(可选：v2、v4)\n本次导出终止...")
    await bot.send(f"🔜即将为你导出UIGFv{version}文件，请耐心等待...")

    export = await export_gachalogs(uid, version)
    if export["retcode"] == "ok":
        file_name = export["name"]
        file_path = export["url"]
        await bot.send(MessageSegment.file(file_path, file_name))
        await bot.send(f"✅导出UIGFv{version}文件成功！")
    else:
        await bot.send("导出抽卡记录失败...")


@sv_import_lelaer_gachalog.on_fullmatch(
    ("从小助手导入抽卡记录"),
    to_ai="""从提瓦特小助手导入抽卡记录

    当用户说"从小助手导入抽卡记录"时调用。
    从提瓦特小助手平台导入抽卡记录到当前系统。

    Args:
        text: 无需参数，留空即可
    """,
)
async def import_lelaer_gachalog(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_91067a"))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await get_lelaer_gachalog(uid)
    await bot.send(im)


@sv_export_lelaer_gachalog.on_fullmatch(
    ("导出抽卡记录到小助手"),
    to_ai="""将抽卡记录导出到提瓦特小助手

    当用户说"导出抽卡记录到小助手"时调用。
    将当前系统的抽卡记录同步导出到提瓦特小助手平台。

    Args:
        text: 无需参数，留空即可
    """,
)
async def export_to_lelaer_gachalog(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_2b884e"))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await export_gachalog_to_lelaer(uid)
    await bot.send(im)


@sv_export_gachalogurl.on_fullmatch(
    ("导出抽卡记录链接", "导出抽卡记录连接"),
    to_ai="""获取原神抽卡记录的导出链接

    当用户说"导出抽卡记录链接"、"导出抽卡记录连接"时调用。
    生成一个可分享的抽卡记录导出链接。

    Args:
        text: 无需参数，留空即可
    """,
)
async def export_gachalogurl(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_11ac61"))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await get_gachaurl(uid)
    if isinstance(im, bytes):
        return await bot.send(im)
    if isinstance(im, (bytearray, memoryview)):
        return await bot.send(bytes(im))
    await bot.send(MessageSegment.node([MessageSegment.text(im)]))
