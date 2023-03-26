import os
import base64
import asyncio
from pathlib import Path
from typing import Dict, List, Union, Optional

import hoshino
import websockets.client
from msgspec import json as msgjson
from websockets.exceptions import ConnectionClosedError

from .base import logger, hoshino_bot
from .models import MessageSend, MessageReceive

BOT_ID = 'HoshinoBot'
bots: Dict[str, str] = {}


class GsClient:
    @classmethod
    async def async_connect(
        cls, IP: str = 'localhost', PORT: Union[str, int] = '8765'
    ):
        self = GsClient()
        cls.is_alive = True
        cls.ws_url = f'ws://{IP}:{PORT}/ws/{BOT_ID}'
        logger.info(f'Bot_ID: {BOT_ID}连接至[gsuid-core]: {self.ws_url}...')
        cls.ws = await websockets.client.connect(cls.ws_url, max_size=2**26)
        logger.info(f'与[gsuid-core]成功连接! Bot_ID: {BOT_ID}')
        cls.msg_list = asyncio.queues.Queue()
        return self

    async def recv_msg(self):
        try:
            global bots
            await asyncio.sleep(5)
            async for message in self.ws:
                try:
                    msg = msgjson.decode(message, type=MessageSend)
                    logger.info(
                        f'【接收】[gsuid-core]: '
                        f'{msg.bot_id} - {msg.target_type} - {msg.target_id}'
                    )
                    # 解析消息
                    if msg.bot_id == 'NoneBot2':
                        continue

                    bot = hoshino_bot

                    content = ''
                    image: Optional[str] = None
                    node = []
                    file = ''
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
                                elif _c.type == 'file':
                                    file = _c.data
                    else:
                        pass

                    # 根据bot_id字段发送消息
                    # OneBot v11 & v12
                    if not msg.bot_self_id:
                        self_ids = hoshino.get_self_ids()
                    else:
                        self_ids = [msg.bot_self_id]

                    for ids in self_ids:
                        if msg.bot_id == 'onebot':
                            await onebot_send(
                                bot,
                                content,
                                image,
                                node,
                                file,
                                ids,
                                msg.target_id,
                                msg.target_type,
                            )
                except Exception as e:
                    logger.error(e)
        except RuntimeError:
            pass
        except ConnectionClosedError:
            logger.warning(f'与[gsuid-core]断开连接! Bot_ID: {BOT_ID}')
            self.is_alive = False

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


def store_file(path: Path, file: str):
    file_content = base64.b64decode(file).decode()
    with open(path, 'w') as f:
        f.write(file_content)


def del_file(path: Path):
    if path.exists():
        os.remove(path)


async def onebot_send(
    bot: hoshino_bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    bot_self_id: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        result_image = f'[CQ:image,file={image}]' if image else ''
        content = content if content else ''
        result_msg = content + result_image

        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            if target_type == 'group':
                await bot.call_action(
                    'upload_group_file',
                    file=str(path.absolute()),
                    name=file_name,
                    group_id=target_id,
                )
            else:
                await bot.call_action(
                    'upload_private_file',
                    file=str(path.absolute()),
                    name=file_name,
                    user_id=target_id,
                )
            del_file(path)
        else:
            if target_type == 'group':
                await bot.send_group_msg(
                    self_id=bot_self_id,
                    group_id=target_id,
                    message=result_msg,
                )
            else:
                await bot.send_private_msg(
                    self_id=bot_self_id,
                    user_id=target_id,
                    message=result_msg,
                )

    async def _send_node(messages):
        if target_type == 'group':
            await bot.call_action(
                'send_group_forward_msg',
                group_id=target_id,
                messages=messages,
            )
        else:
            await bot.call_action(
                'send_private_forward_msg',
                user_id=target_id,
                messages=messages,
            )

    if node:
        messages = [
            to_json(
                f'[CQ:image,file={_msg["data"]}]'
                if _msg['type'] == 'image'
                else _msg['data'],
                '小助手',
                2854196310,
            )
            for _msg in node
            if 'data' in _msg
        ]
        await _send_node(messages)
    else:
        await _send(content, image)
