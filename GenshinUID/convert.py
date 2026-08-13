"""GsCore Message 段 <-> Alconna UniMessage."""

from __future__ import annotations

import base64
from io import BytesIO
from typing import Iterable
from pathlib import Path
from dataclasses import field, dataclass

from nonebot import require, get_driver
from nonebot.log import logger
from nonebot.adapters import Bot, Message as NBMessage

require("nonebot_plugin_alconna")

from nonebot_plugin_alconna.uniseg import (  # noqa: E402
    At,
    File,
    Text,
    Audio,
    Image,
    Reply,
    Video,
    Voice,
    Button,
    RefNode,
    Keyboard,
    Reference,
    CustomNode,
    UniMessage,
)
from nonebot_plugin_alconna.uniseg.segment import Media  # noqa: E402

from .tools import get_bytes_from_base64_str
from .types import NodeItem, BanPayload, ButtonPayload, TemplateMarkdown
from .models import Message

_LINK = "link://"
_B64 = "base64://"
_NODE_MARK = "[合并转发]"
_NODE_MAX_DEPTH = 3


@dataclass
class SendSpecials:
    markdown: str = ""
    template_markdown: TemplateMarkdown | None = None
    group_id: str = ""
    bans: list[BanPayload] = field(default_factory=list)
    node_items: list[NodeItem | Message] = field(default_factory=list)

    def has_qq_markdown(self) -> bool:
        return bool(self.markdown or self.template_markdown)


def _strip_command_start(text: str, starts: Iterable[str], index: int) -> str:
    if index not in (0, 1):
        return text
    stripped = text.strip()
    for word in starts:
        if word and stripped.startswith(word):
            return stripped[len(word) :]
    return text


def _media_to_data(seg: Media, *, prefer_url: bool = True) -> str:
    if prefer_url and seg.url:
        return seg.url
    if seg.raw:
        encoded = base64.b64encode(seg.raw_bytes).decode("utf-8")
        return f"{_B64}{encoded}"
    if seg.path:
        raw = Path(seg.path).read_bytes()
        encoded = base64.b64encode(raw).decode("utf-8")
        return f"{_B64}{encoded}"
    if seg.url:
        return seg.url
    if seg.id:
        return str(seg.id)
    return ""


def _reply_text(seg: Reply) -> str:
    msg = seg.msg
    if msg is None:
        return ""
    if isinstance(msg, str):
        return msg
    if isinstance(msg, UniMessage):
        return msg.extract_plain_text()
    if isinstance(msg, NBMessage):
        return msg.extract_plain_text()
    return ""


async def uni_to_gs(
    uni: UniMessage,
    bot: Bot,
    command_start: Iterable[str],
) -> list[Message]:
    result: list[Message] = []
    text_index = 0

    for seg in uni:
        if isinstance(seg, Text):
            data = _strip_command_start(seg.text, command_start, text_index)
            result.append(Message("text", data))
            text_index += 1
        elif isinstance(seg, At):
            result.append(Message("at", str(seg.target)))
        elif isinstance(seg, Image):
            data = _media_to_data(seg)
            if data:
                result.append(Message("image", data))
        elif isinstance(seg, Reply):
            result.extend(await _reply_to_gs(seg, bot))
        elif isinstance(seg, Reference):
            result.append(Message("node", await _reference_to_items(seg, bot)))
        elif isinstance(seg, (Voice, Audio)):
            data = _media_to_data(seg, prefer_url=False)
            if data:
                result.append(Message("record", data))
        elif isinstance(seg, Video):
            data = _media_to_data(seg, prefer_url=False)
            if data:
                result.append(Message("video", data))
        elif isinstance(seg, File):
            payload = _media_to_data(seg)
            if payload:
                result.append(Message("file", f"{seg.name}|{payload}"))
    return result


