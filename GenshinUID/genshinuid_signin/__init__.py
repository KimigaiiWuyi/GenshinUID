from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.utils.sign.sign import sign_in
from gsuid_core.utils.database.models import GsBind

from ..utils.message import UID_HINT
from ..genshinuid_config.gs_config import gsconfig

SIGN_TIME = gsconfig.get_config("SignTime").data
IS_REPORT_PRIVATE = gsconfig.get_config("PrivateSignReport").data
IS_REPORT_GROUP = gsconfig.get_config("GroupSignReport").data

sv_sign = SV("原神签到")
sv_sign_config = SV("原神签到管理", pm=2)


# 每日零点半执行米游社原神签到
@scheduler.scheduled_job("cron", hour=SIGN_TIME[0], minute=SIGN_TIME[1])
async def sign_at_night():
    if gsconfig.get_config("SchedSignin").data:
        await send_daily_sign()


# 群聊内 签到 功能
@sv_sign.on_fullmatch(
    "签到",
    to_ai="""执行米游社原神每日签到

    当用户说"签到"、"我要签到"、"领取签到奖励"时调用。
    需要用户已绑定原神UID。签到结果以文字形式返回。

    Args:
        text: 无需参数，留空即可
    """,
)
async def get_sign_func(bot: Bot, ev: Event):
    logger.info("[原神] [签到]QQ号: {}".format(ev.user_id))
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    logger.info(t("log.genshinuid.uid_uid_93d17b", uid=uid))
    await bot.send(await sign_in(uid, "gs"))


@sv_sign_config.on_fullmatch(
    "全部重签",
    to_ai="""重新执行所有用户的米游社签到（管理员功能）

    当管理员说"全部重签"、"重新签到"时调用。
    将为所有已绑定用户重新执行米游社签到，耗时较长。

    Args:
        text: 无需参数，留空即可
    """,
)
async def recheck(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_145d21"))
    await bot.send("🚩 [原神] [全部重签] 已开始执行...")
    await send_daily_sign()
    await bot.send("🚩 [原神] [全部重签] 执行完成！")


async def send_daily_sign():
    logger.info(t("log.genshinuid.msg_cf4ab9"))
    # 执行签到 并获得推送消息
    datas = await gs_subscribe.get_subscribe("[原神] 自动签到")
    priv_result, group_result = await gs_subscribe.muti_task(datas, sign_in, "uid")

    if IS_REPORT_PRIVATE:
        for _, data in priv_result.items():
            im = "\n".join(data["im"])
            event = data["event"]
            await event.send(im)

    if IS_REPORT_GROUP:
        for _, data in group_result.items():
            im = "✅ 原神今日自动签到已完成！\n"
            im += f"📝 本群共签到成功{data['success']}人，共签到失败{data['fail']}人。"
            event = data["event"]
            await event.send(im)

    logger.info(t("log.genshinuid.msg_948500"))
