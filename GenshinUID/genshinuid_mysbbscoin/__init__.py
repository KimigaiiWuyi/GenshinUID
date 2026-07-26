import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind, GsUser

from .daily_get import mihoyo_coin, all_daily_mihoyo_bbs_coin
from ..utils.message import UID_HINT
from ..genshinuid_config.gs_config import gsconfig

BBS_TASK_TIME = gsconfig.get_config("BBSTaskTime").data

sv_mysbbs_config = SV("米游币获取管理", pm=2)
sv_get_mysbbs = SV("米游币获取")


# 获取米游币
@sv_get_mysbbs.on_fullmatch(
    "开始获取米游币",
    to_ai="""自动获取米游币

    当用户说"获取米游币"、"开始获取米游币"时调用。
    需要用户已绑定原神UID和stoken。操作结果以文字形式返回。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_mihoyo_coin(bot: Bot, ev: Event):
    await bot.send("开始操作……")
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    stoken = await GsUser.get_user_stoken_by_uid(uid)
    if stoken is None:
        return await bot.send(
            f"🔔 提示：你的当前UID{uid}暂未绑定Stoken~\n"
            f"📎 请使用扫码登陆命令获取Stoken\n"
            f"🚩 或者查看帮助文档获取绑定方式"
        )
    im = await mihoyo_coin(stoken)
    await bot.send(im)


@sv_mysbbs_config.on_fullmatch(
    "全部重获取",
    to_ai="""重新获取所有用户的米游币（管理员功能）

    当管理员说"全部重获取"、"重新获取米游币"时调用。
    为所有已绑定stoken的用户重新执行米游币获取，耗时较长。

    Args:
        text: 无需参数，留空即可
    """,
)
async def bbs_recheck(bot: Bot, ev: Event):
    await bot.send("已开始执行!可能需要较久时间!")
    await send_daily_mihoyo_bbs_sign()
    await bot.send("执行完成!")


# 每日一点十六分进行米游币获取
@scheduler.scheduled_job("cron", hour=BBS_TASK_TIME[0], minute=BBS_TASK_TIME[1])
async def get_coin_at_night():
    if gsconfig.get_config("SchedMhyBBSCoin").data:
        await asyncio.sleep(random.randint(2, 60))
        await send_daily_mihoyo_bbs_sign()


async def send_daily_mihoyo_bbs_sign():
    await all_daily_mihoyo_bbs_coin()
    logger.info(t("log.genshinuid.msg_e592d3"))