def _quoted_message(seg: Reply) -> UniMessage | NBMessage | None:
    raw = seg.msg
    if isinstance(raw, UniMessage):
        return raw
    if isinstance(raw, NBMessage):
        return raw
    origin = seg.origin
    if isinstance(origin, (UniMessage, NBMessage)):
        return origin
    return None


async def _plain_uni_to_gs(
    uni: UniMessage,
    bot: Bot,
    depth: int,
    seen: set[str],
) -> list[Message]:
    """转发节点内的段；遇到内层合并转发按深度继续展开."""
    result: list[Message] = []
    for seg in uni:
        if isinstance(seg, Text):
            result.append(Message("text", seg.text))
        elif isinstance(seg, At):
            result.append(Message("at", str(seg.target)))
        elif isinstance(seg, Image):
            data = _media_to_data(seg)
            if data:
                result.append(Message("image", data))
        elif isinstance(seg, (Voice, Audio)):
            data = _media_to_data(seg, prefer_url=False)
            if data:
                result.append(Message("record", data))
        elif isinstance(seg, Video):
            data = _media_to_data(seg, prefer_url=False)
            if data:
                result.append(Message("video", data))
        elif isinstance(seg, File):
            payload = _media_to_data(seg)
            if payload:
                result.append(Message("file", f"{seg.name}|{payload}"))
        elif isinstance(seg, Reference):
            result.append(Message("text", _NODE_MARK))
            result.extend(await _reference_to_items(seg, bot, depth + 1, seen))
    return result


def _node_preview(items: list[Message]) -> str:
    lines: list[str] = [_NODE_MARK]
    for item in items:
        if item.type == "text" and item.data is not None:
            text = str(item.data).strip()
            if text:
                lines.append(text)
        elif item.type == "image":
            lines.append("[图片]")
        elif item.type == "record":
            lines.append("[语音]")
        elif item.type == "video":
            lines.append("[视频]")
        elif item.type == "file":
            lines.append("[文件]")
        elif item.type == "node":
            lines.append(_NODE_MARK)
    return "\n".join(lines)


async def _custom_node_to_gs(
    node: CustomNode,
    bot: Bot,
    depth: int,
    seen: set[str],
) -> list[Message]:
    items: list[Message] = []
    if node.name:
        items.append(Message("text", f"{node.name}:"))
    content = node.content
    if isinstance(content, str):
        if content:
            items.append(Message("text", content))
        return items
    if isinstance(content, UniMessage):
        items.extend(await _plain_uni_to_gs(content, bot, depth, seen))
        return items
    if isinstance(content, list):
        uni = UniMessage()
        for child in content:
            if isinstance(child, str):
                uni.append(Text(child))
            else:
                uni.append(child)
        items.extend(await _plain_uni_to_gs(uni, bot, depth, seen))
        return items
    if isinstance(content, NBMessage):
        items.extend(await _plain_uni_to_gs(UniMessage.of(content, bot=bot), bot, depth, seen))
    return items


def _forward_id_from_dict(data: dict[str, object]) -> str:
    if "id" in data and data["id"] is not None:
        return str(data["id"])
    if "message_id" in data and data["message_id"] is not None:
        return str(data["message_id"])
    return ""


async def _ob_dict_segs_to_gs(
    segs: list[object],
    bot: Bot,
    depth: int,
    seen: set[str],
) -> list[Message]:
    items: list[Message] = []
    for seg in segs:
        if not isinstance(seg, dict):
            continue
        typ = str(seg["type"]) if "type" in seg and seg["type"] is not None else ""
        data = seg["data"] if "data" in seg and isinstance(seg["data"], dict) else {}
        if typ == "text" and "text" in data:
            items.append(Message("text", str(data["text"])))
        elif typ == "image":
            url = data["url"] if "url" in data else (data["file"] if "file" in data else "")
            if url:
                items.append(Message("image", str(url)))
        elif typ == "at" and "qq" in data:
            items.append(Message("at", str(data["qq"])))
        elif typ in {"forward", "forward_msg"}:
            fid = _forward_id_from_dict(data)
            if fid:
                items.append(Message("text", _NODE_MARK))
                items.extend(await _fetch_forward_items(bot, fid, depth + 1, seen))
            else:
                items.append(Message("text", _NODE_MARK))
        elif typ == "record":
            url = data["url"] if "url" in data else (data["file"] if "file" in data else "")
            if url:
                items.append(Message("record", str(url)))
        elif typ == "video":
            url = data["url"] if "url" in data else (data["file"] if "file" in data else "")
            if url:
                items.append(Message("video", str(url)))
    return items


