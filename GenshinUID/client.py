import asyncio
from typing import Union

import websockets.client
from nonebot import get_bot
from nonebot.log import logger
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosedError

from .models import MessageSend, MessageReceive

BOT_ID = 'NoneBot-OB11'


class GsClient:
    @classmethod
    async def async_connect(
        cls, IP: str = 'localhost', PORT: Union[str, int] = '8765'
    ):
        self = GsClient()
        cls.ws_url = f'ws://{IP}:{PORT}/ws/{BOT_ID}'
        logger.info(f'Bot_ID: {BOT_ID}连接至[gsuid-core]: {self.ws_url}...')
        cls.ws = await websockets.client.connect(cls.ws_url)
        logger.success('与[gsuid-core]成功连接! Bot_ID: {BOT_ID}')
        cls.msg_list = asyncio.queues.Queue()
        return self

    async def recv_msg(self):
        try:
            bot = get_bot()
            async for message in self.ws:
                msg = msgjson.decode(message, type=MessageSend)
                logger.info(f'【接收】[gsuid-core]: {msg}')
                content = ''
                if msg.content:
                    for _c in msg.content:
                        if _c.type == 'text' or _c.type == 'image':
                            content += _c.data if _c.data else ''
                else:
                    pass
                if msg.bot_id.startswith('NoneBot'):
                    if msg.target_type == 'group':
                        await bot.call_api(
                            'send_group_msg',
                            group_id=msg.target_id,
                            message=content,
                        )
                    else:
                        await bot.call_api(
                            'send_private_msg',
                            user_id=msg.target_id,
                            message=content,
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
