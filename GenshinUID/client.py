import asyncio
from typing import Union, Optional

import websockets.client
from nonebot import get_bot
from nonebot.log import logger
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosedError

from .models import MessageSend, MessageReceive

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
                else:
                    pass

                # 根据bot_id字段发送消息
                if msg.bot_id == 'onebot':
                    result_image = (
                        f'[CQ:image,file=base64://{image}]' if image else ''
                    )
                    result_msg = content + result_image
                    if msg.target_type == 'group':
                        await bot.call_api(
                            'send_group_msg',
                            group_id=msg.target_id,
                            message=result_msg,
                        )
                    else:
                        await bot.call_api(
                            'send_private_msg',
                            user_id=msg.target_id,
                            message=result_msg,
                        )
                elif msg.bot_id == 'ntchat':
                    if content:
                        await bot.call_api(
                            'send_text',
                            to_wxid=msg.target_id,
                            content=content,
                        )
                    if image:
                        await bot.call_api(
                            'send_image',
                            to_wxid=msg.target_id,
                            content=content,
                        )
                elif msg.bot_id == 'qqguild':
                    result = {}
                    if image:
                        result['file_image'] = image
                    if content:
                        result['content'] = content
                    if msg.target_type == 'group':
                        await bot.call_api(
                            'post_messages',
                            channel_id=int(msg.target_id)
                            if msg.target_id
                            else 0,
                            **result,
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