async def _parse_forward_payload(
    raw: object,
    bot: Bot,
    depth: int,
    seen: set[str],
) -> list[Message]:
    messages: object
    if isinstance(raw, dict) and "messages" in raw:
        messages = raw["messages"]
    else:
        messages = raw
    if not isinstance(messages, list):
        return [Message("text", _NODE_MARK)]

    items: list[Message] = []
    for entry in messages:
        if not isinstance(entry, dict):
            continue
        payload = entry
        if "type" in entry and entry["type"] == "node" and "data" in entry and isinstance(entry["data"], dict):
            payload = entry["data"]

        nickname = ""
        if "sender" in payload and isinstance(payload["sender"], dict):
            sender = payload["sender"]
            if "nickname" in sender and sender["nickname"]:
                nickname = str(sender["nickname"])
        elif "name" in payload and payload["name"]:
            nickname = str(payload["name"])
        if nickname:
            items.append(Message("text", f"{nickname}:"))

        content: object = None
        if "content" in payload:
            content = payload["content"]
        elif "message" in payload:
            content = payload["message"]

        if isinstance(content, str):
            if content:
                items.append(Message("text", content))
        elif isinstance(content, NBMessage):
            items.extend(await _plain_uni_to_gs(UniMessage.of(content, bot=bot), bot, depth, seen))
        elif isinstance(content, list):
            items.extend(await _ob_dict_segs_to_gs(content, bot, depth, seen))
    return items if items else [Message("text", _NODE_MARK)]


async def _fetch_forward_items(
    bot: Bot,
    forward_id: str,
    depth: int = 0,
    seen: set[str] | None = None,
) -> list[Message]:
    visited = seen if seen is not None else set()
    if not forward_id or forward_id in visited or depth >= _NODE_MAX_DEPTH:
        return [Message("text", _NODE_MARK)]
    visited.add(forward_id)
    name = bot.adapter.get_name()
    if name == "OneBot V11":
        from nonebot.exception import ActionFailed

        try:
            raw = await bot.call_api("get_forward_msg", id=forward_id)
        except ActionFailed:
            raw = await bot.call_api("get_forward_msg", message_id=forward_id)
        return await _parse_forward_payload(raw, bot, depth, visited)
    if name == "Milky":
        from nonebot.adapters.milky.bot import Bot as MilkyBot

        if isinstance(bot, MilkyBot):
            forwarded = await bot.get_forwarded_messages(forward_id=forward_id)
            items: list[Message] = []
            for msg in forwarded:
                if msg.sender_name:
                    items.append(Message("text", f"{msg.sender_name}:"))
                items.extend(await _plain_uni_to_gs(UniMessage.of(msg.message, bot=bot), bot, depth, visited))
            return items if items else [Message("text", _NODE_MARK)]
    return [Message("text", _NODE_MARK)]


async def _reference_to_items(
    seg: Reference,
    bot: Bot,
    depth: int = 0,
    seen: set[str] | None = None,
) -> list[Message]:
    visited = seen if seen is not None else set()
    if depth >= _NODE_MAX_DEPTH:
        return [Message("text", _NODE_MARK)]
    items: list[Message] = []
    for child in seg.children:
        if isinstance(child, CustomNode):
            items.extend(await _custom_node_to_gs(child, bot, depth, visited))
        elif isinstance(child, RefNode):
            items.append(Message("text", _NODE_MARK))
    if items:
        return items
    if seg.id:
        try:
            return await _fetch_forward_items(bot, str(seg.id), depth, visited)
        except Exception as exc:
            logger.warning(f"[gsuid] 拉取合并转发失败: {exc}")
            return [Message("text", _NODE_MARK)]
    return [Message("text", _NODE_MARK)]


