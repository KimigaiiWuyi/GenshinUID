"""平台元事件(meta event)映射与上报构造.

把各适配器的群成员变动与戳一戳类事件(入群/退群/戳一戳)
统一映射为 gsuid_core 的 meta 命名约定, 由本模块构造
content=[Message('meta-<事件名>', data)] 的 MessageReceive, 交回 __init__ 上报,
最终由 core 的 `@sv.on_meta(...)` 触发器分发.

拆分动机: 各适配器的 notice/request 事件五花八门, 全部塞进 __init__ 会让其过长.
本模块按适配器聚合映射逻辑, __init__ 仅负责连接校验与上报队列投递.

约定:
- 每个适配器一个 `_xxx_to_meta(bot, ev) -> Optional[MetaEvent]` 映射函数,
  返回 None 表示该事件无需作为 meta 上报(交由其它处理器或忽略).
- 适配器 import 一律惰性置于各映射函数内部(适配器为可选依赖, 顶层 import 会拖垮
  未安装该适配器的宿主).
- `MetaEvent.data` 即 meta 段的 data 字典, 插件侧用 `ev.get_meta(key)` 读取;
  务必包含 `user_id` / `group_id`(若适用), 既供插件读取, 也供 core 回填顶层字段.

当前支持的元事件(以 OneBot V11 为基准, 跨适配器同语义同名):
- user_join_group: 用户加入群/频道
- user_exit_group: 用户退出群/频道
- poke:           戳一戳(群/私聊)
"""

from typing import Any, Dict, Literal, Callable, Optional, NamedTuple

from nonebot.adapters import Bot
from nonebot.internal.adapter import Event

from .models import Message, MessageReceive


class MetaEvent(NamedTuple):
    """单条 meta 事件的归一化结果.

    event_name: 不含 `meta-` 前缀的事件名(如 `user_exit_group`).
    data:       meta 段 data 字典, 含该事件特有字段, 推荐带 `user_id`/`group_id`.
    bot_id:     平台 bot_id 覆盖; None 时由事件模块名推断(`ev.__module__.split('.')[2]`).
    user_type:  会话类型覆盖; None 时按 data 中是否有 group_id 推断 group/direct.
    """

    event_name: str
    data: Dict[str, Any]
    bot_id: Optional[str] = None
    user_type: Optional[str] = None


def _s(value: Any) -> str:
    """统一把平台侧 id/数值归一为字符串, None -> 空串."""
    return str(value) if value is not None else ""


# ---------------------------------------------------------------------------
# OneBot V11(参考实现)
# ---------------------------------------------------------------------------
def _ob11_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    raw_data: Dict[str, Any] = ev.dict()
    if raw_data.get("post_type") != "notice":
        return None
    ntype = raw_data.get("notice_type")
    if ntype == "group_increase":
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(raw_data.get("user_id")),
                "group_id": _s(raw_data.get("group_id")),
                "operator_id": _s(raw_data.get("operator_id")),
                "sub_type": raw_data.get("sub_type", ""),
            },
        )
    if ntype == "group_decrease":
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(raw_data.get("user_id")),
                "group_id": _s(raw_data.get("group_id")),
                "operator_id": _s(raw_data.get("operator_id")),
                "sub_type": raw_data.get("sub_type", ""),
            },
        )
    if ntype == "notify" and raw_data.get("sub_type") == "poke":
        data: Dict[str, Any] = {
            "user_id": _s(raw_data.get("user_id")),
            "target_id": _s(raw_data.get("target_id")),
        }
        if raw_data.get("group_id") is not None:
            data["group_id"] = _s(raw_data.get("group_id"))
        return MetaEvent("poke", data)
    return None


# ---------------------------------------------------------------------------
# Milky(现代 QQ 协议)
# ---------------------------------------------------------------------------
def _milky_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.milky.event import (
        GroupNudgeEvent,
        FriendNudgeEvent,
        GroupMemberDecreaseEvent,
        GroupMemberIncreaseEvent,
    )

    if isinstance(ev, GroupMemberIncreaseEvent):
        d = ev.data
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(d.user_id),
                "group_id": _s(d.group_id),
                "operator_id": _s(d.operator_id),
                "invitor_id": _s(d.invitor_id),
            },
        )
    if isinstance(ev, GroupMemberDecreaseEvent):
        d = ev.data
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(d.user_id),
                "group_id": _s(d.group_id),
                "operator_id": _s(d.operator_id),
            },
        )
    if isinstance(ev, GroupNudgeEvent):
        d = ev.data
        return MetaEvent(
            "poke",
            {
                "user_id": _s(d.sender_id),
                "target_id": _s(d.receiver_id),
                "group_id": _s(d.group_id),
            },
        )
    if isinstance(ev, FriendNudgeEvent):
        d = ev.data
        # 私聊场景下"被戳者"即为 bot 自身, 用 bot.self_id 补齐 target_id
        return MetaEvent(
            "poke",
            {
                "user_id": _s(d.user_id),
                "target_id": _s(bot.self_id),
            },
        )
    return None


# ---------------------------------------------------------------------------
# OneBot V12
# ---------------------------------------------------------------------------
def _ob12_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.onebot.v12.event import (
        GroupMemberDecreaseEvent,
        GroupMemberIncreaseEvent,
        GuildMemberDecreaseEvent,
        GuildMemberIncreaseEvent,
    )

    if isinstance(ev, GroupMemberIncreaseEvent):
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(ev.user_id),
                "group_id": _s(ev.group_id),
                "operator_id": _s(ev.operator_id),
            },
            bot_id="onebot_v12",
        )
    if isinstance(ev, GroupMemberDecreaseEvent):
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(ev.user_id),
                "group_id": _s(ev.group_id),
                "operator_id": _s(ev.operator_id),
            },
            bot_id="onebot_v12",
        )
    if isinstance(ev, GuildMemberIncreaseEvent):
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(ev.user_id),
                "group_id": _s(ev.guild_id),
                "operator_id": _s(ev.operator_id),
            },
            bot_id="onebot_v12",
        )
    if isinstance(ev, GuildMemberDecreaseEvent):
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(ev.user_id),
                "group_id": _s(ev.guild_id),
                "operator_id": _s(ev.operator_id),
            },
            bot_id="onebot_v12",
        )
    return None


