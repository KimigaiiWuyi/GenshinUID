import os
import re
import asyncio
from pathlib import Path
from copy import deepcopy
from base64 import b64encode
from typing import Any, List, Union, Optional

import aiofiles
from nonebot.log import logger
from nonebot.adapters import Bot
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.internal.adapter import Event
from websockets.exceptions import ConnectionClosed
from nonebot import require, on_notice, on_message, on_fullmatch

require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler  # noqa:E402

from .client import GsClient, driver  # noqa:E402
from .auto_install import start, install  # noqa:E402
from .models import Message, MessageReceive  # noqa:E402

get_message = on_message(priority=999)
get_notice = on_notice(priority=999)
install_core = on_fullmatch('gs一键安装', permission=SUPERUSER, block=True)
start_core = on_fullmatch('启动core', permission=SUPERUSER, block=True)
connect_core = on_fullmatch(
    ('连接core', '链接core'), permission=SUPERUSER, block=True
)

gsclient: Optional[GsClient] = None
command_start = deepcopy(driver.config.command_start)
command_start.discard('')

if hasattr(driver.config, 'gsuid_core_repeat'):
    is_repeat = True
else:
    is_repeat = False


@get_notice.handle()
async def get_notice_message(bot: Bot, ev: Event):
    if gsclient is None:
        return await connect()

    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()

    raw_data = ev.dict()
    logger.debug(raw_data)

    try:
        user_id = str(ev.get_user_id())
    except ValueError:
        user_id = '未知'

    group_id = None
    sp_user_type = None
    sp_bot_id = None
    self_id = str(bot.self_id)
    msg_id = ''
    pm = 6

    if await SUPERUSER(bot, ev):
        pm = 1

    if 'group_id' in raw_data:
        group_id = str(raw_data['group_id'])

    if 'user_id' in raw_data:
        user_id = str(raw_data['user_id'])

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = ev.__class__.__module__.split('.')[2]

    user_type = 'group' if group_id else 'direct'

    if 'notice_type' in raw_data and raw_data['notice_type'] in [
        'group_upload',
        'offline_file',
    ]:
        val = raw_data['file']['url']
        name = raw_data['file']['name']
        message = [Message('file', f'{name}|{val}')]
        # onebot_v11
    else:
        return

    msg = MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=sp_user_type if sp_user_type else user_type,
        group_id=group_id,
        user_id=user_id,
        content=message,
        msg_id=msg_id,
        user_pm=pm,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)