async def _reply_to_gs(seg: Reply, bot: Bot) -> list[Message]:
    result: list[Message] = [Message("reply_id", str(seg.id))]
    reply_text = _reply_text(seg)
    images: list[Message] = []
    nodes: list[Message] = []

    raw = _quoted_message(seg)
    if raw is not None:
        reply_uni = raw if isinstance(raw, UniMessage) else UniMessage.of(raw, bot=bot)
        for rseg in reply_uni:
            if isinstance(rseg, Image):
                data = _media_to_data(rseg)
                if data:
                    images.append(Message("image", data))
            elif isinstance(rseg, Reference):
                items = await _reference_to_items(rseg, bot)
                nodes.append(Message("node", items))
                if not reply_text or _NODE_MARK not in reply_text:
                    preview = _node_preview(items)
                    reply_text = preview if not reply_text else f"{_NODE_MARK}\n{reply_text}"

    result.append(Message("reply", reply_text))
    result.extend(images)
    result.extend(nodes)
    return result


def _looks_like_b64(data: str) -> bool:
    if len(data) < 8 or len(data) % 4 != 0:
        return False
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    return all(ch in allowed for ch in data)


def _decode_media(data: str) -> tuple[bytes | None, str | None]:
    if data.startswith(_LINK):
        return None, data[len(_LINK) :]
    if data.startswith(_B64):
        return get_bytes_from_base64_str(data), None
    if data.startswith("http://") or data.startswith("https://"):
        return None, data
    if _looks_like_b64(data):
        return get_bytes_from_base64_str(data), None
    return None, data


def _image_from_gs(data: str) -> Image:
    raw, url = _decode_media(data)
    if raw is not None:
        from PIL import Image as PILImage

        with PILImage.open(BytesIO(raw)) as img:
            width, height = img.size
        return Image(raw=raw, width=width, height=height)
    return Image(url=url)


def _file_from_gs(data: str) -> File:
    if "|" in data:
        name, content = data.split("|", 1)
    else:
        name, content = "file.bin", data
    raw, url = _decode_media(content)
    if raw is not None:
        return File(raw=raw, name=name)
    return File(url=url, name=name)


def _button_flag(action: int) -> tuple[str, str | None, str | None]:
    """返回 (flag, url, text). action: 0 跳转 / 1 回调 / 2 命令 / -1 自适应."""
    if action == 0:
        return "link", None, None
    if action == 1:
        return "action", None, None
    return "enter", None, None


def _gs_button(btn: ButtonPayload) -> Button:
    action = btn["action"] if "action" in btn else -1
    data = btn["data"] if "data" in btn else ""
    text = btn["text"] if "text" in btn else ""
    pressed = btn["pressed_text"] if "pressed_text" in btn else None
    style = "primary" if ("style" in btn and btn["style"] == 1) else "secondary"
    flag, url, input_text = _button_flag(action)
    if flag == "link":
        return Button(
            flag="link",
            label=text,
            url=data,
            clicked_label=pressed,
            style=style,
        )
    if flag == "action":
        return Button(
            flag="action",
            label=text,
            id=data,
            text=data,
            clicked_label=pressed,
            style=style,
        )
    return Button(
        flag="enter",
        label=text,
        text=data,
        clicked_label=pressed,
        style=style,
    )


def _buttons_to_keyboards(
    buttons: list[ButtonPayload] | list[list[ButtonPayload]],
) -> list[Keyboard]:
    keyboards: list[Keyboard] = []
    flat: list[Button] = []
    for item in buttons:
        if isinstance(item, dict):
            flat.append(_gs_button(item))
            if len(flat) >= 2:
                keyboards.append(Keyboard(buttons=flat))
                flat = []
        elif isinstance(item, list):
            keyboards.append(Keyboard(buttons=[_gs_button(b) for b in item]))
    if flat:
        keyboards.append(Keyboard(buttons=flat))
    return keyboards


