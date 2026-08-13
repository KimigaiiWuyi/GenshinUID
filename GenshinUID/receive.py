"""平台事件 -> GsCore MessageReceive, 依赖 Alconna UniMsg/Target/MsgId."""

from __future__ import annotations

from nonebot import require
from nonebot.adapters import Bot
from nonebot.permission import SUPERUSER
from nonebot.internal.adapter import Event

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna.uniseg import Target, UniMessage  # noqa: E402

from .types import UserType, SenderInfo
from .models import Message, MessageReceive
from .convert import uni_to_gs, command_starts
from .identity import (
    adapter_name,
    infer_bot_id,
    cache_qq_msg_id,
    format_group_id,
)


def _sender_ob11(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.onebot.v11.event import (
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    if isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        nick = event.sender.nickname or user_id
        return SenderInfo(
            nickname=nick,
            user_id=user_id,
            avatar=f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640",
        )
    return SenderInfo(nickname=user_id)


def _sender_ob12(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.onebot.v12.event import (
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    if isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        return SenderInfo(user_id=user_id)
    return SenderInfo(nickname=user_id)


def _sender_telegram(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.telegram.event import (
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    if isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        nick = event.from_.first_name or user_id
        return SenderInfo(nickname=nick, user_id=user_id)
    return SenderInfo(nickname=user_id)


def _sender_discord(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.discord import (
        GuildMessageCreateEvent,
        DirectMessageCreateEvent,
    )

    if isinstance(event, (GuildMessageCreateEvent, DirectMessageCreateEvent)):
        avatar = event.author.avatar
        info: SenderInfo = {"nickname": event.author.username}
        if avatar is not None:
            info["avatar"] = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}"
        return info
    return SenderInfo(nickname=user_id)


def _sender_qq(event: Event, user_id: str, self_id: str) -> SenderInfo:
    from nonebot.adapters.qq.event import (
        GuildMessageEvent,
        C2CMessageCreateEvent,
        GroupMessageCreateEvent,
        DirectMessageCreateEvent,
        GroupAtMessageCreateEvent,
    )

    if isinstance(event, DirectMessageCreateEvent):
        nick = event.author.username or user_id
        return SenderInfo(nickname=nick, user_id=user_id)
    if isinstance(event, (GroupAtMessageCreateEvent, GroupMessageCreateEvent)):
        return SenderInfo(avatar=f"https://q.qlogo.cn/qqapp/{self_id}/{user_id}/0")
    if isinstance(event, C2CMessageCreateEvent):
        openid = event.author.user_openid
        nick = f"QQ用户{openid[:4]}" if openid else "QQ用户"
        return SenderInfo(nickname=nick)
    if isinstance(event, GuildMessageEvent):
        nick = event.author.username or user_id
        return SenderInfo(nickname=nick, user_id=user_id)
    return SenderInfo(nickname=user_id)


def _sender_milky(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.milky.event import (
        GroupMessageEvent,
        FriendMessageEvent,
    )

    if isinstance(event, (GroupMessageEvent, FriendMessageEvent)):
        nick = event.data.sender.nickname
        return SenderInfo(
            name=nick,
            nickname=nick,
            avatar=f"http://q1.qlogo.cn/g?b=qq&nk={event.data.sender.user_id}&s=640",
        )
    return SenderInfo(nickname=user_id)


def _sender_heybox(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.heybox.event import UserIMMessageEvent

    if isinstance(event, UserIMMessageEvent):
        return SenderInfo(name=event.nickname, nickname=event.nickname)
    return SenderInfo(nickname=user_id)


def _sender_console(event: Event, user_id: str) -> SenderInfo:
    from nonebot.adapters.console.event import MessageEvent

    if isinstance(event, MessageEvent):
        nick = event.user.nickname or event.user.id
        return SenderInfo(nickname=nick, user_id=event.user.id)
    return SenderInfo(nickname=user_id)


def extract_sender(
    bot: Bot,
    event: Event,
    user_id: str,
    bot_id: str,
) -> SenderInfo:
    name = adapter_name(bot)
    if name == "OneBot V11":
        return _sender_ob11(event, user_id)
    if name == "OneBot V12":
        return _sender_ob12(event, user_id)
    if name == "Telegram":
        return _sender_telegram(event, user_id)
    if name == "Discord":
        return _sender_discord(event, user_id)
    if name == "QQ":
        return _sender_qq(event, user_id, str(bot.self_id))
    if name == "Milky":
        return _sender_milky(event, user_id)
    if name == "Heybox":
        return _sender_heybox(event, user_id)
    if name == "Console":
        return _sender_console(event, user_id)
    return SenderInfo(nickname=user_id)


def _pm_ob11(event: Event) -> int:
    from nonebot.adapters.onebot.v11.event import (
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    if isinstance(event, (GroupMessageEvent, PrivateMessageEvent)):
        if event.sender.role == "owner":
            return 2
        if event.sender.role == "admin":
            return 3
    return 6


def _pm_qq_guild(event: Event) -> int:
    from nonebot.adapters.qq.event import GuildMessageEvent

    if isinstance(event, GuildMessageEvent) and event.member is not None:
        roles = event.member.roles
        if roles is not None:
            if 4 in roles:
                return 2
            if 2 in roles:
                return 3
            if 5 in roles:
                return 5
    return 6


async def extract_pm(bot: Bot, event: Event) -> int:
    if await SUPERUSER(bot, event):
        return 1
    name = adapter_name(bot)
    if name == "OneBot V11":
        return _pm_ob11(event)
    if name == "QQ":
        return _pm_qq_guild(event)
    return 6


async def build_message_receive(
    bot: Bot,
    event: Event,
    uni: UniMessage,
    target: Target,
    msg_id: str,
) -> MessageReceive | None:
    bot_id = infer_bot_id(bot, event, target)
    user_type: UserType = "direct" if target.private else "group"
    group_id = format_group_id(target, bot_id)
    user_id = event.get_user_id()
    self_id = str(bot.self_id)

    if bot_id == "qqgroup" and user_id and msg_id:
        cache_qq_msg_id(user_id, msg_id)

    content = await uni_to_gs(uni, bot, command_starts())
    if event.is_tome():
        content.append(Message("at", self_id))
    if not content:
        return None

    return MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender=dict(extract_sender(bot, event, user_id, bot_id)),
        content=content,
        msg_id=msg_id,
        user_pm=await extract_pm(bot, event),
    )
