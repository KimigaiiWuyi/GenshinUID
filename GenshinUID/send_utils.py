import json
import time
import uuid
import base64
from io import BytesIO
from typing import Dict, List, Union, Optional
from pathlib import Path
from collections import OrderedDict

from PIL import Image
from nonebot.log import logger
from nonebot.adapters import Bot

from .tools import (
    to_json,
    del_file,
    store_file,
    download_image,
    get_bytes_from_base64_str,
)
from .utils import _kb, _dc_kb, _tg_kb
from .models import Message as GsMessage

msg_id_seq = OrderedDict()


async def onebot_send(
    bot: Bot,
    content: Optional[List[GsMessage]],
    target_id: Optional[str],
    target_type: Optional[str],
) -> Optional[Union[str, List[str]]]:
    if target_id is None or content is None:
        return None
    _target_id = int(target_id)

    from nonebot.adapters.onebot.v11 import Bot, MessageSegment

    assert isinstance(bot, Bot)

    # 收集本次产生的平台出站消息id(可能含转发气泡+正文气泡), 供 recv_msg 回传 core
    recall_ids: List[str] = []

    async def to_file(file: str):
        file_name, file_content = file.split("|")
        if target_type == "group":
            await bot.call_api(
                "upload_group_file",
                file=f"base64://{file_content}",
                name=file_name,
                group_id=_target_id,
            )
        else:
            await bot.call_api(
                "upload_private_file",
                file=f"base64://{file_content}",
                name=file_name,
                user_id=_target_id,
            )

    async def to_msg(gsmsgs: List[GsMessage]) -> List[MessageSegment]:
        message = []
        for _c in gsmsgs:
            if _c.data:
                if _c.type == "text":
                    message.append(MessageSegment.text(_c.data))
                elif _c.type == "image":
                    message.append(
                        MessageSegment.image(
                            _c.data.replace(
                                "link://",
                                "",
                            )
                        )
                    )
                elif _c.type == "node":
                    _temp_data = []
                    for i in _c.data:
                        _temp_data.append(GsMessage(**i))

                    send_forward = [
                        to_json(
                            await to_msg([_msg]),
                            "小助手",
                            str(2854196310),
                        )
                        for _msg in _temp_data
                    ]

                    await _send_node(send_forward)
                elif _c.type == "file":
                    await to_file(_c.data)
                elif _c.type == "at":
                    message.append(MessageSegment.at(_c.data))
                elif _c.type == "record":
                    message.append(MessageSegment.record(get_bytes_from_base64_str(_c.data)))
                elif _c.type == "video":
                    message.append(MessageSegment.video(get_bytes_from_base64_str(_c.data)))
                elif _c.type == "excute_ban_user":
                    user_id = _c.data.get("user_id", None)
                    group_id = _c.data.get("group_id", None)
                    duration = _c.data.get("duration", None)
                    if user_id is not None and group_id is not None:
                        if isinstance(duration, int) or (isinstance(duration, str) and duration.isdigit()):
                            await bot.set_group_ban(
                                group_id=int(group_id),
                                user_id=int(user_id),
                                duration=int(duration),
                            )
        return message

    async def _send_node(messages):
        if target_type == "group":
            ret = await bot.call_api(
                "send_group_forward_msg",
                group_id=_target_id,
                messages=messages,
            )
        else:
            ret = await bot.call_api(
                "send_private_forward_msg",
                user_id=_target_id,
                messages=messages,
            )
        # 合并转发本身是一个气泡, 协议返回 message_id(部分实现还含 forward_id)
        if isinstance(ret, dict) and ret.get("message_id") is not None:
            recall_ids.append(str(ret["message_id"]))

    result_msg = await to_msg(content)
    if result_msg:
        if target_type == "group":
            recall = await bot.call_api(
                "send_group_msg",
                group_id=_target_id,
                message=result_msg,
            )
        else:
            recall = await bot.call_api(
                "send_private_msg",
                user_id=_target_id,
                message=result_msg,
            )
        if isinstance(recall, dict) and recall.get("message_id") is not None:
            recall_ids.append(str(recall["message_id"]))

    # 无id->None; 单气泡->str; 转发+正文等多气泡->List[str], 由 core flatten
    if not recall_ids:
        return None
    return recall_ids[0] if len(recall_ids) == 1 else recall_ids


