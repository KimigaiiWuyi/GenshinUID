import asyncio
from typing import List, Union, Optional

import websockets.client
from nonebot import get_bot
from nonebot.log import logger
from nonebot.adapters import Bot
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosedError

from .models import Message, MessageSend, MessageReceive

BOT_ID = 'NoneBot2'


class GsClient:
    @classmethod
    async def async_connect(
        cls, IP: str = 'localhost', PORT: Union[str, int] = '8765'
    ):
        self = GsClient()
        cls.ws_url = f'ws://{IP}:{PORT}/ws/{BOT_ID}'
        logger.info(f'Bot_ID: {BOT_ID}连接至[gsuid-core]: {self.ws_url}...')
        cls.ws = await websockets.client.connect(cls.ws_url, max_size=2**26)
        logger.success(f'与[gsuid-core]成功连接! Bot_ID: {BOT_ID}')
        cls.msg_list = asyncio.queues.Queue()
        return self

    async def recv_msg(self):
        try:
            bot = get_bot()
            async for message in self.ws:
                msg = msgjson.decode(message, type=MessageSend)
                logger.info(f'【接收】[gsuid-core]: {msg}')
                # 解析消息
                content = ''
                image: Optional[bytes] = None
                node = []
                if msg.content:
                    for _c in msg.content:
                        if _c.data:
                            if _c.type == 'text':
                                content += _c.data
                            elif _c.type == 'image':
                                image = _c.data
                            elif _c.type and _c.type.startswith('log'):
                                _type = _c.type.split('_')[-1].lower()
                                getattr(logger, _type)(_c.data)
                            elif _c.type == 'node':
                                node = _c.data
                else:
                    pass

                # 根据bot_id字段发送消息
                # OneBot v11 & v12
                if msg.bot_id == 'onebot':
                    await onebot_send(
                        bot,
                        content,
                        image,
                        node,
                        msg.target_id,
                        msg.target_type,
                    )
                # ntchat
                elif msg.bot_id == 'ntchat':
                    await ntchat_send(bot, content, image, node, msg.target_id)
                # 频道
                elif msg.bot_id == 'qqguild':
                    await guild_send(
                        bot,
                        content,
                        image,
                        node,
                        msg.target_id,
                        msg.target_type,
                    )
        except ConnectionClosedError:
            logger.warning(f'与[gsuid-core]断开连接! Bot_ID: {BOT_ID}')

    async def _input(self, msg: MessageReceive):
        await self.msg_list.put(msg)

    async def send_msg(self):
        while True:
            msg: MessageReceive = await self.msg_list.get()
            msg_send = msgjson.encode(msg)
            await self.ws.send(msg_send)

    async def start(self):
        recv_task = asyncio.create_task(self.recv_msg())
        send_task = asyncio.create_task(self.send_msg())
        _, pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()


def to_json(msg: str, name: str, uin: int):
    return {
        'type': 'node',
        'data': {'name': name, 'uin': uin, 'content': msg},
    }


async def onebot_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[bytes],
    node: Optional[List[Message]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[bytes]):
        result_image = f'[CQ:image,file=base64://{image}]' if image else ''
        content = content if content else ''
        result_msg = content + result_image
        if target_type == 'group':
            await bot.call_api(
                'send_group_msg',
                group_id=target_id,
                message=result_msg,
            )
        else:
            await bot.call_api(
                'send_private_msg',
                user_id=target_id,
                message=result_msg,
            )

    async def _send_node(messages):
        if target_type == 'group':
            await bot.call_api(
                'send_group_forward_msg',
                group_id=target_id,
                messages=messages,
            )
        else:
            await bot.call_api(
                'send_private_forward_msg',
                user_id=target_id,
                messages=messages,
            )

    if node:
        messages = (
            [
                to_json(
                    f'[CQ:image,file=base64://{_msg.data}]'
                    if _msg.type == 'image'
                    else _msg.data,
                    '小助手',
                    2854196310,
                )
                for _msg in node
                if _msg.data
            ],
        )
        await _send_node(messages)
    else:
        await _send(content, image)


async def guild_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[bytes],
    node: Optional[List[Message]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[bytes]):
        result = {}
        if image:
            result['file_image'] = image
        if content:
            result['content'] = content
        if target_type == 'group':
            await bot.call_api(
                'post_messages',
                channel_id=int(target_id) if target_id else 0,
                **result,
            )

    if node:
        for _msg in node:
            if _msg.type == 'image':
                image = _msg.data
                content = None
            else:
                image = None
                content = _msg.data
            await _send(content, image)
    else:
        await _send(content, image)


async def ntchat_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[bytes],
    node: Optional[List[Message]],
    target_id: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[bytes]):
        if content:
            await bot.call_api(
                'send_text',
                to_wxid=target_id,
                content=content,
            )
        if image:
            await bot.call_api(
                'send_image',
                to_wxid=target_id,
                content=content,
            )

    if node:
        for _msg in node:
            if _msg.type == 'image':
                await _send(None, _msg.data)
            else:
                await _send(_msg.data, None)
    else:
        await _send(content, image)