@get_message.handle()
async def get_all_message(bot: Bot, ev: Event):
    if gsclient is None:
        return await connect()

    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        return await connect()

    # 通用字段获取
    group_id = None
    user_id = ev.get_user_id()
    messages = ev.get_message()
    logger.debug(ev)

    self_id = str(bot.self_id)
    message: List[Message] = []
    sp_bot_id: Optional[str] = None

    pm = 6
    msg_id = ''

    # qqguild
    if bot.adapter.get_name() == 'QQ':
        sp_bot_id = 'qqguild'
        from nonebot.adapters.qq.event import (
            GuildMessageEvent,
            C2CMessageCreateEvent,
            DirectMessageCreateEvent,
            GroupAtMessageCreateEvent,
        )

        # 私聊
        if isinstance(ev, DirectMessageCreateEvent):
            user_type = 'direct'
            group_id = str(ev.guild_id)
            msg_id = ev.id
            sender = ev.author.dict()
            sender['nickname'] = ev.author.username
        elif isinstance(ev, GroupAtMessageCreateEvent):
            sp_bot_id = 'qqgroup'
            user_type = 'group'
            group_id = str(ev.group_id)
            msg_id = ev.id
            sender = ev.author.dict()
        elif isinstance(ev, C2CMessageCreateEvent):
            sp_bot_id = 'qqgroup'
            user_type = 'direct'
            group_id = None
            msg_id = ev.id
            sender = ev.author.dict()
        # 群聊
        elif isinstance(ev, GuildMessageEvent):
            user_type = 'group'
            group_id = str(ev.channel_id)
            sender = ev.author.dict()
            sender['nickname'] = ev.author.username
            if ev.member and ev.member.roles:
                if 4 in ev.member.roles:
                    pm = 2
                elif 2 in ev.member.roles:
                    pm = 3
                elif 5 in ev.member.roles:
                    pm = 5
            msg_id = ev.id
        else:
            logger.debug('[gsuid] 不支持该 QQ Guild 事件...')
            return

        if (
            hasattr(ev, 'message_reference')
            and ev.message_reference  # type: ignore
        ):
            reply_msg_id = ev.message_reference.message_id  # type: ignore
            message.append(Message('reply', reply_msg_id))
    # telegram
    elif bot.adapter.get_name() == 'Telegram':
        from nonebot.adapters.telegram.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        if isinstance(ev, GroupMessageEvent) or isinstance(
            ev, PrivateMessageEvent
        ):
            if ev.from_.is_bot:
                return

            user_id = str(ev.from_.id)
            msg_id = str(ev.message_id)
            sender = ev.from_.dict()
            if isinstance(ev, GroupMessageEvent):
                user_type = 'group'
                group_id = str(ev.chat.id)
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 Telegram 事件...')
            return
    # kaiheila
    elif bot.adapter.get_name() == 'Kaiheila':
        from nonebot.adapters.kaiheila.event import (
            ChannelMessageEvent,
            PrivateMessageEvent,
        )

        if isinstance(ev, ChannelMessageEvent) or isinstance(
            ev, PrivateMessageEvent
        ):
            if ev.event.author.bot:
                return

            user_id = ev.author_id
            msg_id = ev.msg_id
            sender = ev.event.author.dict()
            sender.update(
                {
                    'name': ev.event.author.username,
                    'nickname': ev.event.author.nickname,
                    'avatar': ev.event.author.avatar,
                }
            )
            if isinstance(ev, ChannelMessageEvent):
                user_type = 'group'
                group_id = ev.target_id
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 kaiheila 事件...')
            return
    # onebot
    elif bot.adapter.get_name() == 'OneBot V11':
        from nonebot.adapters.onebot.v11.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        if isinstance(ev, GroupMessageEvent) or isinstance(
            ev, PrivateMessageEvent
        ):
            messages = ev.original_message
            msg_id = str(ev.message_id)
            if ev.sender.role == 'owner':
                pm = 2
            elif ev.sender.role == 'admin':
                pm = 3

            sender = ev.sender.dict(exclude_none=True)
            sender['avatar'] = f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640'

            if isinstance(ev, GroupMessageEvent):
                user_type = 'group'
                group_id = str(ev.group_id)
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 onebotv11 事件...')
            return
    elif bot.adapter.get_name() == 'Feishu':
        from nonebot.adapters.feishu.event import (
            GroupEventMessage,
            PrivateEventMessage,
        )

        if isinstance(ev, GroupEventMessage) or isinstance(
            ev, PrivateEventMessage
        ):
            for feishu_msg in messages:
                if 'image_key' in feishu_msg.data:
                    feishu_msg.data['url'] = feishu_msg.data['image_key']
            user_id = ev.get_user_id()
            msg_id = ev.message_id
            sender = {}
            if isinstance(ev, GroupEventMessage):
                user_type = 'group'
                group_id = ev.chat_id
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 Feishu 事件...')
            return
    # RedProtocol
    elif bot.adapter.get_name() == 'RedProtocol':
        from nonebot.adapters.red.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        sp_bot_id = 'onebot:red'
        if isinstance(ev, GroupMessageEvent) or isinstance(
            ev, PrivateMessageEvent
        ):
            msg_id = ev.msgId
            sender = {
                'name': ev.sendMemberName,
                'nickname': ev.sendNickName,
                'avatar': f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640',
            }
            if isinstance(ev, GroupMessageEvent):
                user_type = 'group'
                group_id = str(ev.peerUid)
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 RedProtocol 事件...')
            return
    # ntchat
    elif bot.adapter.get_name() == 'ntchat':
        from nonebot.adapters.ntchat.event import (
            FileMessageEvent,
            TextMessageEvent,
        )

        sender = {}
        if isinstance(ev, TextMessageEvent):
            user_id = ev.from_wxid
            msg_id = ev.msgid
            if 'chatroom' in ev.to_wxid:
                user_type = 'group'
                group_id = ev.to_wxid
            else:
                user_type = 'direct'
            if 'image' in ev.data:
                message.append(Message('image', ev.data['image']))
            if 'from_wxid' in ev.data:
                if 'raw_msg' in ev.data and 'xml' in ev.data['raw_msg']:
                    match = re.search(
                        r'<svrid>(\d+)</svrid>', ev.data['raw_msg']
                    )
                    if match:
                        message.append(Message('reply', match.group(1)))
            if ev.at_user_list:
                at_list = [Message('at', i) for i in ev.at_user_list]
                at_list.pop(0)
                message.extend(at_list)
        elif isinstance(ev, FileMessageEvent):
            if 'chatroom' in ev.to_wxid:
                group_id = ev.to_wxid
                user_type = 'group'
            else:
                user_type = 'direct'
            val = ev.file
            name = ev.file_name
            await asyncio.sleep(2)
            if (
                os.path.exists(val)
                and os.path.getsize(val) <= 5 * 1024 * 1024
                and str(name).endswith('.json')
            ):
                message.append(await convert_file(val, name))
        else:
            logger.debug('[gsuid] 不支持该 ntchat 事件...')
            return
    # OneBot V12 (仅在 ComWechatClient 测试)
    elif bot.adapter.get_name() == 'OneBot V12':
        from nonebot.adapters.onebot.v12.event import (
            GroupMessageEvent,
            PrivateMessageEvent,
        )

        # v12msgid = raw_data['id']  # V12的消息id
        # self = raw_data['self']  # 返回 platform='xxx' user_id='wxid_xxxxx'
        # platform = self.platform  # 机器人平台
        # V12还支持频道等其他平台，速速Pr！
        sender = {}
        if isinstance(ev, GroupMessageEvent) or isinstance(
            ev, PrivateMessageEvent
        ):
            messages = ev.original_message
            msg_id = ev.message_id
            sp_bot_id = 'onebot_v12'

            if '[文件]' in ev.alt_message:
                file_id = messages[0].data.get('file_id')
                logger.info('[OB12文件ID]', file_id)
                if file_id and file_id in messages[0].data.values():
                    data = await get_file(bot, file_id)
                    logger.info('[OB12文件]', data)
                    name = data['name']
                    path = data['path']
                    message.append(await convert_file(path, name))

            if isinstance(ev, GroupMessageEvent):
                user_type = 'group'
                group_id = ev.group_id
            else:
                user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 onebotv12 事件...')
            return
    elif bot.adapter.get_name() == 'Villa':
        from nonebot.adapters.villa import SendMessageEvent

        sender = {}
        if isinstance(ev, SendMessageEvent):
            user_type = 'group'
            msg_id = ev.msg_uid
            group_id = f'{ev.villa_id}-{ev.room_id}'
        else:
            logger.debug('[gsuid] 不支持该 Villa 事件...')
            return
    elif bot.adapter.get_name() == 'Discord':
        from nonebot.adapters.discord import (
            GuildMessageCreateEvent,
            DirectMessageCreateEvent,
        )

        sender = {}
        if isinstance(ev, GuildMessageCreateEvent):
            user_type = 'group'
            msg_id = str(ev.message_id)
            group_id = str(int(ev.channel_id))
        elif isinstance(ev, DirectMessageCreateEvent):
            msg_id = str(ev.message_id)
            user_type = 'direct'
        else:
            logger.debug('[gsuid] 不支持该 Discord 事件...')
            return

    else:
        logger.debug(f'[gsuid] 不支持该 {bot.adapter.get_name()} 事件...')
        return

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = messages.__class__.__module__.split('.')[2]

    # 确认超管权限
    if await SUPERUSER(bot, ev):
        pm = 1

    # 如果有at提及，增加AT
    if ev.is_tome():
        message.append(Message('at', self_id))

    # 处理消息
    for index, _msg in enumerate(messages):
        message = convert_message(_msg, message, index)

    if not message:
        return

    msg = MessageReceive(
        bot_id=bot_id,
        bot_self_id=self_id,
        user_type=user_type,
        group_id=group_id,
        user_id=user_id,
        sender=sender,
        content=message,
        msg_id=msg_id if msg_id else '',
        user_pm=pm,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)