async def heybox_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    at_list: Optional[List[str]],
    record: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
) -> Optional[str]:
    from nonebot.adapters.heybox.bot import Bot
    from nonebot.adapters.heybox.message import Message, MessageSegment

    assert isinstance(bot, Bot)

    def add_image(image: str):
        image_name = uuid.uuid4().hex + ".jpg"
        if image.startswith("link://"):
            img_url = image.replace("link://", "")
            return MessageSegment.image(img_url, 720, 1280)
        else:
            img_bytes = base64.b64decode(image.replace("base64://", ""))
            # 获取图片宽高
            with Image.open(BytesIO(img_bytes)) as img:
                width, height = img.size

            return MessageSegment.local_image(img_bytes, width, height, image_name)

    def add_text(content: str):
        return MessageSegment.text(content)

    if target_id:
        result_msg: Message = Message()
        channel_id, room_id = target_id.split("-")

        if content:
            result_msg.append(add_text(content))

        if image:
            result_msg.append(add_image(image))

        if record:
            logger.warning("[gscore] Heybox暂不支持发送语音消息")
            return

        if at_list and target_type == "group":
            for at in at_list:
                result_msg += MessageSegment.mention(at)

        if file:
            logger.warning("[gscore] Heybox暂不支持发送文件消息")
            return

        if node:
            for _msg in node:
                if _msg["type"] == "image":
                    result_msg.append(add_image(_msg["data"]))
                elif _msg["type"] == "text":
                    result_msg.append(add_text(_msg["data"]))
                elif _msg["type"] == "at":
                    result_msg.append(MessageSegment.mention(_msg["data"]))

        print(result_msg)
        res = await bot.send_to_channel(
            room_id,
            channel_id,
            result_msg,
            msg_id,
        )
        # heybox 适配器未对发送回执建模, 尽力从原始返回中提取消息id
        if isinstance(res, dict):
            _result = res.get("result") or {}
            _mid = _result.get("im_seq") or _result.get("msg_id") or res.get("im_seq") or res.get("msg_id")
            if _mid is not None:
                return str(_mid)
    return None


async def discord_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    record: Optional[str],
    video: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
    group_id: Optional[str],
) -> Optional[Union[str, List[str]]]:
    from nonebot.adapters.discord import Bot, Message, MessageSegment
    from nonebot.adapters.discord.api import ActionRow

    assert isinstance(bot, Bot)

    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        if group_id:
            message = Message()
            if image:
                img_bytes = base64.b64decode(image.replace("base64://", ""))
                message.append(MessageSegment.attachment("temp.jpg", content=img_bytes))
            if content:
                message.append(MessageSegment.text(content))

            if record:
                message.append(MessageSegment.attachment("temp.mp3", content=get_bytes_from_base64_str(record)))

            if video:
                message.append(MessageSegment.attachment("temp.mp4", content=get_bytes_from_base64_str(video)))

            if at_list and target_type == "group":
                for at in at_list:
                    message.append(MessageSegment.mention_user(int(at)))

            if markdown:
                logger.warning("[gscore] discord暂不支持发送markdown消息")
            if buttons:
                bt = []
                for button in buttons:
                    if isinstance(button, Dict):
                        bt.append(_dc_kb(button))
                        if len(bt) >= 2:
                            message.append(MessageSegment.component(ActionRow(components=bt)))
                            bt = []
                    if isinstance(button, List):
                        _t = []
                        for i in button:
                            _t.append(_dc_kb(i))
                        else:
                            message.append(MessageSegment.component(ActionRow(components=_t)))
                            _t = []

            await bot.call_api("trigger_typing_indicator", channel_id=group_id)
            ret = await bot.send_to(
                channel_id=int(group_id),
                message=message,
            )
            # discord 发送后返回 MessageGet, 其 id 即消息id
            return str(ret.id)
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                image = _msg["data"]
                content = None
            else:
                image = None
                content = _msg["data"]
            _r = await _send(content, image)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id