# ---------------------------------------------------------------------------
# QQ 官方(频道)
# ---------------------------------------------------------------------------
def _qq_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.qq.event import (
        GuildMemberAddEvent,
        GuildMemberRemoveEvent,
    )

    if isinstance(ev, GuildMemberAddEvent):
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(ev.user.id if ev.user else ""),
                "group_id": _s(ev.guild_id),
                "operator_id": _s(ev.op_user_id),
            },
            bot_id="qqguild",
            user_type="group",
        )
    if isinstance(ev, GuildMemberRemoveEvent):
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(ev.user.id if ev.user else ""),
                "group_id": _s(ev.guild_id),
                "operator_id": _s(ev.op_user_id),
            },
            bot_id="qqguild",
            user_type="group",
        )
    return None


# ---------------------------------------------------------------------------
# Discord
# ---------------------------------------------------------------------------
def _discord_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.discord.event import (
        GuildMemberAddEvent,
        GuildMemberRemoveEvent,
    )

    if isinstance(ev, GuildMemberAddEvent):
        return MetaEvent(
            "user_join_group",
            {
                "user_id": _s(ev.user.id),  # type: ignore[attr-defined]
                "group_id": _s(ev.guild_id),
            },
        )
    if isinstance(ev, GuildMemberRemoveEvent):
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(ev.user.id),  # type: ignore[attr-defined]
                "group_id": _s(ev.guild_id),
            },
        )
    return None


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
def _telegram_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.telegram.event import (
        NewChatMemberEvent,
        LeftChatMemberEvent,
    )

    if isinstance(ev, NewChatMemberEvent):
        members = ev.new_chat_members or []
        user_id = _s(members[0].id) if members else ""
        return MetaEvent(
            "user_join_group",
            {"user_id": user_id, "group_id": _s(ev.chat.id)},
        )
    if isinstance(ev, LeftChatMemberEvent):
        return MetaEvent(
            "user_exit_group",
            {
                "user_id": _s(ev.left_chat_member.id),
                "group_id": _s(ev.chat.id),
            },
        )
    return None


# ---------------------------------------------------------------------------
# 飞书 Feishu(事件体为嵌套 detail, 用户 id 为 union_id/open_id 对象)
# ---------------------------------------------------------------------------
def _feishu_user_id(user_id_obj: Any) -> str:
    """飞书 UserId 对象优先取 union_id, 退而 open_id / user_id."""
    if user_id_obj is None:
        return ""
    return _s(user_id_obj.union_id or user_id_obj.open_id or user_id_obj.user_id)


def _feishu_to_meta(bot: Bot, ev: Event) -> Optional[MetaEvent]:
    from nonebot.adapters.feishu.event import (
        GroupMemberUserAddedEvent,
        GroupMemberUserDeletedEvent,
    )

    if isinstance(ev, (GroupMemberUserAddedEvent, GroupMemberUserDeletedEvent)):
        detail = ev.event
        users = detail.users or []
        user_id = _feishu_user_id(users[0].user_id) if users else ""
        name = "user_join_group" if isinstance(ev, GroupMemberUserAddedEvent) else "user_exit_group"
        return MetaEvent(
            name,
            {
                "user_id": user_id,
                "group_id": _s(detail.chat_id),
                "operator_id": _feishu_user_id(detail.operator_id),
            },
        )
    return None


# 适配器名 -> 映射函数; 名称取自 `bot.adapter.get_name()`
_META_MAPPERS: Dict[str, Callable[[Bot, Event], Optional[MetaEvent]]] = {
    "OneBot V11": _ob11_to_meta,
    "OneBot V12": _ob12_to_meta,
    "Milky": _milky_to_meta,
    "QQ": _qq_to_meta,
    "Discord": _discord_to_meta,
    "Telegram": _telegram_to_meta,
    "Feishu": _feishu_to_meta,
}


def build_meta_receive(bot: Bot, ev: Event, pm: int) -> Optional[MessageReceive]:
    """把平台 notice/request 事件转为 meta 上报包; 不支持的事件返回 None.

    pm 由调用方算好(含 SUPERUSER 判定)后传入. 顶层 user_id/group_id 从 meta data
    回读(与 core 回填口径一致), bot_id/user_type 优先用映射函数的显式覆盖。
    """
    mapper = _META_MAPPERS.get(bot.adapter.get_name())
    if mapper is None:
        return None

    result = mapper(bot, ev)
    if result is None:
        return None

    data = result.data
    group_id = data.get("group_id") or None
    user_id = data.get("user_id") or ""

    if result.bot_id:
        bot_id = result.bot_id
    else:
        bot_id = ev.__class__.__module__.split(".")[2]

    user_type: Literal["group", "direct", "channel", "sub_channel"]
    if result.user_type:
        user_type = result.user_type  # type: ignore[assignment]
    else:
        user_type = "group" if group_id else "direct"

    return MessageReceive(
        bot_id=bot_id,
        bot_self_id=str(bot.self_id),
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender={},
        content=[Message(f"meta-{result.event_name}", data)],
        msg_id="",
        user_pm=pm,
    )
