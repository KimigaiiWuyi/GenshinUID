from typing import List, Union

from nonebot.log import logger
from nonebot import get_driver, on_message
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent

from .client import BOT_ID, GsClient
from .models import Message, MessageReceive

get_message = on_message(priority=999)
driver = get_driver()
gsclient: GsClient


@get_message.handle()
async def send_char_adv(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)
    else:
        group_id = None
    message: List[Message] = []
    for _msg in event.message:
        if _msg.type == 'text':
            message.append(Message('text', _msg.data['text']))
        elif _msg.type == 'image':
            message.append(Message('image', _msg.data['url']))
        elif _msg.type == 'at':
            message.append(Message('at', _msg.data['qq']))
    if not message:
        return
    msg = MessageReceive(
        bot_id=BOT_ID,
        user_type='group' if group_id else 'user',
        group_id=group_id,
        user_id=str(event.user_id),
        content=message,
    )
    if gsclient is None:
        await start_client()
    logger.info(f'【发送】[gsuid-core]：{msg}')
    await gsclient._input(msg)


@driver.on_bot_connect
async def start_client():
    global gsclient
    gsclient = await GsClient().async_connect()
    await gsclient.start()