def _one_gs_to_seg(
    gs: Message,
) -> Text | Image | At | Reply | Voice | Video | File | None:
    if not gs.type or gs.data is None:
        return None
    if gs.type == "text":
        return Text(str(gs.data))
    if gs.type == "image":
        return _image_from_gs(str(gs.data))
    if gs.type == "at":
        return At("user", str(gs.data))
    if gs.type in {"reply", "reply_id"}:
        return Reply(str(gs.data))
    if gs.type == "record":
        raw, url = _decode_media(str(gs.data))
        if raw is not None:
            return Voice(raw=raw)
        return Voice(url=url)
    if gs.type == "video":
        raw, url = _decode_media(str(gs.data))
        if raw is not None:
            return Video(raw=raw)
        return Video(url=url)
    if gs.type == "file":
        return _file_from_gs(str(gs.data))
    return None


def _node_to_uni(item: NodeItem | Message) -> UniMessage:
    if isinstance(item, Message):
        gs = item
    else:
        gs = Message(
            type=item["type"] if "type" in item else None,
            data=item["data"] if "data" in item else None,
        )
    seg = _one_gs_to_seg(gs)
    if seg is None:
        if gs.data is not None:
            return UniMessage(str(gs.data))
        return UniMessage()
    return UniMessage(seg)


def gs_to_uni(content: list[Message]) -> tuple[UniMessage, SendSpecials]:
    uni = UniMessage()
    specials = SendSpecials()

    for gs in content:
        if not gs.type or gs.data is None:
            continue
        if gs.type == "buttons":
            if isinstance(gs.data, list):
                for kb in _buttons_to_keyboards(gs.data):
                    uni.append(kb)
            continue
        if gs.type == "markdown":
            specials.markdown = str(gs.data).replace(_LINK, "")
            continue
        if gs.type == "template_markdown":
            if isinstance(gs.data, dict) and "template_id" in gs.data:
                para = gs.data["para"] if "para" in gs.data else {}
                specials.template_markdown = {
                    "template_id": str(gs.data["template_id"]),
                    "para": para if isinstance(para, dict) else {},
                }
            continue
        if gs.type == "template_buttons":
            uni.append(Keyboard(id=str(gs.data)))
            continue
        if gs.type == "group":
            specials.group_id = str(gs.data)
            continue
        if gs.type == "excute_ban_user":
            if isinstance(gs.data, dict) and "user_id" in gs.data:
                ban: BanPayload = {
                    "user_id": str(gs.data["user_id"]),
                    "group_id": (str(gs.data["group_id"]) if "group_id" in gs.data else ""),
                    "duration": (gs.data["duration"] if "duration" in gs.data else 0),
                }
                specials.bans.append(ban)
            continue
        if gs.type == "node":
            if isinstance(gs.data, list):
                specials.node_items = gs.data
            continue
        if gs.type == "image_size":
            continue
        seg = _one_gs_to_seg(gs)
        if seg is not None:
            uni.append(seg)
        else:
            logger.debug(f"[gsuid] 忽略未知下发段: {gs.type}")

    return uni, specials


def nodes_to_reference(items: list[NodeItem | Message]) -> Reference:
    nodes: list[CustomNode] = []
    for item in items:
        nodes.append(
            CustomNode(
                uid="2854196310",
                name="小助手",
                content=_node_to_uni(item),
            )
        )
    return Reference(nodes=nodes)


def node_to_unimessages(items: list[NodeItem | Message]) -> list[UniMessage]:
    return [_node_to_uni(item) for item in items]


def command_starts() -> set[str]:
    starts = set(get_driver().config.command_start)
    starts.discard("")
    return starts
