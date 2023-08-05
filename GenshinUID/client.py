import os
import json
import time
import uuid
import base64
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Union, Optional

import websockets.client
from nonebot.log import logger
from nonebot.adapters import Bot
from msgspec import json as msgjson
from nonebot import get_bot, get_bots, get_driver
from websockets.exceptions import ConnectionClosedError

from .models import MessageSend, MessageReceive

bots: Dict[str, str] = {}
driver = get_driver()

if hasattr(driver.config, 'gsuid_core_botid'):
    BOT_ID = str(uuid.uuid4())[:10]
else:
    BOT_ID = 'NoneBot2'

if hasattr(driver.config, 'gsuid_core_host'):
    HOST = driver.config.gsuid_core_host
else:
    HOST = 'localhost'

if hasattr(driver.config, 'gsuid_core_port'):
    PORT = driver.config.gsuid_core_port
else:
    PORT = '8765'


def _get_bot(bot_id: str) -> Bot:
    if 'v12' in bot_id:
        bot_id = 'onebotv12'
    # bots: Dict[str, str] 以适配器名称为键、bot_self_id为值的字典
    _refresh_bots()
    if bot_id not in bots:
        for _bot_id in bots.keys():
            if bot_id in _bot_id:
                bot_id = _bot_id
                break
        else:
            logger.warning('未获取到正确的Bot实例,将使用默认Bot...')
            logger.warning(f'当前bot_id: {bot_id}, bots: {bots}')
            return get_bot()
    bot_real_id = bots[bot_id]
    bot = get_bot(bot_real_id)
    return bot


def _refresh_bots():
    global bots
    _bots = get_bots()
    for bot_real_id in _bots:
        bot = _bots[bot_real_id]
        bot_id = bot.type.lower().replace(' ', '')
        bots[bot_id] = bot_real_id


class GsClient:
    _instance = None

    @classmethod
    async def async_connect(cls, IP: str = HOST, PORT: Union[str, int] = PORT):
        self = GsClient()
        cls.is_alive = True
        cls.ws_url = f'ws://{IP}:{PORT}/ws/{BOT_ID}'
        logger.info(f'Bot_ID: {BOT_ID}连接至[gsuid-core]: {self.ws_url}...')
        cls.ws = await websockets.client.connect(
            cls.ws_url, max_size=2**26, open_timeout=60, ping_timeout=60
        )
        logger.success(f'与[gsuid-core]成功连接! Bot_ID: {BOT_ID}')
        cls.msg_list = asyncio.queues.Queue()
        cls.pending = []
        return self

    def __new__(cls, *args, **kwargs):
        # 判断sv是否已经被初始化
        if cls._instance is None:
            cls._instance = super(GsClient, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    async def recv_msg(self):
        try:
            await asyncio.sleep(5)
            _refresh_bots()
            async for message in self.ws:
                try:
                    _bots = get_bots()
                    msg = msgjson.decode(message, type=MessageSend)
                    logger.info(
                        f'【接收】[gsuid-core]: '
                        f'{msg.bot_id} - {msg.target_type} - {msg.target_id}'
                    )
                    bot_list = []

                    # 解析消息
                    if msg.bot_id == 'NoneBot2':
                        if msg.content:
                            _data = msg.content[0]
                            if _data.type and _data.type.startswith('log'):
                                _type = _data.type.split('_')[-1].lower()
                                getattr(logger, _type)(_data.data)
                        continue

                    if msg.bot_self_id in _bots:
                        bot_list.append(_bots[msg.bot_self_id])
                    elif not msg.bot_self_id:
                        bot_list.append(_get_bot(msg.bot_id))
                    else:
                        continue

                    content = ''
                    image: Optional[str] = None
                    node = []
                    file = ''
                    at_list = []
                    group_id = ''
                    if msg.content:
                        for _c in msg.content:
                            if _c.data:
                                if _c.type == 'text':
                                    content += _c.data
                                elif _c.type == 'image':
                                    image = _c.data
                                elif _c.type == 'node':
                                    node = _c.data
                                elif _c.type == 'file':
                                    file = _c.data
                                elif _c.type == 'at':
                                    at_list.append(_c.data)
                                elif _c.type == 'group':
                                    group_id = _c.data
                    else:
                        pass

                    # 根据bot_id字段发送消息

                    for bot in bot_list:
                        # OneBot v11
                        if msg.bot_id == 'onebot':
                            await onebot_send(
                                bot,
                                content,
                                image,
                                node,
                                file,
                                at_list,
                                msg.target_id,
                                msg.target_type,
                            )
                        # OneBot v12
                        elif msg.bot_id == 'onebot_v12':
                            await onebot_v12_send(
                                bot,
                                content,
                                image,
                                node,
                                file,
                                at_list,
                                msg.target_id,
                                msg.target_type,
                            )
                        # ntchat
                        elif msg.bot_id == 'ntchat':
                            await ntchat_send(
                                bot,
                                content,
                                image,
                                file,
                                node,
                                at_list,
                                msg.target_id,
                                msg.target_type,
                            )
                        # 频道
                        elif msg.bot_id == 'qqguild':
                            await guild_send(
                                bot,
                                content,
                                image,
                                node,
                                at_list,
                                msg.target_id,
                                msg.target_type,
                                msg.msg_id,
                                group_id,
                            )
                        elif msg.bot_id == 'telegram':
                            await telegram_send(
                                bot,
                                content,
                                image,
                                file,
                                node,
                                msg.target_id,
                            )
                        elif msg.bot_id == 'kaiheila':
                            await kaiheila_send(
                                bot,
                                content,
                                image,
                                file,
                                node,
                                msg.target_id,
                                msg.target_type,
                            )
                        elif msg.bot_id == 'feishu':
                            await feishu_send(
                                bot,
                                content,
                                image,
                                file,
                                node,
                                at_list,
                                msg.target_id,
                                msg.target_type,
                            )
                except Exception as e:
                    logger.error(e)
        except RuntimeError as e:
            logger.error(e)
        except ConnectionClosedError:
            for task in self.pending:
                task.cancel()
            logger.warning(f'与[gsuid-core]断开连接! Bot_ID: {BOT_ID}')
            for _ in range(30):
                await asyncio.sleep(5)
                try:
                    await self.async_connect()
                    await self.start()
                    break
                except:  # noqa
                    logger.debug('自动连接core服务器失败...五秒后重新连接...')

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
        _, self.pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )


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
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        from nonebot.adapters.onebot.v11 import MessageSegment

        result_image = MessageSegment.image(image) if image else ''
        _content = MessageSegment.text(content) if content else ''
        result_msg = _content + result_image
        if at_list and target_type == 'group':
            for at in at_list:
                result_msg += MessageSegment.at(at)

        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            if target_type == 'group':
                await bot.call_api(
                    'upload_group_file',
                    file=str(path.absolute()),
                    name=file_name,
                    group_id=target_id,
                )
            else:
                await bot.call_api(
                    'upload_private_file',
                    file=str(path.absolute()),
                    name=file_name,
                    user_id=target_id,
                )
            del_file(path)
        else:
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


