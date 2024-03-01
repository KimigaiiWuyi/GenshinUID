import os
import json
import time
import uuid
import base64
import asyncio
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Union, Optional

import websockets.client
from nonebot.log import logger
from nonebot.adapters import Bot
from msgspec import json as msgjson
from nonebot import get_bot, get_bots, get_driver
from websockets.exceptions import ConnectionClosedError

from .utils import download_image
from .models import MessageSend, MessageReceive

msg_id_seq = OrderedDict()
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
                    template_buttons = ''
                    template_markdown = {}

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
                                elif _c.type == 'template_markdown':
                                    template_markdown = _c.data
                                elif _c.type == 'template_buttons':
                                    template_buttons = _c.data
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
                                template_markdown,
                                template_buttons,
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
                                buttons,
                                msg.target_id,
                            )
                        elif msg.bot_id == 'kaiheila':
                            await kaiheila_send(
                                bot,
                                content,
                                image,
                                file,
                                markdown,
                                buttons,
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
                                template_markdown,
                                template_buttons,
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
                        elif msg.bot_id == 'discord':
                            await discord_send(
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


def _bt(button: Dict):
    from nonebot.adapters.qq.models import (
        Action,
        Button,
        Permission,
        RenderData,
    )

    action = button['action']
    if action == -1:
        action = 2
    enter = None
    if action == 1:
        action = 2
        enter = True
    return Button(
        render_data=RenderData(
            label=button['text'],
            visited_label=button['pressed_text'],
            style=button['style'],
        ),
        action=Action(
            type=action,
            permission=Permission(
                type=button['permisson'],
                specify_role_ids=button['specify_role_ids'],
                specify_user_ids=button['specify_user_ids'],
            ),
            enter=enter,
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


def _villa_kb(index: int, button: Dict):
    from nonebot.adapters.villa.models import InputButton, CallbackButton

    if button['action'] == 1:
        return CallbackButton(
            id=str(index),
            text=button['text'],
            extra=button['data'],
        )
    elif button['action'] == 2:
        return InputButton(
            id=str(index),
            text=button['text'],
            input=button['data'],
        )
    else:
        return CallbackButton(
            id=str(index),
            text=button['text'],
            extra=button['data'],
        )


def _dodo_kb(button: Dict):
    from nonebot.adapters.dodo.models import CardButton, ButtonClickAction

    return CardButton(
        click=ButtonClickAction(value=button['data'], action='call_back'),
        name=button['text'],
    )


def _kaiheila_kb(button: Dict):
    action = "return-val"
    return {
        "type": "button",
        "theme": "info",
        "value": button['data'],
        "click": action,
        "text": {"type": "plain-text", "content": button['text']},
    }


def _kaiheila_kb_group(buttons: List[Dict]):
    return {
        "type": "action-group",
        "elements": [button for button in buttons],
    }


def _tg_kb(button: Dict):
    from nonebot.adapters.telegram.model import InlineKeyboardButton

    return InlineKeyboardButton(
        text=button['text'],
        callback_data=button['data'],
    )


def _dc_kb(button: Dict):
    from nonebot.adapters.discord.api import Button, ButtonStyle

    return Button(
        label=button['text'],
        custom_id=button['data'],
        style=ButtonStyle.Primary,
    )


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
    from nonebot.adapters.villa.models import Panel
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
                if image.startswith('link://'):
                    img_url = image.replace('link://', '')
                    img_url = await bot.transfer_image(url=img_url)
                else:
                    img_bytes = base64.b64decode(
                        image.replace('base64://', '')
                    )
                    img_upload = await bot.upload_image(img_bytes)
                    img_url = img_upload.url
                msg += MessageSegment.image(img_url)
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
                bt = []
                bigc = []
                midc = []
                smc = []
                for index, button in enumerate(buttons):
                    if isinstance(button, Dict):
                        bt.append(_villa_kb(index, button))
                    if isinstance(button, List):
                        if len(button) == 1:
                            bigc.append([_villa_kb(100 + index, button[0])])
                        elif len(button) == 2:
                            _t = []
                            for indexB, btn in enumerate(button):
                                _t.append(_villa_kb(200 + index + indexB, btn))
                            midc.append(_t)
                        else:
                            _t = []
                            for indexC, btn in enumerate(button):
                                _t.append(_villa_kb(300 + index + indexC, btn))
                                if len(_t) >= 3:
                                    smc.append(_t)
                                    _t = []
                            smc.append(_t)
                if bt:
                    msg += MessageSegment.components(*bt)
                else:
                    panel = Panel(
                        mid_component_group_list=midc,
                        small_component_group_list=smc,
                        big_component_group_list=bigc,
                    )

                    msg += MessageSegment.panel(panel)

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
    if target_id is None:
        return
    _target_id = int(target_id)

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
                    group_id=_target_id,
                )
            else:
                await bot.call_api(
                    'upload_private_file',
                    file=str(path.absolute()),
                    name=file_name,
                    user_id=_target_id,
                )
            del_file(path)
        else:
            if target_type == 'group':
                await bot.call_api(
                    'send_group_msg',
                    group_id=_target_id,
                    message=result_msg,
                )
            else:
                await bot.call_api(
                    'send_private_msg',
                    user_id=_target_id,
                    message=result_msg,
                )

    async def _send_node(messages):
        if target_type == 'group':
            await bot.call_api(
                'send_group_forward_msg',
                group_id=_target_id,
                messages=messages,
            )
        else:
            await bot.call_api(
                'send_private_forward_msg',
                user_id=_target_id,
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
    group_id: Optional[str],
):
    from nonebot.adapters.discord.api import ActionRow
    from nonebot.adapters.discord import Bot, Message, MessageSegment

    assert isinstance(bot, Bot)

    async def _send(content: Optional[str], image: Optional[str]):
        if group_id:
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
                bt = []
                for button in buttons:
                    if isinstance(button, Dict):
                        bt.append(_dc_kb(button))
                        if len(bt) >= 2:
                            message.append(
                                MessageSegment.component(
                                    ActionRow(components=bt)
                                )
                            )
                            bt = []
                    if isinstance(button, List):
                        _t = []
                        for i in button:
                            _t.append(_dc_kb(i))
                        else:
                            message.append(
                                MessageSegment.component(
                                    ActionRow(components=_t)
                                )
                            )
                            _t = []

            await bot.call_api('trigger_typing_indicator', channel_id=group_id)
            await bot.send_to(
                channel_id=int(group_id),
                message=message,
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
    template_markdown: Optional[Dict],
    template_buttons: Optional[str],
    target_id: Optional[str],
    target_type: Optional[str],
    msg_id: Optional[str],
    guild_id: Optional[str],
):
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.exception import ActionFailed
    from nonebot.adapters.qq.message import Message, MessageSegment
    from nonebot.adapters.qq.models import (
        MessageKeyboard,
        MessageMarkdown,
        MessageMarkdownParams,
    )

    assert isinstance(bot, qqbot)

    if target_id is None:
        return

    async def _send(content: Optional[str], image: Optional[str]):
        message = Message()
        if image:
            if image.startswith('link://'):
                message.append(
                    MessageSegment.image(image.replace('link://', ''))
                )
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
                message.append(MessageSegment.file_image(img_bytes))
        if content:
            message.append(MessageSegment.text(content))
            if at_list and target_type == 'group':
                for at in at_list:
                    message.append(MessageSegment.mention_user(at))
        if template_markdown:
            message.append(
                MessageSegment.markdown(
                    MessageMarkdown(
                        custom_template_id=template_markdown['template_id'],
                        params=[
                            MessageMarkdownParams(
                                key=key,
                                values=[template_markdown['para'][key]],
                            )
                            for key in template_markdown['para']
                        ],
                    )
                )
            )
        elif markdown:
            _markdown = markdown.replace('link://', '')
            message.append(MessageSegment.markdown(_markdown))
        if template_buttons:
            message.append(
                MessageSegment.keyboard(MessageKeyboard(id=template_buttons))
            )
        elif buttons:
            message.append(MessageSegment.keyboard(_kb(buttons)))

        if target_type == 'group':
            await bot.send_to_channel(
                channel_id=str(target_id),
                message=message,
                msg_id=msg_id,
            )
        else:
            try:
                await bot.send_to_dms(
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
                    await bot.send_to_dms(
                        guild_id=dms.guild_id,
                        message=message,
                        msg_id=msg_id,
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
    from nonebot.adapters.dodo.models import (
        CardText,
        TextData,
        CardImage,
        CardButtonGroup,
    )

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
        card = []
        message = Message()
        if image:
            if image.startswith('base64://'):
                img_bytes = base64.b64decode(image.replace('base64://', ''))
                image_return = await bot.set_resouce_picture_upload(
                    file=img_bytes
                )
                url = image_return.url
                w, h = image_return.width, image_return.height
            else:
                logger.warning('[gscore] dodo可能不支持发送URL图片, 请转为base64发送')
                url = image.replace('link://', '')
                w, h = 950, 1500

            if buttons:
                card.append(CardImage(src=url))
            else:
                message.append(MessageSegment.picture(url, w, h))
                await __send(message)
                message = Message()

        if content:
            if buttons:
                card.append(
                    CardText(text=TextData(type='plain-text', content=content))
                )
            else:
                message.append(MessageSegment.text(content))
        if markdown:
            if buttons:
                card.append(
                    CardText(text=TextData(type='dodo-md', content=markdown))
                )
            else:
                message.append(MessageSegment.text(markdown))
        if at_list and target_type == 'group':
            for at in at_list:
                message.append(MessageSegment.at_user(at))

        if buttons:
            bt = []
            for button in buttons:
                if isinstance(button, Dict):
                    bt.append(_dodo_kb(button))
                    if len(bt) >= 2:
                        card.append(CardButtonGroup(elements=bt))
                        bt = []
                if isinstance(button, List):
                    _t = []
                    for i in button:
                        _t.append(_dodo_kb(i))
                    else:
                        card.append(CardButtonGroup(elements=_t))
                        _t = []
            message.append(MessageSegment.card(components=card))

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
):
    from nonebot.adapters.qq.bot import Bot as qqbot
    from nonebot.adapters.qq.message import Message, MessageSegment
    from nonebot.adapters.qq.models import (
        MessageKeyboard,
        MessageMarkdown,
        MessageMarkdownParams,
    )

    assert isinstance(bot, qqbot)
    assert isinstance(target_id, str)

    async def _send(
        text: Optional[str], img: Optional[str], mid: Optional[str]
    ):
        message = Message()
        if img:
            if img.startswith('link://'):
                _img = img.replace('link://', '')
            else:
                logger.warning('[gscore] qqgroup暂不支持发送本地图信息, 请转为URL发送')
                return
        else:
            _img = ''

        if text and img:
            data = f'{text}\n{_img}'
            message.append(MessageSegment.markdown(data))
        elif text:
            message.append(MessageSegment.text(text))
        elif _img:
            message.append(MessageSegment.image(_img))

        if template_markdown:
            message.append(
                MessageSegment.markdown(
                    MessageMarkdown(
                        custom_template_id=template_markdown['template_id'],
                        params=[
                            MessageMarkdownParams(
                                key=key,
                                values=[template_markdown['para'][key]],
                            )
                            for key in template_markdown['para']
                        ],
                    )
                )
            )
        elif markdown:
            _markdown = markdown.replace('link://', '')
            message.append(MessageSegment.markdown(_markdown))
        if template_buttons:
            message.append(
                MessageSegment.keyboard(MessageKeyboard(id=template_buttons))
            )
        elif buttons:
            message.append(MessageSegment.keyboard(_kb(buttons)))

        if mid is None:
            msg_seq = None
        else:
            msg_seq = msg_id_seq[mid]

        if target_type == 'group':
            await bot.send_to_group(
                group_openid=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
                msg_seq=msg_seq,
            )
        else:
            await bot.send_to_c2c(
                openid=target_id,
                msg_id=msg_id,
                event_id=msg_id,
                message=message,
                msg_seq=msg_seq,
            )

        msg_id_seq[mid] += 1

    if msg_id not in msg_id_seq:
        msg_id_seq[msg_id] = 1

    if len(msg_id_seq) >= 30:
        oldest_key = next(iter(msg_id_seq))
        del msg_id_seq[oldest_key]

    if node:
        for _msg in node:
            if _msg['type'] == 'image':
                await _send(None, _msg['data'], msg_id)
            elif _msg['type'] == 'text':
                await _send(_msg['data'], None, msg_id)
    else:
        await _send(content, image, msg_id)


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
    markdown: Optional[str],
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    node: Optional[List[Dict]],
    target_id: Optional[str],
    target_type: Optional[str],
):
    from nonebot.adapters.kaiheila import Bot
    from nonebot.adapters.kaiheila.message import (
        Message,
        MessageSegment,
        _convert_to_card_message,
    )

    assert isinstance(bot, Bot)
    assert isinstance(target_id, str)

    async def _send(content: Optional[str], image: Optional[str]):
        message = Message()
        result = {}
        result['type'] = 1
        if image:
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))

            url = await bot.upload_file(img_bytes, 'GSUID-TEMP')
            message.append(MessageSegment.image(url))
        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
                doc = f.read()
            url = await bot.upload_file(doc, file_name)
            message.append(MessageSegment.file(url))
            del_file(path)
        if content:
            message.append(MessageSegment.text(content))
        if markdown:
            message.append(MessageSegment.KMarkdown(markdown))
        if buttons:
            if message:
                card_message = _convert_to_card_message(message)
                message = Message()
                card_json = json.loads(card_message.data['content'][1:-1])
                modules = card_json['modules']
            else:
                modules = []

            bt = []
            for button in buttons:
                if isinstance(button, Dict):
                    bt.append(_kaiheila_kb(button))
                    if len(bt) >= 2:
                        modules.append(_kaiheila_kb_group(bt))
                        bt = []
                if isinstance(button, List):
                    _t = []
                    for i in button:
                        _t.append(_kaiheila_kb(i))
                    else:
                        modules.append(_kaiheila_kb_group(_t))
                        _t = []

            cards = [
                {
                    "type": "card",
                    "theme": "none",
                    "size": "lg",
                    "modules": modules,
                }
            ]
            message.append(MessageSegment.Card(cards))
        if target_type == 'group':
            await bot.send_channel_msg(channel_id=target_id, message=message)
        else:
            await bot.send_private_msg(user_id=target_id, message=message)

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
    buttons: Optional[Union[List[Dict], List[List[Dict]]]],
    target_id: Optional[str],
):
    from nonebot.adapters.telegram.bot import Bot
    from nonebot.adapters.telegram.model import InlineKeyboardMarkup
    from nonebot.adapters.telegram.message import File, Entity, Message

    assert isinstance(bot, Bot)

    if target_id is None:
        return

    async def _send(content: Optional[str], image: Optional[str]):
        message = Message()
        reply_markup = None
        if image:
            if image.startswith('link://'):
                img_bytes = await download_image(image.replace('link://', ''))
            else:
                img_bytes = base64.b64decode(image.replace('base64://', ''))
            message.append(File.photo(img_bytes))
        if content:
            message.append(Entity.text(content))
        if file:
            file_name, file_content = file.split('|')
            path = Path(__file__).resolve().parent / file_name
            store_file(path, file_content)
            with open(path, 'rb') as f:
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

        await bot.send_to(target_id, message, reply_markup=reply_markup)

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