async def guild_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    template_markdown: Optional[Dict],
    template_buttons: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
    guild_id: Optional[str],
) -> Optional[Union[str, List[str]]]:
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.models import (
        MessageKeyboard,
        MessageMarkdown,
        MessageMarkdownParams,
    )
    from nonebot.adapters.qq.message import Message, MessageSegment
    from nonebot.adapters.qq.exception import ActionFailed

    assert isinstance(bot, qqbot)

    if target_id is None:
        return None

    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        message = Message()
        if image:
            if image.startswith("link://"):
                message.append(MessageSegment.image(image.replace("link://", "")))
            else:
                img_bytes = base64.b64decode(image.replace("base64://", ""))
                message.append(MessageSegment.file_image(img_bytes))
        if content:
            message.append(MessageSegment.text(content))
            if at_list and target_type == "group":
                for at in at_list:
                    message.append(MessageSegment.mention_user(at))
        if template_markdown:
            message.append(
                MessageSegment.markdown(
                    MessageMarkdown(
                        custom_template_id=template_markdown["template_id"],
                        params=[
                            MessageMarkdownParams(
                                key=key,
                                values=[template_markdown["para"][key]],
                            )
                            for key in template_markdown["para"]
                        ],
                    )
                )
            )
        elif markdown:
            _markdown = markdown.replace("link://", "")
            message.append(MessageSegment.markdown(_markdown))
        if template_buttons:
            message.append(MessageSegment.keyboard(MessageKeyboard(id=template_buttons)))
        elif buttons:
            message.append(MessageSegment.keyboard(_kb(buttons)))

        ret = None
        if target_type == "group":
            ret = await bot.send_to_channel(
                channel_id=str(target_id),
                message=message,
                msg_id=msg_id,
            )
        else:
            try:
                ret = await bot.send_to_dms(
                    guild_id=str(guild_id),
                    message=message,
                    msg_id=msg_id,
                )
            except ActionFailed:
                dms = await bot.post_dms(
                    recipient_id=str(target_id),
                    source_guild_id=str(guild_id),
                )
                if dms.guild_id:
                    ret = await bot.send_to_dms(
                        guild_id=dms.guild_id,
                        message=message,
                        msg_id=msg_id,
                    )
        # qq 频道发送后返回 GuildMessage, 其 id 即消息id
        if ret is not None:
            return str(ret.id)
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                image = _msg["data"]
                content = None
            else:
                image = None
                content = _msg["data"]
            _r = await _send(content, image)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id


