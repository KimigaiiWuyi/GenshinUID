"""通知/回调上报, QQ 模板 Markdown, 禁言.

按钮走 Alconna Keyboard; 这里只处理 UniMessage 覆盖不到的交互.
"""

from __future__ import annotations

from pathlib import Path

from nonebot.log import logger
from nonebot.adapters import Bot, Message as NBMessage
from nonebot.internal.adapter import Event

from .types import UserType, BanPayload
from .models import Message, MessageReceive
from .convert import SendSpecials
from .receive import extract_pm
from .identity import adapter_name, peek_qq_msg_id


def _to_str(value: object) -> str:
    return str(value) if value is not None else ""


def _base_receive(
    bot: Bot,
    *,
    bot_id: str,
    user_id: str,
    group_id: str | None,
    content: list[Message],
    msg_id: str = "",
    sender: dict[str, object] | None = None,
    user_type: UserType | None = None,
    pm: int = 6,
) -> MessageReceive:
    resolved: UserType = user_type if user_type is not None else ("group" if group_id else "direct")
    return MessageReceive(
        bot_id=bot_id,
        bot_self_id=str(bot.self_id),
        user_type=resolved,
        group_id=group_id,
        user_id=user_id,
        sender=sender if sender is not None else {},
        content=content,
        msg_id=msg_id,
        user_pm=pm,
    )


async def _ob11_notice(bot: Bot, event: Event) -> MessageReceive | None:
    from nonebot.adapters.onebot.v11.event import GroupUploadNoticeEvent

    if not isinstance(event, GroupUploadNoticeEvent):
        return None

    file_info = event.file
    val: str | None = None
    dumped = file_info.model_dump()
    if "url" in dumped and isinstance(dumped["url"], str) and dumped["url"]:
        val = dumped["url"]
    elif file_info.id and file_info.size is not None and file_info.size <= 1024 * 1024 * 4:
        val_data = await bot.call_api("get_file", file_id=file_info.id)
        if isinstance(val_data, dict):
            if "base64" in val_data and val_data["base64"]:
                val = str(val_data["base64"])
            elif "file" in val_data:
                import base64

                val = base64.b64encode(Path(str(val_data["file"])).read_bytes()).decode("utf-8")
    if val is None:
        logger.warning("[文件上传] 不支持的协议端")
        return None

    return _base_receive(
        bot,
        bot_id="onebot",
        user_id=str(event.user_id),
        group_id=str(event.group_id),
        content=[Message("file", f"{file_info.name}|{val}")],
        pm=await extract_pm(bot, event),
    )


async def _milky_notice(bot: Bot, event: Event) -> MessageReceive | None:
    from nonebot.adapters.milky.bot import Bot as MilkyBot
    from nonebot.adapters.milky.event import (
        GroupFileUploadEvent,
        FriendFileUploadEvent,
    )

    if not isinstance(bot, MilkyBot):
        return None
    pm = await extract_pm(bot, event)
    if isinstance(event, GroupFileUploadEvent):
        link = await bot.get_group_file_download_url(
            group_id=event.data.group_id,
            file_id=event.data.file_id,
        )
        return _base_receive(
            bot,
            bot_id="milky",
            user_id=_to_str(event.data.user_id),
            group_id=_to_str(event.data.group_id),
            content=[Message("file", str(link))],
            user_type="group",
            pm=pm,
        )
    if isinstance(event, FriendFileUploadEvent):
        link = await bot.get_private_file_download_url(
            user_id=event.data.user_id,
            file_id=event.data.file_id,
            file_hash=event.data.file_hash,
        )
        return _base_receive(
            bot,
            bot_id="milky",
            user_id=_to_str(event.data.user_id),
            group_id=None,
            content=[Message("file", str(link))],
            user_type="direct",
            pm=pm,
        )
    return None


async def _telegram_callback(bot: Bot, event: Event) -> MessageReceive | None:
    from nonebot.adapters.telegram.event import CallbackQueryEvent

    if not isinstance(event, CallbackQueryEvent):
        return None
    if event.from_.is_bot or event.message is None or event.data is None:
        return None
    if event.message.chat.type == "private":
        user_type: UserType = "direct"
        group_id = None
    else:
        user_type = "group"
        group_id = str(event.message.chat.id)
    return _base_receive(
        bot,
        bot_id="telegram",
        user_id=str(event.from_.id),
        group_id=group_id,
        content=[Message("text", event.data)],
        msg_id=str(event.id),
        sender={"nickname": event.from_.first_name or str(event.from_.id)},
        user_type=user_type,
        pm=await extract_pm(bot, event),
    )