async def guild_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
    guild_id: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        result: Dict[str, Any] = {'msg_id': msg_id}
        if image:
            img_bytes = base64.b64decode(image.replace('base64://', ''))
            result['file_image'] = img_bytes
        if content:
            result['content'] = content
            if at_list and target_type == 'group':
                for at in at_list:
                    result['content'] += f'<@{at}>'
        if target_type == 'group':
            await bot.call_api(
                'post_messages',
                channel_id=int(target_id) if target_id else 0,
                **result,
            )
        else:
            dms = await bot.call_api(
                'post_dms',
                recipient_id=str(target_id),
                source_guild_id=str(guild_id),
            )
            await bot.call_api(
                'post_dms_messages',
                guild_id=dms.guild_id,
                **result,
            )

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                image = _msg['data']
                content = None
            else:
                image = None
                content = _msg['data']
            await _send(content, image)
    else:
        await _send(content, image)


async def ntchat_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        if content:
            result = {}
            if at_list and target_type == 'group':
                for _ in at_list:
                    content += '{$@}'
                result['at_list'] = at_list
            result['content'] = content
            await bot.call_api('send_text', to_wxid=target_id, **result)
        if image:
            await bot.call_api(
                'send_image',
                to_wxid=target_id,
                file_path=image,
            )
        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            await bot.call_api(
                'send_file',
                to_wxid=target_id,
                file_path=str(path.absolute()),
            )
            del_file(path)

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'])
            else:
                await _send(_msg['data'], None)
    else:
        await _send(content, image)


