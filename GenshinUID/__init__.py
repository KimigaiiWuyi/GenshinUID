import os
import re
import asyncio
from pathlib import Path
from base64 import b64encode
from typing import Any, List, Union, Literal, Optional

import aiofiles
from nonebot.log import logger
from nonebot.adapters import Bot
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.internal.adapter import Event
from nonebot import on_notice, get_driver, on_message, on_fullmatch

from .client import GsClient
from .auto_install import start, install
from .models import Message, MessageReceive

get_message = on_message(priority=999)
get_notice = on_notice(priority=999)
install_core = on_fullmatch('gs一键安装', permission=SUPERUSER, block=True)
start_core = on_fullmatch('启动core', permission=SUPERUSER, block=True)
connect_core = on_fullmatch(
    ('连接core', '链接core'), permission=SUPERUSER, block=True
)
driver = get_driver()
gsclient: Optional[GsClient] = None


@get_notice.handle()
async def get_notice_message(bot: Bot, ev: Event):
    if gsclient is None or not gsclient.is_alive:
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
async def send_char_adv(bot: Bot, ev: Event):
    if gsclient is None or not gsclient.is_alive:
        return await connect()

    # 通用字段获取
    sessions = ev.get_session_id().split('_')
    user_id = str(ev.get_user_id())
    messages = ev.get_message()
    raw_data = ev.__dict__
    print(raw_data)
    group_id = sessions[-2] if len(sessions) >= 2 else None
    self_id = str(bot.self_id)
    message: List[Message] = []
    msg_id = ''
    sp_bot_id: Optional[str] = None
    sp_user_type: Optional[
        Literal['group', 'direct', 'channel', 'sub_channel']
    ] = None
    pm = 6

    # qqguild
    if '_message' in raw_data:
        messages = raw_data['_message']
        if 'direct_message' in raw_data and raw_data['direct_message']:
            sp_user_type = 'direct'
            group_id = str(raw_data['guild_id'])
        else:
            group_id = str(raw_data['channel_id'])
            if 4 in raw_data['member'].roles:
                pm = 2
            elif 2 in raw_data['member'].roles:
                pm = 3
            elif 5 in raw_data['member'].roles:
                pm = 5
        msg_id = raw_data['id']
    # telegram
    elif 'telegram_model' in raw_data:
        # 如果发送者是个Bot，不响应
        if raw_data['from_'].is_bot:
            return
        messages = raw_data['message']
        # message.append(Message(type='text', data=text))
        if raw_data['chat'].type == 'group':
            sp_user_type = 'group'
            group_id = str(raw_data['chat'].id)

        else:
            sp_user_type = 'direct'
            group_id = None
        user_id = str(raw_data['from_'].id)
        msg_id = str(raw_data['message_id'])
    # kaiheila
    elif 'channel_type' in raw_data:
        # 如果发送者是个Bot，不响应
        if raw_data['event'].author.bot:
            return
        sp_bot_id = 'kaiheila'
        messages = raw_data['event'].content
        if raw_data['channel_type'] == 'GROUP':
            sp_user_type = 'group'
            group_id = raw_data['target_id']
        else:
            sp_user_type = 'direct'
            group_id = None
        user_id = raw_data['author_id']
        msg_id = raw_data['message_id']
    # onebot
    elif 'sender' in raw_data:
        if raw_data['sender'].role == 'owner':
            pm = 2
        elif raw_data['sender'].role == 'admin':
            pm = 3
        messages = raw_data['original_message']
        msg_id = str(raw_data['message_id'])
    # feishu
    elif 'schema_' in raw_data:
        messages = raw_data['event'].message.content
        for feishu_msg in messages:
            if 'image_key' in feishu_msg.data:
                feishu_msg.data['url'] = feishu_msg.data['image_key']
        if raw_data['event'].message.chat_type == 'group':
            sp_user_type = 'group'
            group_id = raw_data['event'].message.chat_id
        else:
            sp_user_type = 'direct'
            group_id = None
        user_id = raw_data['event'].sender.sender_id.union_id
        msg_id = str(raw_data['event'].message.message_id)
    # ntchat
    elif 'data' in raw_data:
        if 'chatroom' in raw_data['data']['to_wxid']:
            group_id = raw_data['data']['to_wxid']
        if 'image' in raw_data['data']:
            message.append(Message('image', raw_data['data']['image']))
        if 'from_wxid' in raw_data['data']:
            user_id = raw_data['data']['from_wxid']
            messages = raw_data['message']
            msg_id = str(raw_data['data']['msgid'])
            if (
                'raw_msg' in raw_data['data']
                and 'xml' in raw_data['data']['raw_msg']
            ):
                match = re.search(
                    r'<svrid>(\d+)</svrid>', raw_data['data']['raw_msg']
                )
                if match:
                    message.append(Message('reply', match.group(1)))
        if 'at_user_list' in raw_data['data']:
            _at_list = raw_data['data']['at_user_list']
            if _at_list:
                at_list = [Message('at', i) for i in _at_list]
                at_list.pop(0)
                message.extend(at_list)
        if 'type' in raw_data and raw_data['type'] == 11055:
            val = raw_data['file']
            name = raw_data['file_name']
            await asyncio.sleep(2)
            if (
                os.path.exists(val)
                and os.path.getsize(val) <= 5 * 1024 * 1024
                and str(name).endswith(".json")
            ):
                message.append(await convert_file(val, name))  # type: ignore
    # OneBot V12 (仅在 ComWechatClient 测试)
    if bot.adapter.get_name() == 'OneBot V12':
        # v12msgid = raw_data['id']  # V12的消息id
        # self = raw_data['self']  # 返回 platform='xxx' user_id='wxid_xxxxx'
        # platform = self.platform  # 机器人平台
        # V12还支持频道等其他平台，速速Pr！

        messages = raw_data['original_message']  # 消息
        self_id = bot.self_id  # 机器人账号ID
        msg_id = raw_data['message_id']  # 消息ID
        sp_bot_id = 'onebot_v12'

        if 'alt_message' in raw_data and '[文件]' in raw_data['alt_message']:
            file_id = messages[0].data.get('file_id')
            print('[OB12文件ID]', file_id)
            if file_id in messages[0].data.values():
                data = await get_file(bot, file_id)
                print('[OB12文件]', data)
                name = data['name']
                path = data['path']
                message.append(await convert_file(path, name))

        if 'group_id' in raw_data:
            group_id = raw_data['group_id']
            user_id = raw_data['user_id']
            sp_user_type = 'group'
        else:
            user_id = raw_data['user_id']
            sp_user_type = 'direct'

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = messages.__class__.__module__.split('.')[2]

    if await SUPERUSER(bot, ev):
        pm = 1

    if ev.is_tome():
        message.append(Message('at', self_id))

    # 处理消息
    for _msg in messages:
        message = convert_message(_msg, message)

    if not message:
        return

    user_type = 'group' if group_id else 'direct'
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


def convert_message(_msg: Any, message: List[Message]):
    if _msg.type == 'text':
        message.append(
            Message(
                'text',
                _msg.data['text']
                if 'text' in _msg.data
                else _msg.data['content'],
            )
        )
    elif _msg.type == 'image':
        file_id = _msg.data.get('file_id')
        if file_id in _msg.data.values():
            message.append(Message('image', _msg.data['file_id']))
            logger.debug('[OB12图片]', _msg.data["file_id"])
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
    return message


# 读取文件为base64
async def convert_file(
    content: Union[Path, str, bytes], file_name: str
) -> Message:
    if isinstance(content, Path):
        print(content)
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
        api="get_file",
        file_id=f"{file_id}",
        type="path",
    )
    return data