async def _discord_callback(bot: Bot, event: Event) -> MessageReceive | None:
    from nonebot.adapters.discord import MessageComponentInteractionEvent
    from nonebot.adapters.discord.api import (
        ChannelType,
        InteractionResponse,
        InteractionCallbackType,
        is_not_unset,
    )

    if not isinstance(event, MessageComponentInteractionEvent):
        return None

    is_dm = is_not_unset(event.channel) and event.channel.type == ChannelType.DM
    user_type: UserType = "direct" if is_dm else "group"
    user_id = ""
    nickname = ""
    avatar: object | None = None
    if user_type == "direct":
        user = event.user
        if is_not_unset(user) and user is not None:
            user_id = str(user.id)
            nickname = str(user.username)
            avatar = user.avatar
    else:
        member = event.member
        if is_not_unset(member) and member is not None:
            user = member.user
            if is_not_unset(user) and user is not None:
                user_id = str(user.id)
                nickname = str(user.username)
                avatar = user.avatar

    await bot.call_api(
        "create_interaction_response",
        interaction_id=event.id,
        interaction_token=event.token,
        response=InteractionResponse(type=InteractionCallbackType.PONG),
    )
    return _base_receive(
        bot,
        bot_id="discord",
        user_id=user_id,
        group_id=str(event.channel_id),
        content=[Message("text", event.data.custom_id)],
        msg_id=str(event.id),
        sender={
            "nickname": nickname,
            "avatar": f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}",
        },
        user_type=user_type,
        pm=await extract_pm(bot, event),
    )


async def _qq_callback(bot: Bot, event: Event) -> MessageReceive | None:
    from nonebot.adapters.qq.bot import Bot as QQBot
    from nonebot.adapters.qq.event import InteractionCreateEvent

    if not isinstance(bot, QQBot) or not isinstance(event, InteractionCreateEvent):
        return None

    self_id = str(bot.self_id)
    resolved = event.data.resolved if event.data is not None else None
    button_data = ""
    if resolved is not None and resolved.button_data is not None:
        button_data = str(resolved.button_data)

    if event.scene == "guild":
        bot_id = "qqguild"
        user_type: UserType = "group"
        group_id = str(event.channel_id)
        user_id = event.get_user_id()
        msg_id = str(resolved.message_id) if resolved is not None and resolved.message_id is not None else str(event.id)
        sender: dict[str, object] = {}
    else:
        bot_id = "qqgroup"
        if event.scene == "group":
            user_id = str(event.group_member_openid)
            group_id = str(event.group_openid)
            user_type = "group"
            sender = {"avatar": f"https://q.qlogo.cn/qqapp/{self_id}/{user_id}/0"}
        else:
            user_id = str(event.user_openid)
            group_id = None
            user_type = "direct"
            sender = {}
        cached = peek_qq_msg_id(user_id)
        msg_id = cached if cached is not None else str(event.id)

    await bot.put_interaction(interaction_id=event.id, code=0)
    return _base_receive(
        bot,
        bot_id=bot_id,
        user_id=user_id,
        group_id=group_id,
        content=[Message("text", button_data)],
        msg_id=msg_id,
        sender=sender,
        user_type=user_type,
        pm=await extract_pm(bot, event),
    )


async def handle_notice(bot: Bot, event: Event) -> MessageReceive | None:
    name = adapter_name(bot)
    if name == "OneBot V11":
        return await _ob11_notice(bot, event)
    if name == "Milky":
        return await _milky_notice(bot, event)
    if name == "Telegram":
        return await _telegram_callback(bot, event)
    if name == "Discord":
        return await _discord_callback(bot, event)
    if name == "QQ":
        return await _qq_callback(bot, event)
    return None


def append_qq_markdown(message: NBMessage, specials: SendSpecials) -> NBMessage:
    from nonebot.adapters.qq.models import (
        MessageMarkdown,
        MessageMarkdownParams,
    )
    from nonebot.adapters.qq.message import MessageSegment

    tmpl = specials.template_markdown
    if tmpl is not None:
        message.append(
            MessageSegment.markdown(
                MessageMarkdown(
                    custom_template_id=tmpl["template_id"],
                    params=[MessageMarkdownParams(key=key, values=[tmpl["para"][key]]) for key in tmpl["para"]],
                )
            )
        )
    elif specials.markdown:
        message.append(MessageSegment.markdown(specials.markdown))
    return message


async def ban_user(bot: Bot, bot_id: str, data: BanPayload) -> None:
    if "user_id" not in data or "group_id" not in data:
        return
    duration = data["duration"] if "duration" in data else None
    if duration is None:
        return
    if not (isinstance(duration, int) or (isinstance(duration, str) and duration.isdigit())):
        return
    if bot_id in {"onebot", "milky"}:
        await bot.call_api(
            "set_group_ban",
            group_id=int(data["group_id"]),
            user_id=int(data["user_id"]),
            duration=int(duration),
        )
        return
    logger.warning(f"[gscore] 平台 {bot_id} 暂不支持禁言")
