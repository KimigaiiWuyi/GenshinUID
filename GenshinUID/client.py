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

from .utils import download_image
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
    elif 'red' in bot_id:
        bot_id = 'RedProtocol'
    elif 'qqguild' in bot_id:
        bot_id = 'qq'
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
                    markdown = ''
                    buttons = []

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
                                elif _c.type == 'markdown':
                                    markdown = _c.data
                                elif _c.type == 'buttons':
                                    buttons = _c.data
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
                        # RedProtocol
                        elif msg.bot_id == 'onebot:red':
                            await onebot_red_send(
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
                                markdown,
                                buttons,
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
                        elif msg.bot_id == 'qqgroup':
                            await group_send(
                                bot,
                                content,
                                image,
                                node,
                                markdown,
                                buttons,
                                msg.target_id,
                                msg.target_type,
                                msg.msg_id,
                            )
                        elif msg.bot_id == 'villa':
                            await villa_send(
                                bot,
                                content,
                                image,
                                node,
                                at_list,
                                markdown,
                                buttons,
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
                        elif msg.bot_id == 'dodo':
                            await dodo_send(
                                bot,
                                content,
                                image,
                                node,
                                at_list,
                                markdown,
                                buttons,
                                msg.target_id,
                                msg.target_type,
                                group_id,
                            )
                except Exception as e:
                    logger.exception(e)
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


async def villa_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    from nonebot.adapters.villa import Bot, Message, MessageSegment
    from nonebot.adapters.villa.api import (
        PostMessageContent,
        ImageMessageContent,
    )

    assert isinstance(bot, Bot)

    async def _send(content: Optional[str], image: Optional[str]):
        if target_type == 'group' and target_id:
            msg = Message()
            villa_id, room_id = target_id.split('-')

            if image:
                msg += MessageSegment.image(image)
            if content:
                msg += MessageSegment.text(content)

            if at_list and target_type == 'group':
                for at in at_list:
                    msg += MessageSegment.mention_user(
                        int(at), villa_id=int(villa_id)
                    )

            if markdown:
                logger.warning('[gscore] villa暂不支持发送markdown消息')
            if buttons:
                logger.warning('[gscore] villa暂不支持发送buttons消息')

            content_info = await bot.parse_message_content(msg)

            if isinstance(content_info.content, PostMessageContent):
                object_name = "MHY:Post"
            elif isinstance(content_info.content, ImageMessageContent):
                object_name = "MHY:Image"
            else:
                object_name = "MHY:Text"

            await bot.send_message(
                villa_id=int(villa_id),
                room_id=int(room_id),
                object_name=object_name,
                msg_content=content_info.json(
                    by_alias=True, exclude_none=True
                ),
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

        result_image = (
            MessageSegment.image(image.replace('link://', '')) if image else ''
        )
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


async def onebot_red_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    file: Optional[str],
    at_list: Optional[List[str]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    from nonebot.adapters.red.bot import Bot
    from nonebot.adapters.red.api.model import ChatType
    from nonebot.adapters.red.message import Message, MessageSegment

    assert isinstance(bot, Bot)

    chat_type = ChatType.GROUP if target_type == 'group' else ChatType.FRIEND

    async def _send(content: Optional[str], image: Optional[str]):
        result_msg: Message = Message()
        if image:
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
            result_msg.append(MessageSegment.image(img_bytes))

        if content:
            result_msg.append(MessageSegment.text(content))

        if at_list and target_type == 'group':
            for at in at_list:
                result_msg += MessageSegment.at(at)

        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            result_msg += MessageSegment.file(path)

        if target_id:
            await bot.send_message(chat_type, target_id, result_msg)

        if file:
            del_file(path)  # type: ignore

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


async def discord_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    from nonebot.adapters.discord.message import parse_message
    from nonebot.adapters.discord import Bot, Message, MessageSegment

    assert isinstance(bot, Bot)

    async def _send(content: Optional[str], image: Optional[str]):
        if target_id:
            message = Message()
            if image:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
                message.append(
                    MessageSegment.attachment('temp.jpg', content=img_bytes)
                )
            if content:
                message.append(MessageSegment.text(content))

            if at_list and target_type == 'group':
                for at in at_list:
                    message.append(MessageSegment.mention_user(int(at)))

            if markdown:
                logger.warning('[gscore] discord暂不支持发送markdown消息')
            if buttons:
                logger.warning('[gscore] discord暂不支持发送markdown消息')

            message_data = parse_message(message)
            await bot.create_message(
                channel_id=int(target_id),
                nonce=None,
                tts=False,
                allowed_mentions=None,
                **message_data,
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


async def guild_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
    guild_id: Optional[str],
):
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.exception import ActionFailed

    assert isinstance(bot, qqbot)

    if target_id is None:
        return

    async def _send(content: Optional[str], image: Optional[str]):
        result: Dict[str, Any] = {'msg_id': msg_id}
        if image:
            if image.startswith('link://'):
                result['image'] = image.replace('link://', '')
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
                result['file_image'] = img_bytes
        if content:
            result['content'] = content
            if at_list and target_type == 'group':
                for at in at_list:
                    result['content'] += f'<@{at}>'
        if markdown:
            logger.warning('[gscore] qqguild暂不支持发送markdown消息')
        if buttons:
            logger.warning('[gscore] qqguild暂不支持发送buttons消息')

        if target_type == 'group':
            await bot.post_messages(
                channel_id=str(target_id),
                **result,
            )
        else:
            try:
                await bot.post_dms_messages(
                    guild_id=str(guild_id),
                    **result,
                )
            except ActionFailed:
                dms = await bot.post_dms(
                    recipient_id=str(target_id),
                    source_guild_id=str(guild_id),
                )
                if dms.guild_id:
                    await bot.post_dms_messages(
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


async def dodo_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    at_list: Optional[List[str]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
    target_type: Optional[str],
    group_id: Optional[str],
):
    from nonebot.adapters.dodo.bot import Bot as dodobot
    from nonebot.adapters.dodo.message import Message, MessageSegment

    assert isinstance(bot, dodobot)
    assert isinstance(target_id, str)

    async def __send(message: Message):
        if target_type == 'group':
            await bot.send_to_channel(
                channel_id=target_id,
                message=message,
            )
        else:
            if group_id:
                await bot.send_to_personal(group_id, target_id, message)

    async def _send(content: Optional[str], image: Optional[str]):
        message = Message()
        if image:
            img_bytes = base64.b64decode(image.replace('base64://', ''))
            image_return = await bot.set_resouce_picture_upload(file=img_bytes)
            message.append(
                MessageSegment.picture(
                    image_return.url, image_return.width, image_return.height
                )
            )
            await __send(message)
            message = Message()

        if content:
            message.append(MessageSegment.text(content))
        if markdown:
            message.append(MessageSegment.text(markdown))
        if at_list and target_type == 'group':
            for at in at_list:
                message.append(MessageSegment.at_user(at))

        if buttons:
            logger.warning('[gscore] DoDo暂不支持发送buttons消息')

        if message:
            await __send(message)

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


def _bt(button: Dict):
    from nonebot.adapters.qq.models import (
        Action,
        Button,
        Permission,
        RenderData,
    )

    return Button(
        render_data=RenderData(
            label=button['text'],
            visited_label=button['pressed_text'],
            style=button['style'],
        ),
        action=Action(
            type=button['action'],
            permission=Permission(
                type=button['permisson'],
                specify_role_ids=button['specify_role_ids'],
                specify_user_ids=button['specify_user_ids'],
            ),
            unsupport_tips=button['unsupport_tips'],
            data=button['data'],
        ),
    )


def _kb(buttons: Union[List[Dict], List[List[Dict]]]):
    from nonebot.adapters.qq.models import (
        InlineKeyboard,
        MessageKeyboard,
        InlineKeyboardRow,
    )

    _rows = []
    _buttons = []
    _buttons_rows = []
    for button in buttons:
        if isinstance(button, Dict):
            _buttons.append(_bt(button))
            if len(_buttons) >= 2:
                _rows.append(InlineKeyboardRow(buttons=_buttons))
                _buttons = []
        else:
            _buttons_rows.append([_bt(b) for b in button])

    if _buttons:
        _rows.append(InlineKeyboardRow(buttons=_buttons))
    if _buttons_rows:
        _rows.extend([InlineKeyboardRow(buttons=b) for b in _buttons_rows])

    return MessageKeyboard(content=InlineKeyboard(rows=_rows))


async def group_send(
    bot: Bot,
    content: Optional[str],
    image: Optional[str],
    node: Optional[List[Dict]],
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
):
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.message import Message, MessageSegment

    assert isinstance(bot, qqbot)
    assert isinstance(target_id, str)

    async def _send(
        content: Optional[str], image: Optional[str], msg_seq: int
    ):
        message = Message()
        if image:
            if image.startswith('link://'):
                _image = image.replace('link://', '')
            else:
                logger.warning('[gscore] qqgroup暂不支持发送本地图信息, 请转为URL发送')
                return
        else:
            _image = ''

        if content and image:
            data = f'{content}\n{_image}'
            message.append(MessageSegment.markdown(data))
        elif content:
            message.append(MessageSegment.text(content))
        elif _image:
            message.append(MessageSegment.image(_image))

        if markdown:
            _markdown = markdown.replace('link://', '')
            message.append(MessageSegment.markdown(_markdown))
        if buttons:
            message.append(MessageSegment.keyboard(_kb(buttons)))

        if target_type == 'group':
            await bot.send_to_group(
                group_id=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
            )
        else:
            await bot.send_to_c2c(
                user_id=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
            )

    msg_seq = 1
    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                image = _msg['data']
                content = None
            elif _msg['type'] == 'text':
                image = None
                content = _msg['data']
            await _send(content, image, msg_seq)
            msg_seq += 1
    else:
        await _send(content, image, msg_seq)


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
    from nonebot.adapters.kaiheila import Bot

    assert isinstance(bot, Bot)

    async def _send(content: Optional[str], image: Optional[str]):
        result = {}
        result['type'] = 1
        if image:
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))

            url = await bot.upload_file(img_bytes, 'GSUID-TEMP')
            result['type'] = 2
            result['content'] = url
        elif file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
                doc = f.read()
            url = await bot.upload_file(doc, file_name)
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
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
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
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
            data = {"image_type": "message"}
            files = {"image": img_bytes}
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
