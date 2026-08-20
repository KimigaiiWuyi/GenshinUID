import re
from typing import Optional

from gsuid_core.sv import SV, get_plugin_available_prefix
from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.subscribe import Subscribe, gs_subscribe
from gsuid_core.utils.database.models import GsBind, GsUser

from ..utils.message import PREFIX as P, UID_HINT
from .draw_config_card import draw_config_img


def _remind():
    from ..genshinuid_resin.special_remind import (
        SPECIAL_TASK,
        extract_email,
        default_qq_email,
        is_email_remind_text,
    )

    return SPECIAL_TASK, extract_email, default_qq_email, is_email_remind_text


sv_self_config = SV("原神配置")

PRIV_MAP = {
    "宝钱": 2000,
    "体力": 100,
    "派遣": 300,
    "质变仪": 1000,
    "自动签到": None,
    "自动米游币": None,
    "推送": None,
    "日常检查": None,
    "活动提醒": None,
}


@sv_self_config.on_fullmatch(
    ("配置", "原神配置"),
    to_ai="""查看当前用户的原神功能配置状态

    当用户说"配置"、"原神配置"、"我的配置"时调用。
    以图片形式展示当前用户已开启的各项推送和自动功能状态。

    Args:
        text: 无需参数，留空即可
    """,
)
async def send_config_card(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.gs_ebec48"))
    im = await draw_config_img(ev.bot_id)
    await bot.send(im)


@sv_self_config.on_prefix(
    ("设置"),
    to_ai="""设置原神功能的阈值参数

    当用户说"设置体力阈值200"、"设置宝钱阈值1500"时调用。
    需要用户已绑定UID和Cookie，且对应功能已开启。

    Args:
        text: 格式为"功能名称阈值数字"，例如 "体力阈值200"、"宝钱阈值1500"、"派遣阈值200"、"质变仪阈值800"
              可设置的功能：体力、宝钱、派遣、质变仪
    """,
)
async def send_config_ev(bot: Bot, ev: Event):
    logger.info(t("log.genshinuid.msg_6ea246"))

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    cookie = await GsUser.get_user_cookie_by_uid(uid)
    if cookie is None:
        return await bot.send(
            f"🔔 提示：你的当前UID{uid}暂未绑定Cookie~\n"
            f"📎 请使用扫码登陆命令获取Cookie\n"
            f"🚩 或者查看帮助文档获取绑定方式\n"
            f"💡 若你想切换UID, 可以尝试命令：{P}切换UID"
        )

    config_name = "".join(re.findall("[\u4e00-\u9fa5]", ev.text.replace("阈值", "")))

    _, _, _, is_email_remind_text = _remind()
    if is_email_remind_text(ev.text):
        return await _set_special_remind_email(bot, ev)

    value = re.findall(r"\d+", ev.text)
    value = value[0] if value else None

    if value is None:
        return await bot.send(f"🔨 [原神服务]\n❌ 请输入正确的阈值数字...\n🚩 例如: {P}设置体力阈值200")

    logger.info(t("log.genshinuid.func_config_name_value_value_556366", config_name=config_name, value=value))

    if config_name not in PRIV_MAP or (config_name in PRIV_MAP and PRIV_MAP[config_name] is None):
        return await bot.send(f"🔨 [原神服务]\n❌ 请输入正确的功能名称...\n🚩 例如: {P}设置体力阈值200")

    datas = await gs_subscribe.get_subscribe(
        f"[原神] {config_name}",
        ev.user_id,
        ev.bot_id,
        ev.user_type,
    )

    if datas:
        if len(datas) > 1:
            logger.warning(t("log.genshinuid.p0_datas_6006b0", p0=ev.user_id, datas=datas))

        data = datas[0]
        await gs_subscribe.update_subscribe_message(
            "single",
            data.task_name,
            ev,
            extra_message=str(value),
        )
        im = f"🔨 [原神服务]\n✅ 已为[UID{uid}]设置{config_name}为{value}!"
    else:
        im = f"🔨 [原神服务]\n❌ 请先开启功能...\n🚩 例如: {P}开启体力推送"

    await bot.send(im)


# 开启 自动签到 和 推送树脂提醒 功能
@sv_self_config.on_prefix(
    ("开启", "关闭"),
    to_ai="""开启或关闭原神的各项推送和自动功能

    当用户说"开启体力推送"、"关闭自动签到"、"开启宝钱推送"时调用。
    需要用户已绑定UID和Cookie。操作结果以文字形式返回。

    Args:
        text: 功能名称，可选值：
              - "体力"/"体力推送"：树脂满时提醒
              - "宝钱"/"宝钱推送"：洞天宝钱满时提醒
              - "派遣"/"派遣推送"：派遣完成时提醒
              - "质变仪"/"质变仪推送"：参量质变仪可用时提醒
              - "自动签到"：每日自动米游社签到
              - "自动米游币"：每日自动获取米游币
              - "推送"：推送总开关
              - "日常检查"：每日零点检查日常完成情况
              - "活动提醒"：活动即将结束时提醒
              - "邮箱提醒"：体力溢出改走邮箱。可不带邮箱（默认 QQ 号@qq.com），也可指定，例如 开启邮箱提醒 a@b.c
    """,
)
async def open_switch_func(bot: Bot, ev: Event):
    SPECIAL_TASK, _extract, _default, is_email_remind_text = _remind()
    if is_email_remind_text(ev.text):
        return await _switch_special_remind(bot, ev)

    user_id = ev.user_id
    config_name = ev.text
    if config_name.startswith(("体力", "宝钱", "派遣", "质变仪")):
        config_name = config_name.replace("推送", "")

    if config_name not in PRIV_MAP:
        return await bot.send(f"🔨 [原神服务]\n❌ 请输入正确的功能名称...\n🚩 例如: {P}开启自动签到")

    logger.info(t("log.genshinuid.user_id_p0_p1_512ea1", user_id=user_id, p0=ev.command[2:], p1=ev.text))

    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        return await bot.send(UID_HINT)
    cookie = await GsUser.get_user_cookie_by_uid(uid)
    if cookie is None:
        PREFIX = get_plugin_available_prefix("GenshinUID")
        return await bot.send(
            f"🔔 提示：你的当前UID{uid}暂未绑定Cookie~\n"
            f"📎 请使用扫码登陆命令获取Cookie\n"
            f"🚩 或者查看帮助文档获取绑定方式\n"
            f"💡 若你想切换UID, 可以尝试命令：{PREFIX}切换UID"
        )

    c_name = f"[原神] {config_name}"

    if "开启" in ev.command:
        im = f"🔨 [原神服务]\n✅ 已为[UID{uid}]开启{config_name}功能。"

        if PRIV_MAP[config_name] is None and await gs_subscribe.get_subscribe(c_name, uid=uid):
            await Subscribe.update_data_by_data(
                {
                    "task_name": c_name,
                    "uid": uid,
                },
                {
                    "user_id": ev.user_id,
                    "bot_id": ev.bot_id,
                    "group_id": ev.group_id,
                    "bot_self_id": ev.bot_self_id,
                    "user_type": ev.user_type,
                    "WS_BOT_ID": ev.WS_BOT_ID,
                },
            )
        else:
            await gs_subscribe.add_subscribe(
                "single",
                c_name,
                ev,
                extra_message=PRIV_MAP[config_name],
                uid=uid,
            )

        if PRIV_MAP[config_name]:
            im += f"\n🔧 并设置了触发阈值为{PRIV_MAP[config_name]}!"
            if not await gs_subscribe.get_subscribe("[原神] 推送", uid=uid):
                im += "\n⚠ 警告: 由于未打开推送总开关, 所以此项设置可能无效！"
                im += f"如需打开总开关, 请发送命令开启推送: {P}开启推送！"
        if config_name == "推送":
            resin = await gs_subscribe.get_subscribe("[原神] 体力", uid=uid)
            coin = await gs_subscribe.get_subscribe("[原神] 宝钱", uid=uid)
            go = await gs_subscribe.get_subscribe("[原神] 派遣", uid=uid)
            trans = await gs_subscribe.get_subscribe("[原神] 质变仪", uid=uid)
            daily = await gs_subscribe.get_subscribe("[原神] 日常检查", uid=uid)
            activity = await gs_subscribe.get_subscribe("[原神] 活动提醒", uid=uid)

            im += (
                f"\n✅ 如需关闭请发送命令: {P}关闭推送\n💚"
                " 该项为总开关, 你开可以单独开启体力、宝钱、派遣、质变仪、日常检查的推送。"
            )

            im += "\n🔖 【当前推送设置状态】"
            if resin:
                im += f"\n✅ 体力推送 (阈值: {resin[0].extra_message})"
            else:
                im += f"\n❌ 体力推送 (可发送{P}开启体力推送)"

            if coin:
                im += f"\n✅ 宝钱推送 (阈值: {coin[0].extra_message})"
            else:
                im += f"\n❌ 宝钱推送 (可发送{P}开启宝钱推送)"

            if go:
                im += f"\n✅ 派遣推送 (阈值: {go[0].extra_message})"
            else:
                im += f"\n❌ 派遣推送 (可发送{P}开启派遣推送)"

            if trans:
                im += f"\n✅ 质变仪推送 (阈值: {trans[0].extra_message})"
            else:
                im += f"\n❌ 质变仪推送 (可发送{P}开启质变仪推送)"

            if daily:
                im += "\n✅ 日常检查推送 (将在每日零点检查日常是否完成)"
            else:
                im += f"\n❌ 日常检查推送 (可发送{P}开启日常检查推送)"

            if activity:
                im += "\n✅ 活动提醒推送 (将在活动将要结束之时仍未完成时提醒)"
            else:
                im += f"\n❌ 活动提醒推送 (可发送{P}开启活动提醒推送)"

            special = await gs_subscribe.get_subscribe(SPECIAL_TASK, uid=uid)
            if special and special[0].extra_message:
                im += f"\n✅ 邮箱提醒 (发到 {special[0].extra_message}，体力溢出走邮件)"
            else:
                im += f"\n❌ 邮箱提醒 (可发送{P}开启邮箱提醒)"

    else:
        data = await gs_subscribe.get_subscribe(
            c_name,
            ev.user_id,
            ev.bot_id,
            ev.user_type,
        )
        if data:
            await gs_subscribe.delete_subscribe(
                "single",
                c_name,
                ev,
                uid=uid,
            )
            im = f"🔨 [原神服务]\n✅ 已为[UID{uid}]关闭{config_name}功能。"
        else:
            im = f"🔨 [原神服务]\n❌ 未找到[UID{uid}]的{config_name}功能配置, 该功能可能未开启。"

    await bot.send(im)


async def _require_uid_cookie(bot: Bot, ev: Event) -> Optional[str]:
    uid = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    if uid is None:
        await bot.send(UID_HINT)
        return None
    cookie = await GsUser.get_user_cookie_by_uid(uid)
    if cookie is None:
        await bot.send(
            f"🔔 提示：你的当前UID{uid}暂未绑定Cookie~\n"
            f"📎 请使用扫码登陆命令获取Cookie\n"
            f"💡 若你想切换UID, 可以尝试命令：{P}切换UID"
        )
        return None
    return uid


async def _ensure_push_and_resin(ev: Event, uid: str) -> str:
    extra = ""
    if not await gs_subscribe.get_subscribe("[原神] 推送", uid=uid):
        await gs_subscribe.add_subscribe("single", "[原神] 推送", ev, uid=uid)
        extra += "\n✅ 已同时开启推送总开关。"
    if not await gs_subscribe.get_subscribe("[原神] 体力", uid=uid):
        await gs_subscribe.add_subscribe(
            "single",
            "[原神] 体力",
            ev,
            extra_message=str(PRIV_MAP["体力"]),
            uid=uid,
        )
        extra += f"\n✅ 已同时开启体力推送（阈值 {PRIV_MAP['体力']}）。"
    return extra


async def _switch_special_remind(bot: Bot, ev: Event) -> None:
    SPECIAL_TASK, extract_email, default_qq_email, _is_email = _remind()
    uid = await _require_uid_cookie(bot, ev)
    if uid is None:
        return

    if "关闭" in ev.command:
        data = await gs_subscribe.get_subscribe(SPECIAL_TASK, uid=uid)
        if data:
            await gs_subscribe.delete_subscribe("single", SPECIAL_TASK, ev, uid=uid)
            await bot.send(f"🔨 [原神服务]\n✅ 已为[UID{uid}]关闭邮箱提醒，体力溢出将改回群/私聊推送。")
        else:
            await bot.send(f"🔨 [原神服务]\n❌ [UID{uid}]未开启邮箱提醒。")
        return

    email = extract_email(ev.text)
    hint = ""
    if email is None:
        existed = await gs_subscribe.get_subscribe(SPECIAL_TASK, uid=uid)
        if existed and existed[0].extra_message:
            email = existed[0].extra_message
        else:
            email = default_qq_email(ev.user_id)
            hint = f"\n💡 未指定邮箱，已使用 {email}。改邮箱请发：{P}设置邮箱提醒 你的邮箱"

    await _enable_email_remind(bot, ev, uid, email, hint)


async def _enable_email_remind(bot: Bot, ev: Event, uid: str, email: str, hint: str = "") -> None:
    SPECIAL_TASK, _extract, _default, _is_email = _remind()
    await gs_subscribe.add_subscribe(
        "single",
        SPECIAL_TASK,
        ev,
        extra_message=email,
        uid=uid,
    )
    extra = await _ensure_push_and_resin(ev, uid)
    await bot.send(
        f"🔨 [原神服务]\n✅ 已为[UID{uid}]开启邮箱提醒。\n📧 体力溢出将发到 {email}，不再走群/私聊。{hint}{extra}"
    )


async def _set_special_remind_email(bot: Bot, ev: Event) -> None:
    SPECIAL_TASK, extract_email, default_qq_email, _is_email = _remind()
    uid = await _require_uid_cookie(bot, ev)
    if uid is None:
        return
    email = extract_email(ev.text)
    if email is None:
        email = default_qq_email(ev.user_id)
    existed = await gs_subscribe.get_subscribe(SPECIAL_TASK, uid=uid)
    if not existed:
        await bot.send(f"🔨 [原神服务]\n❌ 请先开启邮箱提醒。\n🚩 例如: {P}开启邮箱提醒")
        return
    await gs_subscribe.update_subscribe_message(
        "single",
        SPECIAL_TASK,
        ev,
        extra_message=email,
        uid=uid,
    )
    await bot.send(f"🔨 [原神服务]\n✅ 已为[UID{uid}]更新邮箱提醒收件箱为 {email}")
