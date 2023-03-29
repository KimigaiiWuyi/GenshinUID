from typing import List, Literal, Optional

from nonebot.log import logger
from nonebot.adapters import Bot
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
connect_core = on_fullmatch(
    ('连接core', '链接core'), permission=SUPERUSER, block=True
)
driver = get_driver()
gsclient: Optional[GsClient] = None


@get_message.handle()
async def send_char_adv(bot: Bot, ev: Event):
    if gsclient is None or not gsclient.is_alive:
        return await connect()

    # 通用字段获取
    sessions = ev.get_session_id().split('_')
    user_id = str(ev.get_user_id())
    messages = ev.get_message()
    raw_data = ev.__dict__
    group_id = sessions[-2] if len(sessions) >= 2 else None
    self_id = str(bot.self_id)
    message: List[Message] = []
    msg_id = ''
    sp_bot_id: Optional[str] = None
    sp_user_type: Optional[
        Literal['group', 'direct', 'channel', 'sub_channel']
    ] = None
    pm = 3

    # qqguild
    if '_message' in raw_data:
        messages = raw_data['_message']
        if 'direct_message' in raw_data and raw_data['direct_message']:
            sp_user_type = 'direct'
            group_id = str(raw_data['guild_id'])
        else:
            group_id = str(raw_data['channel_id'])
        msg_id = raw_data['id']
        if 4 in raw_data['roles'] or 2 in raw_data['roles']:
            pm = 2
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
    # ntchat
    elif not messages and 'message' in raw_data:
        messages = raw_data['message']
        msg_id = str(raw_data['data']['msgid'])
    # onebot
    elif 'sender' in raw_data:
        if (
            raw_data['sender'].role == 'owner'
            or raw_data['sender'].role == 'admin'
        ):
            pm = 2
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
    if 'data' in raw_data:
        if 'chatroom' in raw_data['data']['to_wxid']:
            group_id = raw_data['data']['to_wxid']
        if 'image' in raw_data['data']:
            message.append(Message('image', raw_data['data']['image']))
        if 'from_wxid' in raw_data['data']:
            user_id = raw_data['data']['from_wxid']
        if 'at_user_list' in raw_data['data']:
            _at_list = raw_data['data']['at_user_list']
            if _at_list:
                at_list = [Message('at', i) for i in _at_list]
                at_list.pop(0)
                message.extend(at_list)

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = messages.__class__.__module__.split('.')[2]

    if await SUPERUSER(bot, ev):
        pm = 1

    if ev.is_tome:
        message.append(Message('at', self_id))

    # 处理消息
    for _msg in messages:
        if _msg.type == 'text':
            message.append(
                Message(
                    'text',
                    _msg.data['text'].replace('/', '')
                    if 'text' in _msg.data
                    else _msg.data['content'].replace('/', ''),
                )
            )
        elif _msg.type == 'image':
            message.append(Message('image', _msg.data['url']))
        elif _msg.type == 'at':
            message.append(Message('at', _msg.data['qq']))
        elif _msg.type == 'reply':
            message.append(Message('reply', _msg.data['id']))
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
