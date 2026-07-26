from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from .notice import send_notice_list
from .resin_text import get_resin_text
from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_resin_card import get_resin_img
from ..genshinuid_config.gs_config import gsconfig

sv_get_resin = SV("查询体力")
sv_get_resin_admin = SV("强制推送", pm=1)

is_check_resin = gsconfig.get_config("SchedResinPush").data

__all__ = ["ai_return"]


@sv_get_resin.on_fullmatch(
    ("当前状态"),
    to_ai="""以文字形式查询原神当前状态（树脂、宝钱、派遣等）

    当用户说"当前状态"、"体力多少"、"树脂满了没"时调用。
    以文字形式返回树脂、洞天宝钱、派遣、参量质变仪等状态。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_daily_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_fd95a1"))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info("[每日信息文字版]UID: {}".format(uid))

    im = await get_resin_text(uid)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_get_resin_admin.on_fullmatch(
    ("强制推送体力提醒"),
    to_ai="""强制执行一次体力提醒推送（管理员功能）

    当管理员说"强制推送体力提醒"时调用。
    立即检查所有用户的体力状态并推送提醒。

    Args:
        text: 无需参数，留空即可
    """,
)
async def force_notice_job(bot: Bot, ev: Event):
    await bot.send("🔨 [原神服务]\n🌱 开始执行强制推送体力提醒!")
    await notice_job(True)
    await bot.send("🔨 [原神服务]\n✅ 强制推送体力提醒执行完成!")


@scheduler.scheduled_job("cron", minute="*/30")
async def notice_job(force: bool = False):
    if is_check_resin or force:
        await send_notice_list()
    else:
        logger.info(t("log.genshinuid.msg_5887e9"))


@sv_get_resin.on_fullmatch(
    ("每日", "mr", "实时便笺", "便笺", "便签"),
    to_ai="""以图片形式查询原神实时便笺信息

    当用户说"每日"、"mr"、"实时便笺"、"便签"时调用。
    以图片形式返回树脂、洞天宝钱、派遣、参量质变仪等实时信息。需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_daily_info_pic(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_2f9be3"))
    user_id = ev.at if ev.at else ev.user_id
    logger.info("[每日信息]QQ号: {}".format(user_id))

    im = await get_resin_img(bot.bot_id, user_id)
    await bot.send(im)