@install_core.handle()
async def send_install_msg(matcher: Matcher):
    await matcher.send('即将开始安装...会持续一段时间, 且期间无法使用Bot!')
    await matcher.send(await install())


@connect_core.handle()
async def send_connect_msg(matcher: Matcher):
    await connect()
    await matcher.send('链接成功！')


@start_core.handle()
async def send_start_msg(matcher: Matcher):
    await matcher.send(await start())


@driver.on_bot_connect
async def start_client():
    if gsclient is None:
        await connect()


async def connect():
    global gsclient
    try:
        gsclient = await GsClient().async_connect()
        await gsclient.start()
    except ConnectionRefusedError:
        logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')


@scheduler.scheduled_job('cron', second='*/10')
async def repeat_connect():
    if is_repeat:
        global gsclient
        if gsclient is None:
            await connect()
        else:
            try:
                await gsclient.ws.ensure_open()
            except ConnectionClosed:
                return await connect()
        return


def convert_message(_msg: Any, message: List[Message], index: int):
    if _msg.type == 'text':
        data: str = (
            _msg.data['text'] if 'text' in _msg.data else _msg.data['content']
        )

        if index == 0:
            for word in command_start:
                if data.startswith(word):
                    data = data[len(word) :]  # noqa:E203
                    break
        message.append(Message('text', data))
    elif _msg.type == 'image':
        file_id = _msg.data.get('file_id')
        if file_id in _msg.data.values():
            message.append(Message('image', _msg.data['file_id']))
            logger.debug('[OB12图片]', _msg.data['file_id'])
        elif 'path' in _msg.data:
            message.append(Message('image', _msg.data['path']))
        else:
            message.append(Message('image', _msg.data['url']))
    elif _msg.type == 'at':
        message.append(Message('at', _msg.data['qq']))
    elif _msg.type == 'reply':
        message_id = _msg.data.get('message_id')
        if message_id in _msg.data.values():
            message.append(Message('reply', _msg.data['message_id']))
        else:
            message.append(Message('reply', _msg.data['id']))
    elif _msg.type == 'mention':
        if 'user_id' in _msg.data:
            message.append(Message('at', _msg.data['user_id']))
    elif _msg.type == 'wx.link':
        data: str = f"title: {_msg.data['title']} url: {_msg.data['url']}"
        message.append(Message('text', data))
    return message


# 读取文件为base64
async def convert_file(
    content: Union[Path, str, bytes], file_name: str
) -> Message:
    if isinstance(content, Path):
        async with aiofiles.open(str(content), 'rb') as fp:
            file = await fp.read()
    elif isinstance(content, bytes):
        file = content
    else:
        async with aiofiles.open(content, 'rb') as fp:
            file = await fp.read()
    return Message(
        type='file',
        data=f'{file_name}|{b64encode(file).decode()}',
    )


# 获取文件
async def get_file(bot: Bot, file_id: str):
    data = await bot.call_api(
        api='get_file',
        file_id=f'{file_id}',
        type='path',
    )
    return data