async def group_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    template_markdown: Optional[Dict],
    template_buttons: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
) -> Optional[Union[str, List[str]]]:
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.models import (
        MessageKeyboard,
        MessageMarkdown,
        MessageMarkdownParams,
        PostC2CMessagesReturn,
        PostGroupMessagesReturn,
    )
    from nonebot.adapters.qq.message import Message, MessageSegment

    assert isinstance(bot, qqbot)
    assert isinstance(target_id, str)

    async def _send(text: Optional[str], img: Optional[str], mid: Optional[str]) -> Optional[str]:
        message = Message()
        if img:
            if img.startswith("link://"):
                _img = img.replace("link://", "")
                message.append(MessageSegment.image(_img))
            else:
                message.append(MessageSegment.file_image(base64.b64decode(img.replace("base64://", ""))))

        if text:
            message.append(MessageSegment.text(text))

        if template_markdown:
            message.append(
                MessageSegment.markdown(
                    MessageMarkdown(
                        custom_template_id=template_markdown["template_id"],
                        params=[
                            MessageMarkdownParams(
                                key=key,
                                values=[template_markdown["para"][key]],
                            )
                            for key in template_markdown["para"]
                        ],
                    )
                )
            )
        elif markdown:
            _markdown = markdown.replace("link://", "")
            message.append(MessageSegment.markdown(_markdown))
        if template_buttons:
            message.append(MessageSegment.keyboard(MessageKeyboard(id=template_buttons)))
        elif buttons:
            message.append(MessageSegment.keyboard(_kb(buttons)))

        if mid is None:
            msg_seq = None
        else:
            msg_seq = msg_id_seq[mid]

        if target_type == "group":
            ret = await bot.send_to_group(
                group_openid=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
                msg_seq=msg_seq,
            )
        else:
            ret = await bot.send_to_c2c(
                openid=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
                msg_seq=msg_seq,
            )

        msg_id_seq[mid] += 1

        # qq 群/c2c 发送后返回 PostGroup/C2CMessagesReturn, 其 id 即消息id
        if isinstance(ret, (PostGroupMessagesReturn, PostC2CMessagesReturn)) and ret.id is not None:
            return str(ret.id)
        return None

    if msg_id not in msg_id_seq:
        msg_id_seq[msg_id] = 1

    if len(msg_id_seq) >= 30:
        oldest_key = next(iter(msg_id_seq))
        del msg_id_seq[oldest_key]

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                _r = await _send(None, _msg["data"], msg_id)
            elif _msg["type"] == "text":
                _r = await _send(_msg["data"], None, msg_id)
            else:
                _r = None
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image, msg_id)
    return recall_id


async def telegram_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    record: Optional[str],
    video: Optional[str],
    target_id: Optional[str],
) -> Optional[Union[str, List[str]]]:
    from nonebot.adapters.telegram.bot import Bot
    from nonebot.adapters.telegram.model import InlineKeyboardMarkup
    from nonebot.adapters.telegram.message import File, Entity, Message

    assert isinstance(bot, Bot)

    if target_id is None:
        return None

    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        message = Message()
        reply_markup = None
        if image:
            if image.startswith("link://"):
                img_bytes = await download_image(image.replace("link://", ""))
            else:
                img_bytes = base64.b64decode(image.replace("base64://", ""))
            message.append(File.photo(img_bytes))
        if content:
            message.append(Entity.text(content))
        if record:
            message.append(File.audio(get_bytes_from_base64_str(record)))
        if video:
            message.append(File.video(get_bytes_from_base64_str(video)))

        if file:
            file_name, file_content = file.split("|")
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, "rb") as f:
                doc = f.read()
            message.append(File.document(doc))
            del_file(path)
        if buttons:
            bt = []
            kb = []
            for button in buttons:
                if isinstance(button, Dict):
                    bt.append(_tg_kb(button))
                    if len(bt) >= 2:
                        kb.append(bt)
                        bt = []
                if isinstance(button, List):
                    _t = []
                    for i in button:
                        _t.append(_tg_kb(i))
                    else:
                        kb.append(_t)
                        _t = []
            reply_markup = InlineKeyboardMarkup(inline_keyboard=kb)

        ret = await bot.send_to(
            chat_id=target_id,
            message=message,
            reply_markup=reply_markup,
        )
        # telegram 发送后返回 Message(媒体组为其列表), message_id 即消息id
        if isinstance(ret, list):
            ret = ret[0] if ret else None
        if ret is not None:
            return str(ret.message_id)
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                _r = await _send(None, _msg["data"])
            else:
                _r = await _send(_msg["data"], None)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id


