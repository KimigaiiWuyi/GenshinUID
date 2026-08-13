"""平台 bot_id 推断、Bot 查找、下发 Target 构造."""

from __future__ import annotations

from typing import Any
from collections import OrderedDict

from nonebot import get_bot, require, get_bots
from nonebot.log import logger
from nonebot.adapters import Bot
from nonebot.internal.adapter import Event

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna.uniseg import Target  # noqa: E402

ADAPTER_BOT_ID: dict[str, str] = {
    "OneBot V11": "onebot",
    "OneBot V12": "onebot_v12",
    "Telegram": "telegram",
    "Discord": "discord",
    "Feishu": "feishu",
    "Heybox": "heybox",
    "Milky": "milky",
    "Kaiheila": "kaiheila",
    "DoDo": "dodo",
    "RedProtocol": "onebot:red",
    "Kritor": "kritor",
    "Satori": "satori",
    "ntchat": "ntchat",
    "Console": "console",
    "Ding": "ding",
    "Minecraft": "minecraft",
    "Mirai": "mirai",
    "GitHub": "github",
    "Mail": "mail",
    "WXMP": "wxmp",
    "Tailchat": "tailchat",
    "EFChat": "efchat",
    "YunHu": "yunhu",
    "VoceChat": "vocechat",
    "bilibili Live": "bililive",
}

BOT_ID_ADAPTERS: dict[str, tuple[str, ...]] = {
    "onebot": ("OneBot V11",),
    "onebot_v12": ("OneBot V12",),
    "onebot:red": ("RedProtocol",),
    "qqguild": ("QQ",),
    "qqgroup": ("QQ",),
    "telegram": ("Telegram",),
    "discord": ("Discord",),
    "feishu": ("Feishu",),
    "heybox": ("Heybox",),
    "milky": ("Milky",),
    "kaiheila": ("Kaiheila",),
    "dodo": ("DoDo",),
    "kritor": ("Kritor",),
    "satori": ("Satori",),
    "ntchat": ("ntchat",),
    "villa": ("Villa",),
    "console": ("Console",),
}

DUAL_ID_BOTS = frozenset({"heybox", "villa"})
CHANNEL_BOTS = frozenset({"qqguild", "discord", "kaiheila", "dodo", "heybox", "villa"})

_qq_msg_seq: OrderedDict[str, int] = OrderedDict()
_QQ_SEQ_LIMIT = 30
_qq_msg_id_cache: OrderedDict[str, str] = OrderedDict()
_QQ_MSG_CACHE_LIMIT = 300


def adapter_name(bot: Bot) -> str:
    return bot.adapter.get_name()


def infer_bot_id(bot: Bot, event: Event, target: Target) -> str:
    name = adapter_name(bot)
    if name == "QQ":
        return _infer_qq_bot_id(event, target)
    if name in ADAPTER_BOT_ID:
        return ADAPTER_BOT_ID[name]
    return _bot_id_from_module(event)


def _infer_qq_bot_id(event: Event, target: Target) -> str:
    from nonebot.adapters.qq.event import (
        GuildMessageEvent,
        GuildMemberAddEvent,
        C2CMessageCreateEvent,
        GuildMemberRemoveEvent,
        InteractionCreateEvent,
        GroupMessageCreateEvent,
        DirectMessageCreateEvent,
        GroupAtMessageCreateEvent,
    )

    if isinstance(
        event,
        (
            GroupAtMessageCreateEvent,
            GroupMessageCreateEvent,
            C2CMessageCreateEvent,
        ),
    ):
        return "qqgroup"
    if isinstance(event, InteractionCreateEvent):
        if event.scene == "guild":
            return "qqguild"
        return "qqgroup"
    if isinstance(
        event,
        (
            GuildMessageEvent,
            DirectMessageCreateEvent,
            GuildMemberAddEvent,
            GuildMemberRemoveEvent,
        ),
    ):
        return "qqguild"
    if target.channel:
        return "qqguild"
    return "qqgroup"


def _bot_id_from_module(event: Event) -> str:
    parts = event.__class__.__module__.split(".")
    if "adapters" in parts:
        idx = parts.index("adapters")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    if len(parts) > 2:
        return parts[2]
    return parts[-1] if parts else "unknown"


def format_group_id(target: Target, bot_id: str) -> str | None:
    if target.private:
        if bot_id == "qqguild" and target.parent_id:
            return target.parent_id
        return None
    if bot_id in DUAL_ID_BOTS and target.parent_id:
        return f"{target.id}-{target.parent_id}"
    if target.id:
        return target.id
    return None


def cache_qq_msg_id(user_id: str, msg_id: str) -> None:
    if not user_id or not msg_id:
        return
    _qq_msg_id_cache[user_id] = msg_id
    _qq_msg_id_cache.move_to_end(user_id)
    while len(_qq_msg_id_cache) > _QQ_MSG_CACHE_LIMIT:
        _qq_msg_id_cache.popitem(last=False)


def peek_qq_msg_id(user_id: str) -> str | None:
    if user_id in _qq_msg_id_cache:
        return _qq_msg_id_cache[user_id]
    return None


def next_qq_reply_seq(msg_id: str) -> int:
    """Alconna QQ exporter 发现 extra['qq.reply_seq'] 非 None 会先 +1."""
    seq = _qq_msg_seq[msg_id] if msg_id in _qq_msg_seq else 1
    _qq_msg_seq[msg_id] = seq + 1
    _qq_msg_seq.move_to_end(msg_id)
    while len(_qq_msg_seq) > _QQ_SEQ_LIMIT:
        _qq_msg_seq.popitem(last=False)
    return seq


def build_send_target(
    bot: Bot,
    bot_id: str,
    target_id: str,
    target_type: str | None,
    msg_id: str,
    extra_group_id: str,
) -> Target:
    private = target_type == "direct"
    dest = target_id
    parent_id = ""
    channel = bot_id in CHANNEL_BOTS
    extra: dict[str, Any] = {}

    if bot_id in DUAL_ID_BOTS and "-" in dest:
        left, right = dest.split("-", 1)
        dest, parent_id = left, right
        channel = True

    if extra_group_id:
        if bot_id == "discord":
            dest = extra_group_id
            channel = True
        elif bot_id == "qqguild" and private:
            parent_id = extra_group_id
            channel = True

    if bot_id == "qqguild":
        channel = True
    elif bot_id == "qqgroup":
        channel = False

    if bot_id in {"qqgroup", "qqguild"} and msg_id:
        extra["qq.reply_seq"] = next_qq_reply_seq(msg_id) - 1

    return Target(
        dest,
        parent_id=parent_id,
        channel=channel,
        private=private,
        source=msg_id,
        self_id=str(bot.self_id),
        adapter=adapter_name(bot),
        extra=extra,
    )


def resolve_bot(bot_id: str, bot_self_id: str) -> Bot | None:
    bots = get_bots()
    if bot_self_id and bot_self_id in bots:
        return bots[bot_self_id]

    if bot_id in BOT_ID_ADAPTERS:
        hints = BOT_ID_ADAPTERS[bot_id]
        for bot in bots.values():
            if adapter_name(bot) in hints:
                return bot

    compact_want = bot_id.lower().replace("_", "").replace(":", "")
    for bot in bots.values():
        compact = adapter_name(bot).lower().replace(" ", "").replace("_", "")
        if compact_want in compact or compact in compact_want:
            return bot

    if not bots:
        logger.warning(f"当前没有可用 Bot, 无法下发. bot_id={bot_id}")
        return None
    logger.warning(f"未获取到精确 Bot 实例, 使用默认 Bot. bot_id={bot_id}")
    return get_bot()
