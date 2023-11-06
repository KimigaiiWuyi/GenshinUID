from typing import List, Literal, Optional

from hoshino import priv
from websockets.exceptions import ConnectionClosed
from hoshino.typing import CQEvent, HoshinoBot, NoticeSession

from .client import GsClient
from .auto_install import start, install
from .base import sv, logger, hoshino_bot
from .models import Message, MessageReceive

gsclient: Optional[GsClient] = None
gsconnecting = False


async def connect():
    global gsclient
    global gsconnecting
    if not gsconnecting:
        gsconnecting = True
        try:
            gsclient = await GsClient().async_connect()
            logger.info('[gsuid-core]: 发起一次连接')
            await gsclient.start()
            gsconnecting = False
        except ConnectionRefusedError:
            gsconnecting = False
            logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')


async def get_gs_msg(ev):
    if gsclient is None:
        return await connect()

    try:
        await gsclient.ws.ping()
    except ConnectionClosed:
        await connect()

    # 通用字段获取
    user_id = str(ev.user_id)
    msg_id = str(ev.message_id)
    group_id = str(ev.group_id)
    self_id = str(ev.self_id)
    sender = ev.sender
    sender['avater'] = f'http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640'
    messages = ev.message
    message: List[Message] = []
    sp_bot_id: Optional[str] = None
    sp_user_type: Optional[
        Literal['group', 'direct', 'channel', 'sub_channel']
    ] = None
    pm = 6

    if priv.check_priv(ev, priv.SUPERUSER):
        pm = 1
    elif priv.check_priv(ev, priv.OWNER):
        pm = 2
    elif priv.check_priv(ev, priv.ADMIN):
        pm = 3

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = 'onebot'

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
        sender=sender,
        content=message,
        msg_id=msg_id,
        user_pm=pm,
    )
    logger.info(f'【发送】[gsuid-core]: {msg.bot_id}')
    await gsclient._input(msg)


@hoshino_bot.on_message('private')
async def send_priv_msg(ctx):
    ctx.group_id = ''
    await get_gs_msg(ctx)


@sv.on_message('group')
async def send_message(bot, ev: CQEvent):
    await get_gs_msg(ev)


@sv.on_notice()
async def import_gacha_log_info(session: NoticeSession):
    if gsclient is None or not gsclient.is_alive:
        return await connect()

    ev = session.event

    user_id = None
    group_id = None
    sp_user_type = None

    if (
        'message_type' not in ev
        and 'notice_type' not in ev
        and ev['notice_type'] != 'offline_file'
    ):
        return

    if 'user_id' in ev:
        user_id = str(ev['user_id'])
    if 'group_id' in ev:
        group_id = str(ev['group_id'])

    self_id = str(ev['self_id'])

    msg_id = ''
    pm = 6

    if 'message_type' in ev:
        if priv.check_priv(ev, priv.SUPERUSER):
            pm = 1
        elif priv.check_priv(ev, priv.OWNER):
            pm = 2
        elif priv.check_priv(ev, priv.ADMIN):
            pm = 3

    user_type = 'group' if group_id else 'direct'

    if 'notice_type' in ev and ev['notice_type'] in [
        'group_upload',
        'offline_file',
    ]:
        val = ev['file']['url']
        name = ev['file']['name']
        message = [Message('file', f'{name}|{val}')]
    else:
        return

    msg = MessageReceive(
        bot_id='onebot',
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


@sv.on_fullmatch('gs一键安装')
async def send_install_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, '即将开始安装...会持续一段时间, 且期间无法使用Bot!')
        await bot.send(ev, await install())


@sv.on_fullmatch(('连接core', '链接core'))
async def send_connect_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.SUPERUSER):
        await connect()
        await bot.send(ev, '链接成功！')


@sv.on_fullmatch(('启动core'))
async def send_start_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev, await start())
