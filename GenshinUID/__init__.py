from typing import List

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
gsclient: GsClient


@get_message.handle()
async def send_char_adv(ev: Event):
    sessions = ev.get_session_id().split('_')
    group_id = sessions[-2] if len(sessions) >= 2 else None
    user_id = str(ev.get_user_id())
    messages = ev.get_message()
    bot_id = messages.__class__.__module__.split('.')[2]
    message: List[Message] = []
    for _msg in messages:
        if _msg.type == 'text':
            message.append(Message('text', _msg.data['text']))
        elif _msg.type == 'image':
            message.append(Message('image', _msg.data['url']))
        elif _msg.type == 'at':
            message.append(Message('at', _msg.data['qq']))
    if not message:
        return
    msg = MessageReceive(
        bot_id=bot_id,
        user_type='group' if group_id else 'user',
        group_id=group_id,
        user_id=user_id,
        content=message,
    )
    if gsclient is None:
        await start_client()
    logger.info(f'【发送】[gsuid-core]: {msg}')
    await gsclient._input(msg)


@install_core.handle()
async def send_install_msg(matcher: Matcher):
    await matcher.send('即将开始安装...会持续一段时间, 且期间无法使用Bot!')
    await matcher.send(await install())


@start_core.handle()
async def send_start_msg(matcher: Matcher):
    await matcher.send(await start())


@driver.on_bot_connect
async def start_client():
    global gsclient
    gsclient = await GsClient().async_connect()
    await gsclient.start()