async def feishu_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    record: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
) -> Optional[Union[str, List[str]]]:
    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        if file:
            file_name, file_content = file.split("|")
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, "rb") as f:
                doc = f.read()
            msg = await bot.call_api(
                "im/v1/files",
                method="POST",
                data={"file_type": "stream", "file_name": file_name},
                files={"file": doc},
            )
            del_file(path)
            _type = "file"
        elif record:
            logger.warning("飞书不支持发送MP3语音消息")
            return
        elif content:
            if at_list and target_type == "group":
                for at in at_list:
                    try:
                        name_data = await bot.call_api(
                            "contact/v3/users",
                            method="GET",
                            query={"user_id": at},
                            body={"user_id_type", "union_id"},
                        )
                        name = name_data["user"]["name"]
                    except Exception as e:
                        logger.warning(f"获取用户名称失败...{e}")
                        name = at[:3]

                    content += f'<at user_id="{at}">{name}</at>'
            msg = {"text": content}
            _type = "text"
        elif image:
            if image.startswith("link://"):
                img_bytes = await download_image(image.replace("link://", ""))
            else:
                img_bytes = base64.b64decode(image.replace("base64://", ""))
            data = {"image_type": "message"}
            files = {"image": img_bytes}
            params = {
                "method": "POST",
                "data": data,
                "files": files,
            }
            msg = await bot.call_api("im/v1/images", **params)
            _type = "image"
        else:
            return

        params = {
            "method": "POST",
            "query": {"receive_id_type": ("union_id" if target_type == "direct" else "chat_id")},
            "body": {
                "receive_id": target_id,
                "content": json.dumps(msg),
                "msg_type": _type,
            },
        }
        msg_result = await bot.call_api("im/v1/messages", **params)
        # 飞书发送回执的 data 含 message_id 字段(call_api 返回响应 data)
        if isinstance(msg_result, dict):
            _mid = msg_result.get("message_id")
            if _mid is None and isinstance(msg_result.get("data"), dict):
                _mid = msg_result["data"].get("message_id")
            if _mid is not None:
                return str(_mid)
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                _r = await _send(None, _msg["data"])
            else:
                _r = await _send(_msg["data"], None)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id


async def Milky_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    record: Optional[str],
    video: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
) -> Optional[Union[str, List[str]]]:
    from nonebot.adapters.milky import Bot
    from nonebot.adapters.milky.message import Message, MessageSegment

    assert isinstance(bot, Bot)

    if target_id is None:
        return None

    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        message = Message()

        if file:
            file_name, file_content = file.split("|")
            if target_type == "group":
                await bot.upload_group_file(
                    group_id=int(target_id),
                    file_name=file_name,
                    base64=file_content,
                )
            elif target_type == "direct":
                await bot.upload_private_file(
                    user_id=int(target_id),
                    file_name=file_name,
                    base64=file_content,
                )
            return

        if content:
            message.append(MessageSegment.text(content))
        if image:
            message.append(MessageSegment.image(image))
        if record:
            message.append(MessageSegment.record(raw=get_bytes_from_base64_str(record)))
        if video:
            message.append(MessageSegment.video(raw=get_bytes_from_base64_str(video)))

        if at_list:
            for at in at_list:
                message.append(MessageSegment.mention(int(at)))

        ret = None
        if target_type == "group":
            ret = await bot.send_group_message(group_id=int(target_id), message=message)
        elif target_type == "direct":
            ret = await bot.send_private_message(user_id=int(target_id), message=message)

        # milky 发送后返回 MessageResponse, message_seq 即消息id
        if ret is not None:
            return str(ret.message_seq)
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                _r = await _send(None, _msg["data"])
            else:
                _r = await _send(_msg["data"], None)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id


