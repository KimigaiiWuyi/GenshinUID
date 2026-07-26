import random
import asyncio

from gsuid_core.sv import SV
from gsuid_core.aps import scheduler
from gsuid_core.bot import Bot
from gsuid_core.gss import gss
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import gs_subscribe

from .main import ann, consume_remind
from .util import black_ids
from .ann_card import sub_ann, unsub_ann, ann_list_card, ann_detail_card
from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from ..utils.image.convert import convert_img
from ..genshinuid_config.gs_config import gsconfig

sv_ann = SV("原神公告")
sv_ann_sub = SV("原神公告订阅", pm=2)
sv_ann_hint = SV("原神公告红点")
sv_ann_schedule = SV("原神定时清空公告红点", priority=3)


@sv_ann.on_command(
    ("原神公告"),
    to_ai="""查看原神公告列表或指定公告详情

    当用户说"原神公告"、"游戏公告"、"有什么公告"时调用。
    留空显示公告列表图片，输入公告ID显示对应公告详情。

    Args:
        text: 可选的公告ID数字，留空显示公告列表
              例如 ""（显示列表）、"12345"（显示指定公告详情）
    """,
)
async def ann_(bot: Bot, ev: Event):
    ann_id = ev.text
    if not ann_id:
        img = await ann_list_card()
        img = await convert_img(img)
        return await bot.send(img)

    ann_id = ann_id.replace("#", "")
    if not ann_id.isdigit():
        raise Exception("公告ID不正确")

    img = await ann_detail_card(int(ann_id))
    await bot.send(img)


@sv_ann_sub.on_fullmatch(
    "订阅原神公告",
    to_ai="""订阅原神公告推送

    当用户说"订阅原神公告"时调用。需要在群聊中使用。
    订阅后群内将自动推送新公告通知。

    Args:
        text: 无需参数，留空即可
    """,
)
async def sub_ann_(bot: Bot, ev: Event):
    if ev.group_id is None:
        return await bot.send("请在群聊中订阅")
    await bot.send(sub_ann(bot.bot_id, ev.group_id))


@sv_ann_sub.on_fullmatch(
    ("取消订阅原神公告", "取消原神公告", "退订原神公告"),
    to_ai="""取消订阅原神公告推送

    当用户说"取消订阅原神公告"、"退订原神公告"时调用。需要在群聊中使用。

    Args:
        text: 无需参数，留空即可
    """,
)
async def unsub_ann_(bot: Bot, ev: Event):
    if ev.group_id is None:
        return await bot.send("请在群聊中取消订阅")
    await bot.send(unsub_ann(bot.bot_id, ev.group_id))


@sv_ann_hint.on_fullmatch(
    (
        "取消原神公告红点",
        "清除原神公告红点",
        "清除公告红点",
        "取消公告红点",
    ),
    to_ai="""清除原神公告的未读红点提示

    当用户说"清除公告红点"、"取消公告红点"时调用。
    需要用户已绑定UID。

    Args:
        text: 无需参数，留空即可
    """,
)
async def consume_remind_(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    else:
        await bot.send(await consume_remind(uid))


@sv_ann_schedule.on_fullmatch(
    ("开启自动清红", "关闭自动清红"),
    block=True,
    to_ai="""开启或关闭自动清除原神公告红点功能

    当用户说"开启自动清红"、"关闭自动清红"时调用。
    开启后每5小时自动清除公告未读红点。

    Args:
        text: 无需参数，留空即可。开启/关闭由命令本身决定
    """,
)
async def get_ann_schedule_msg(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if not uid:
        return await bot.send(UID_HINT)

    logger.info(t("log.genshinuid.uid_uid_6dd59a", uid=uid))
    await gs_subscribe.add_subscribe(
        "single",
        "[原神] 自动清红",
        ev,
        extra_message=uid,
    )
    await bot.send(f"UID{uid}已开启自动清红!")


@scheduler.scheduled_job("cron", hour="*/5")
async def send_ann_schedule():
    logger.info(t("log.genshinuid.msg_856bd2"))
    datas = await gs_subscribe.get_subscribe("[原神] 自动清红")
    if datas:
        for subscribe in datas:
            if subscribe.extra_message:
                await consume_remind(subscribe.extra_message)
                await asyncio.sleep(random.uniform(5, 10))


@scheduler.scheduled_job("cron", minute=10)
async def check_ann():
    await check_ann_state()


async def check_ann_state():
    logger.info(t("log.genshinuid.msg_d457f8"))
    ids = gsconfig.get_config("Ann_Ids").data
    sub_list = gsconfig.get_config("Ann_Groups").data

    if not sub_list:
        logger.info(t("log.genshinuid.msg_a6d5f9"))
        return

    if not ids:
        ids = await ann().get_ann_ids()
        if not ids:
            raise Exception("获取原神公告ID列表错误,请检查接口")
        gsconfig.set_config("Ann_Ids", ids)
        logger.info(t("log.genshinuid.msg_357117"))
        return

    new_ids = await ann().get_ann_ids()
    new_ann = set(ids) ^ set(new_ids)

    if not new_ann:
        logger.info(t("log.genshinuid.msg_517227"))
        return

    for ann_id in new_ann:
        if ann_id in black_ids:
            continue
        try:
            img = await ann_detail_card(ann_id)
            img = await convert_img(img)
            for bot_id in sub_list:
                try:
                    for BOT_ID in gss.active_bot:
                        bot = gss.active_bot[BOT_ID]
                        for group_id in sub_list[bot_id]:
                            await bot.target_send(img, "group", group_id, bot_id, "", "")
                            await asyncio.sleep(random.uniform(1, 3))
                except Exception as e:
                    logger.exception(e)
        except Exception as e:
            logger.exception(str(e))

    logger.info(t("log.genshinuid.msg_ec7120"))
    gsconfig.set_config("Ann_Ids", new_ids)
