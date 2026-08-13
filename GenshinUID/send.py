"""GsCore MessageSend -> UniMessage.send."""

from __future__ import annotations

import tempfile
from typing import Protocol, runtime_checkable
from pathlib import Path

from nonebot import require
from nonebot.log import logger
from nonebot.adapters import Bot

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna.uniseg import (  # noqa: E402
    File,
    Target,
    Receipt,
    UniMessage,
)
from nonebot_plugin_alconna.uniseg.adapters import (  # noqa: E402
    alter_get_exporter,
)
from nonebot_plugin_alconna.uniseg.constraint import (  # noqa: E402
    SerializeFailed,
)

from .extras import ban_user, append_qq_markdown
from .models import Message, MessageSend
from .convert import (
    SendSpecials,
    gs_to_uni,
    nodes_to_reference,
    node_to_unimessages,
)
from .identity import build_send_target

RecallId = str | list[str] | None


@runtime_checkable
class _HasMessageId(Protocol):
    message_id: object


@runtime_checkable
class _HasMessageSeq(Protocol):
    message_seq: object


@runtime_checkable
class _HasId(Protocol):
    id: object


@runtime_checkable
class _HasImSeq(Protocol):
    im_seq: object


def _materialize_files(uni: UniMessage) -> list[Path]:
    temps: list[Path] = []
    for i, seg in enumerate(uni):
        if not isinstance(seg, File) or not seg.raw or seg.path:
            continue
        suffix = Path(seg.name).suffix or ".bin"
        handle, name = tempfile.mkstemp(prefix="gsuid_", suffix=suffix)
        path = Path(name)
        with open(handle, "wb") as fp:
            fp.write(seg.raw_bytes)
        uni[i] = File(path=path, name=seg.name)
        temps.append(path)
    return temps


def _cleanup_temps(paths: list[Path]) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


def mid_to_str(mid: object) -> str | None:
    if mid is None:
        return None
    if isinstance(mid, (str, int)):
        text = str(mid)
        return text if text else None
    if isinstance(mid, dict):
        if "message_id" in mid:
            return str(mid["message_id"])
        if "message_seq" in mid:
            return str(mid["message_seq"])
        if "id" in mid:
            return str(mid["id"])
        if "im_seq" in mid:
            return str(mid["im_seq"])
        if "msg_id" in mid:
            return str(mid["msg_id"])
        if "data" in mid:
            return mid_to_str(mid["data"])
        if "result" in mid:
            return mid_to_str(mid["result"])
        return None
    if isinstance(mid, list):
        if not mid:
            return None
        return mid_to_str(mid[0])
    if isinstance(mid, _HasMessageId):
        return str(mid.message_id)
    if isinstance(mid, _HasMessageSeq):
        return str(mid.message_seq)
    if isinstance(mid, _HasImSeq):
        return str(mid.im_seq)
    if isinstance(mid, _HasId):
        return str(mid.id)
    return None


def collect_ids(res: object) -> list[str]:
    if res is None:
        return []
    if isinstance(res, list):
        ids: list[str] = []
        for item in res:
            found = mid_to_str(item)
            if found is not None:
                ids.append(found)
        return ids
    found = mid_to_str(res)
    return [found] if found is not None else []


def ids_from_receipt(receipt: Receipt) -> list[str]:
    return collect_ids(receipt.msg_ids)


def pack_recall(ids: list[str]) -> RecallId:
    if not ids:
        return None
    if len(ids) == 1:
        return ids[0]
    return ids


async def _send_uni(
    bot: Bot,
    target: Target,
    uni: UniMessage,
    specials: SendSpecials,
    bot_id: str,
) -> list[str]:
    if not uni and not specials.has_qq_markdown():
        return []
    payload = uni if uni else UniMessage()
    temps = _materialize_files(payload)
    try:
        if bot_id in {"qqguild", "qqgroup"} and specials.has_qq_markdown():
            exporter = alter_get_exporter(bot.adapter.get_name())
            if exporter is None:
                raise SerializeFailed(bot.adapter.get_name())
            exported = await payload.export(bot)
            exported = append_qq_markdown(exported, specials)
            res = await exporter.send_to(target, bot, exported)
            return collect_ids(res)
        receipt = await payload.send(target, bot)
        return ids_from_receipt(receipt)
    except SerializeFailed as exc:
        logger.warning(f"[gscore] UniMessage 发送失败({bot_id}): {exc}")
        return []
    finally:
        _cleanup_temps(temps)


async def send_gs(bot: Bot, msg: MessageSend) -> RecallId:
    if msg.target_id is None or msg.content is None:
        return None

    uni, specials = gs_to_uni(msg.content)
    for ban in specials.bans:
        await ban_user(bot, msg.bot_id, ban)

    target = build_send_target(
        bot,
        msg.bot_id,
        msg.target_id,
        msg.target_type,
        msg.msg_id,
        specials.group_id,
    )

    ids: list[str] = []
    if specials.node_items:
        if msg.bot_id == "onebot":
            forward = UniMessage(nodes_to_reference(specials.node_items))
            ids.extend(await _send_uni(bot, target, forward, specials, msg.bot_id))
        else:
            for node_uni in node_to_unimessages(specials.node_items):
                ids.extend(await _send_uni(bot, target, node_uni, specials, msg.bot_id))

    if uni or specials.has_qq_markdown():
        ids.extend(await _send_uni(bot, target, uni, specials, msg.bot_id))
    return pack_recall(ids)


def is_log_packet(msg: MessageSend, route_bot_id: str) -> bool:
    if msg.bot_id != route_bot_id or not msg.content:
        return False
    first = msg.content[0]
    return bool(first.type and first.type.startswith("log"))


def handle_log_packet(msg: MessageSend) -> None:
    if not msg.content:
        return
    first = msg.content[0]
    if first.type is None:
        return
    level = first.type.split("_")[-1].lower()
    if level == "info":
        logger.info(first.data)
    elif level == "warning":
        logger.warning(first.data)
    elif level == "error":
        logger.error(first.data)
    elif level == "success":
        logger.success(first.data)
    else:
        logger.info(first.data)


def is_delete_packet(content: list[Message] | None) -> bool:
    return bool(content and len(content) == 1 and content[0].type == "excute_delete_message")


async def handle_delete_packet(bot: Bot, msg: MessageSend) -> None:
    if not msg.content:
        return
    data = msg.content[0].data
    if not isinstance(data, dict) or "message_id" not in data:
        return
    mid = str(data["message_id"])
    target = build_send_target(
        bot,
        msg.bot_id,
        msg.target_id or "",
        msg.target_type,
        msg.msg_id,
        "",
    )
    exporter = alter_get_exporter(bot.adapter.get_name())
    if exporter is None:
        logger.warning(f"[gscore] 平台 {msg.bot_id} 暂不支持撤回消息")
        return
    await exporter.recall(mid, bot, target)