async def kaiheila_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        result = {}
        result['type'] = 1
        if image:
            img_bytes = base64.b64decode(image.replace('base64://', ''))
            url = await bot.upload_file(img_bytes, 'GSUID-TEMP')  # type:ignore
            result['type'] = 2
            result['content'] = url
        elif file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
                doc = f.read()
            url = await bot.upload_file(doc, file_name)  # type:ignore
            result['content'] = url
            del_file(path)
        else:
            result['content'] = content

        if target_type == 'group':
            api = 'message/create'
            result['channel_id'] = target_id
        else:
            api = 'direct-message/create'
            result['target_id'] = target_id
        await bot.call_api(api, **result)

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'])
            else:
                await _send(_msg['data'], None)
    else:
        await _send(content, image)


async def telegram_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    target_id: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        result = {}
        if image:
            img_bytes = base64.b64decode(image.replace('base64://', ''))
            result['photo'] = img_bytes
        if content:
            result['text'] = content
        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
                doc = f.read()
            result['document'] = doc
            del_file(path)

        if content:
            await bot.call_api('send_message', chat_id=target_id, **result)
        if image:
            await bot.call_api('send_photo', chat_id=target_id, **result)
        if file:
            await bot.call_api('send_document', chat_id=target_id, **result)

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'])
            else:
                await _send(_msg['data'], None)
    else:
        await _send(content, image)


async def feishu_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    file: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
                doc = f.read()
            msg = await bot.call_api(
                'im/v1/files',
                method='POST',
                data={'file_type': 'stream', 'file_name': file_name},
                files={'file': doc},
            )
            del_file(path)
            _type = 'file'
        elif content:
            if at_list and target_type == 'group':
                for at in at_list:
                    try:
                        name_data = await bot.call_api(
                            'contact/v3/users',
                            method='GET',
                            query={'user_id': at},
                            body={'user_id_type', 'union_id'},
                        )
                        name = name_data['user']['name']
                    except Exception as e:
                        logger.warning(f'获取用户名称失败...{e}')
                        name = at[:3]

                    content += f'<at user_id="{at}">{name}</at>'
            msg = {'text': content}
            _type = 'text'
        elif image:
            data = {"image_type": "message"}
            files = {"image": base64.b64decode(image.replace('base64://', ''))}
            params = {
                "method": "POST",
                "data": data,
                "files": files,
            }
            msg = await bot.call_api('im/v1/images', **params)
            _type = 'image'
        else:
            return

        params = {
            "method": "POST",
            "query": {
                "receive_id_type": 'union_id'
                if target_type == 'direct'
                else 'chat_id'
            },
            "body": {
                "receive_id": target_id,
                "content": json.dumps(msg),
                "msg_type": _type,
            },
        }
        await bot.call_api('im/v1/messages', **params)

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'])
            else:
                await _send(_msg['data'], None)
    else:
        await _send(content, image)


async def onebot_v12_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    async def _send(content: Optional[str], image: Optional[str]):
        async def send_file_message(params, file_type, file_id):
            params["message"] = [
                {"type": file_type, "data": {"file_id": file_id}}
            ]
            await bot.call_api('send_message', **params)

        if not any([content, image, file]):
            return

        params = {}
        if target_type == "group":
            params["detail_type"] = "group"
            params["group_id"] = target_id
        elif target_type == "direct":
            params["detail_type"] = "private"
            params["user_id"] = target_id

        if content:
            params["message"] = [
                {"type": "text", "data": {"text": f"{content}"}}
            ]
            if at_list and target_type == "group":
                params["message"].insert(
                    0,
                    {"type": "mention", "data": {"user_id": f"{at_list[0]}"}},
                )
            await bot.call_api('send_message', **params)
        elif image:
            timestamp = time.time()
            file_name = f'{target_id}_{timestamp}.png'
            if image.startswith('link://'):
                link = image.replace('link://', '')
                up_data = await bot.call_api(
                    'upload_file',
                    type="url",
                    url=link,
                    name=f"{file_name}",
                )
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
                up_data = await bot.call_api(
                    'upload_file',
                    type="data",
                    data=img_bytes,
                    name=f"{file_name}",
                )
            file_id = up_data['file_id']
            await send_file_message(params, "image", file_id)
        elif file:
            file_name, file_content = file.split('|')
            if file_content.startswith('link://'):
                link = file_content.replace('link://', '')
                up_data = await bot.call_api(
                    'upload_file',
                    type="url",
                    url=link,
                    name=f"{file_name}",
                )
            else:
                file_data = base64.b64decode(file_content)
                up_data = await bot.call_api(
                    'upload_file',
                    type="data",
                    data=file_data,
                    name=f"{file_name}",
                )
            file_id = up_data['file_id']
            await send_file_message(params, "file", file_id)

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'])
            else:
                await _send(_msg['data'], None)
    else:
        await _send(content, image)