async def del_msg(
    bot: Bot,
    bot_id: str,
    message_id: str,
    target_id: Optional[str],
    target_type: Optional[str],
) -> None:
    """撤回已发出的消息(对应 core 下发的 excute_delete_message 控制包).

    各平台撤回入参不同: OneBot/飞书仅需消息id; Telegram/QQ频道/Discord 需会话定位;
    Milky 用 message_seq + 会话. 平台无对应 API 时记 warning, 不再误发空消息.
    """
    try:
        if bot_id == "onebot":
            from nonebot.adapters.onebot.v11 import Bot as OB11Bot

            assert isinstance(bot, OB11Bot)
            await bot.delete_msg(message_id=int(message_id))
        elif bot_id == "onebot_v12":
            await bot.call_api("delete_message", message_id=str(message_id))
        elif bot_id == "telegram":
            if target_id is not None:
                await bot.call_api(
                    "delete_message",
                    chat_id=target_id,
                    message_id=int(message_id),
                )
        elif bot_id == "qqguild":
            if target_id is not None:
                await bot.call_api(
                    "delete_message",
                    channel_id=str(target_id),
                    message_id=str(message_id),
                )
        elif bot_id == "discord":
            if target_id is not None:
                await bot.call_api(
                    "delete_message",
                    channel_id=int(target_id),
                    message_id=int(message_id),
                )
        elif bot_id == "milky":
            if target_id is not None:
                if target_type == "group":
                    await bot.call_api(
                        "recall_group_message",
                        group_id=int(target_id),
                        message_seq=int(message_id),
                    )
                else:
                    await bot.call_api(
                        "recall_private_message",
                        user_id=int(target_id),
                        message_seq=int(message_id),
                    )
        elif bot_id == "feishu":
            await bot.call_api(
                f"im/v1/messages/{message_id}",
                method="DELETE",
            )
        else:
            logger.warning(f"[gscore] 平台 {bot_id} 暂不支持撤回消息")
    except Exception as e:
        logger.warning(f"[gscore] 撤回消息失败({bot_id}): {e}")


async def onebot_v12_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    at_list: Optional[List[str]],
    record: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
) -> Optional[Union[str, List[str]]]:
    async def _send(content: Optional[str], image: Optional[str]) -> Optional[str]:
        async def send_file_message(params, file_type, file_id):
            params["message"] = [{"type": file_type, "data": {"file_id": file_id}}]
            return await bot.call_api("send_message", **params)

        if not any([content, image, file]):
            return None

        params = {}
        if target_type == "group":
            params["detail_type"] = "group"
            params["group_id"] = target_id
        elif target_type == "direct":
            params["detail_type"] = "private"
            params["user_id"] = target_id

        resp = None
        if content:
            params["message"] = [{"type": "text", "data": {"text": f"{content}"}}]
            if at_list and target_type == "group":
                params["message"].insert(
                    0,
                    {"type": "mention", "data": {"user_id": f"{at_list[0]}"}},
                )
            resp = await bot.call_api("send_message", **params)
        elif image:
            timestamp = time.time()
            file_name = f"{target_id}_{timestamp}.png"
            if image.startswith("link://"):
                link = image.replace("link://", "")
                up_data = await bot.call_api(
                    "upload_file",
                    type="url",
                    url=link,
                    name=f"{file_name}",
                )
            else:
                img_bytes = base64.b64decode(image.replace("base64://", ""))
                up_data = await bot.call_api(
                    "upload_file",
                    type="data",
                    data=img_bytes,
                    name=f"{file_name}",
                )
            file_id = up_data["file_id"]
            resp = await send_file_message(params, "image", file_id)
        elif file:
            file_name, file_content = file.split("|")
            if file_content.startswith("link://"):
                link = file_content.replace("link://", "")
                up_data = await bot.call_api(
                    "upload_file",
                    type="url",
                    url=link,
                    name=f"{file_name}",
                )
            else:
                file_data = base64.b64decode(file_content)
                up_data = await bot.call_api(
                    "upload_file",
                    type="data",
                    data=file_data,
                    name=f"{file_name}",
                )
            file_id = up_data["file_id"]
            resp = await send_file_message(params, "file", file_id)

        # OneBot v12 的 send_message 动作回执含 message_id 字段
        if isinstance(resp, dict) and resp.get("message_id") is not None:
            return str(resp["message_id"])
        return None

    # node 在不支持合并转发的平台被展开为多条消息, 逐条累积 id 为 list 回传
    recall_id: Optional[Union[str, List[str]]] = None
    if node:
        _ids: List[str] = []
        for _msg in node:
            if _msg["type"] == "image":
                _r = await _send(None, _msg["data"])
            else:
                _r = await _send(_msg["data"], None)
            if _r is not None:
                _ids.append(_r)
        recall_id = _ids
    else:
        recall_id = await _send(content, image)
    return recall_id
