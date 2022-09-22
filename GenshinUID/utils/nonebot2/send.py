import json
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

from nonebot.log import logger
from aiohttp import ClientSession
from nonebot.drivers import Request
from nonebot.typing import overrides
from nonebot.adapters.qqguild.bot import Bot
from pydantic import BaseModel, parse_obj_as
from nonebot.adapters.qqguild.adapter import Adapter
from nonebot.adapters.qqguild.api.request import _request
from nonebot.adapters.qqguild.api.handle import API_HANDLERS
from nonebot.adapters.qqguild.api.model import Message as APIMessage
from nonebot.adapters.qqguild.message import Message, MessageSegment
from nonebot.adapters.qqguild.event import (
    Event,
    MessageEvent,
    DirectMessageCreateEvent,
)
from nonebot.adapters.qqguild.api.model import (
    MessageArk,
    MessageEmbed,
    MessageReference,
)


class LocalImage(MessageSegment):
    @overrides(MessageSegment)
    def __str__(self) -> str:
        return "<local_image>"


def local_image(data: Union[str, Path, bytes, BytesIO]) -> LocalImage:
    if isinstance(data, (str, Path)):
        with open(data, "rb") as f:
            b = f.read()
    elif isinstance(data, BytesIO):
        b = data.getvalue()
    else:
        b = data
    return LocalImage("local_image", data={"content": b})


class MessageSend(BaseModel):
    content: Optional[str] = None
    embed: Optional[MessageEmbed] = None
    ark: Optional[MessageArk] = None
    message_reference: Optional[MessageReference] = None
    image: Optional[str] = None
    file_image: Optional[bytes] = None
    msg_id: Optional[str] = None


def patch_send():
    logger.info("注入本地图片发送猴子补丁")

    @overrides(Bot)
    async def send(
        self,
        event: Event,
        message: Union[str, Message, MessageSegment],
        **kwargs,
    ) -> Any:
        if (
            not isinstance(event, MessageEvent)
            or not event.channel_id
            or not event.id
        ):
            raise RuntimeError("Event cannot be replied to!")
        message = (
            MessageSegment.text(message)
            if isinstance(message, str)
            else message
        )

        message = message if isinstance(message, Message) else Message(message)
        content = message.extract_content() or None
        guild_id = None
        if isinstance(event, DirectMessageCreateEvent):
            event_dict = event.__dict__
            guild_id = event_dict['guild_id']
        if embed := (message["embed"] or None):
            embed = embed[-1].data["embed"]
        if ark := (message["ark"] or None):
            ark = ark[-1].data["ark"]
        if image := (message["attachment"] or None):
            image = image[-1].data["url"]
        if local_image := (message["local_image"] or None):
            local_image = local_image[-1].data["content"]
        return await self.post_messages(
            channel_id=event.channel_id,
            guild_id=guild_id,
            msg_id=event.id,
            content=content,
            embed=embed,
            ark=ark,
            image=image,
            file_image=local_image,
            **kwargs,
        )

    Bot.send = send

    async def post_messages(
        adapter: Adapter, bot: Bot, channel_id: int, guild_id: int, **data
    ) -> Union[APIMessage, List[APIMessage]]:
        headers = {"Authorization": adapter.get_authorization(bot.bot_info)}
        model_data = MessageSend(**data).dict(exclude_none=True)
        d_api = adapter.get_api_base() / f"channels/{channel_id}/messages"
        if guild_id:
            d_api = adapter.get_api_base() / f"dms/{guild_id}/messages"
        if "file_image" in model_data.keys() and (
            file_image := model_data.pop("file_image")
        ):
            new_data: Dict[str, Union[BytesIO, str]] = {
                "file_image": BytesIO(file_image)
            }
            for k, v in model_data.items():
                # 当字段类型为对象或数组时需要将字段序列化为 JSON 字符串后进行调用
                # https://bot.q.qq.com/wiki/develop/api/openapi/message/post_messages.html#form-data-%E6%A0%BC%E5%BC%8F%E7%A4%BA%E4%BE%8B
                if isinstance(v, BaseModel):
                    new_data[k] = v.json()
                elif isinstance(v, (list, dict)):
                    new_data[k] = json.dumps(v)

                else:
                    new_data[k] = v
            async with ClientSession(headers=headers) as session:
                req = await session.post(
                    d_api,
                    data=new_data,
                )
                data = await req.json()
        else:
            request = Request(
                "POST",
                d_api,
                json=model_data,
                headers=headers,
            )
            data = await _request(adapter, bot, request)
        if guild_id:
            return parse_obj_as(List[APIMessage], data)
        else:
            return parse_obj_as(APIMessage, data)

    API_HANDLERS["post_messages"] = post_messages
    logger.success("本地图片发送猴子补丁已注入")
