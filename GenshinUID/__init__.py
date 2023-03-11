from typing import List, Optional

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.internal.adapter import Event
from nonebot import get_driver, on_message, on_fullmatch

from .client import GsClient
from .auto_install import start, install
from .models import Message, MessageReceive

get_message = on_message(priority=999)
install_core = on_fullmatch('gs一键安装', permission=SUPERUSER, block=True)
start_core = on_fullmatch('启动core', permission=SUPERUSER, block=True)
driver = get_driver()
gsclient: Optional[GsClient] = None


@get_message.handle()
async def send_char_adv(ev: Event):
    if gsclient is None:
        return await connect()

    # 通用字段获取
    sessions = ev.get_session_id().split('_')
    user_id = str(ev.get_user_id())
    messages = ev.get_message()
    raw_data = ev.__dict__
    group_id = sessions[-2] if len(sessions) >= 2 else None
    message: List[Message] = []
    msg_id = ''

    # qqguild
    if '_message' in raw_data:
        messages = raw_data['_message']
        if 'direct_message' in raw_data and raw_data['direct_message']:
            group_id = None
            user_id = str(raw_data['guild_id'])
        else:
            group_id = str(raw_data['channel_id'])
        msg_id = raw_data['id']
    # ntchat
    elif not messages and 'message' in raw_data:
        messages = raw_data['message']
    # ntchat
    if 'data' in raw_data:
        if 'chatroom' in raw_data['data']['to_wxid']:
            group_id = raw_data['data']['to_wxid']
        if 'image' in raw_data['data']:
            message.append(Message('image', raw_data['data']['image']))
        if 'from_wxid' in raw_data['data']:
            user_id = raw_data['data']['from_wxid']
        if 'at_user_list' in raw_data['data']:
            _at_list = raw_data['data']['at_user_list']
            at_list = [Message('at', i) for i in _at_list]
            message.extend(at_list)
    bot_id = messages.__class__.__module__.split('.')[2]

    # 处理消息
    for _msg in messages:
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
            message.append(Message('image', _msg.data['url']))
        elif _msg.type == 'at':
            message.append(Message('at', _msg.data['qq']))
    if not message:
        return

    msg = MessageReceive(
        bot_id=bot_id,
        user_type='group' if group_id else 'direct',
        group_id=group_id,
        user_id=user_id,
        content=message,
        msg_id=msg_id,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)


@install_core.handle()
async def send_install_msg(matcher: Matcher):
    await matcher.send('即将开始安装...会持续一段时间, 且期间无法使用Bot!')
    await matcher.send(await install())


@start_core.handle()
async def send_start_msg(matcher: Matcher):
    await start()
    await start_client()
    await matcher.send('启动完成...')


@driver.on_bot_connect
async def start_client():
    if gsclient is None:
        await start()
    await connect()


async def connect():
    global gsclient
    try:
        gsclient = await GsClient().async_connect()
        await gsclient.start()
    except ConnectionRefusedError:
        logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')
