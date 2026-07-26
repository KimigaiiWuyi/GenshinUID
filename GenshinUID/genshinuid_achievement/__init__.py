from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from .draw_achi import draw_achi_img
from .get_achi_desc import get_achi, get_daily_achi
from ..utils.convert import get_uid
from ..utils.message import UID_HINT

sv_task_achi = SV("成就委托查询")
sv_achi_search = SV("成就完成查询")


@sv_achi_search.on_command(
    ("我的成就", "成就列表", "成就一览"),
    to_ai="""查询原神成就完成情况

    当用户说"我的成就"、"成就列表"、"成就一览"时调用。
    以图片形式返回成就完成进度。需要用户已绑定UID。

    Args:
        text: 可选的筛选关键词，留空显示全部成就
              例如 ""（全部）、"天地万象"（按系列筛选）
    """,
)
async def send_achi_img(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.p0_11ddc2", p0=ev.text))
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_achi_img(ev, uid)
    await bot.send(im)


@sv_task_achi.on_prefix(
    "查委托",
    to_ai="""查询原神每日委托完成情况

    当用户说"查委托 今日"、"查委托 昨日"时调用。
    返回指定日期的每日委托完成详情。

    Args:
        text: 日期或关键词，例如 "今日"、"昨日"、"前日"
    """,
)
async def send_task_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.p0_55baa5", p0=ev.text))
    im = await get_daily_achi(ev.text)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)


@sv_task_achi.on_prefix(
    "查成就",
    to_ai="""根据关键词搜索原神成就信息

    当用户说"查成就 天地万象"、"查成就 宝箱"时调用。
    根据关键词模糊搜索成就并返回详情。

    Args:
        text: 成就名称或关键词，例如 "天地万象"、"宝箱"、"击败"
    """,
)
async def send_achi_info(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.p0_41dd2b", p0=ev.text))
    im = await get_achi(ev.text)
    if isinstance(im, str):
        ai_return(im)
    await bot.send(im)
