from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event

from .notice_cale import notice_cale
from .draw_cale_pic import draw_cale_img
from ..utils.buttons import a, b, c, s, t as btn_t, u, v, x, y
from ..utils.convert import get_uid
from ..utils.message import UID_HINT

sv_cale = SV("个人日历")


@sv_cale.on_command(
    ("个人日历", "日历", "查询个人日历", "查询日历"),
    block=True,
    to_ai="""查询原神个人日历（个人活动完成状态）

    当用户说"个人日历"、"日历"、"活动完成状态"时调用。
    以图片形式返回当前卡池/活动/深渊的完成情况。
    需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_cale_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_6e0c45", uid=uid))

    im = await draw_cale_img(ev, uid)
    await bot.send_option(im, [[a, b, c], [btn_t, s, u], [v, x, y]])


@scheduler.scheduled_job("cron", hour="0", minute="5")
async def notice_cale_job(force: bool = False):
    await notice_cale()
