from typing import List, Literal, Optional

from hoshino import priv
from hoshino.typing import CQEvent, HoshinoBot

from .client import GsClient
from .auto_install import start, install
from .base import sv, logger, hoshino_bot
from .models import Message, MessageReceive

gsclient: Optional[GsClient] = None


async def connect():
    global gsclient
    try:
        gsclient = await GsClient().async_connect()
        await gsclient.start()
    except ConnectionRefusedError:
        logger.error('Core服务器连接失败...请稍后使用[启动core]命令启动...')


async def get_gs_msg(ev):
    if gsclient is None or not gsclient.is_alive:
        return await connect()
    # 通用字段获取
    user_id = str(ev.user_id)
    msg_id = str(ev.message_id)
    group_id = str(ev.group_id)
    self_id = str(ev.self_id)
    messages = ev.message
    message: List[Message] = []
    msg_id = ''
    sp_bot_id: Optional[str] = None
    sp_user_type: Optional[
        Literal['group', 'direct', 'channel', 'sub_channel']
    ] = None
    pm = 3

    if priv.check_priv(ev, priv.SUPERUSER):
        pm = 1
    elif priv.check_priv(ev, priv.ADMIN):
        pm = 2

    if sp_bot_id:
        bot_id = sp_bot_id
    else:
        bot_id = 'onebot'

    if ev.to_me:
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


@hoshino_bot.on_message('private')
async def send_priv_msg(ctx):
    ctx.group_id = ''
    await get_gs_msg(ctx)


@sv.on_message('group')
async def send_message(bot, ev: CQEvent):
    await get_gs_msg(ev)


@sv.on_fullmatch('gs一键安装')
async def send_install_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, '即将开始安装...会持续一段时间, 且期间无法使用Bot!')
        await bot.send(ev, await install())


@sv.on_fullmatch(('连接core', '链接core'))
async def send_connect_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.ADMIN):
        await connect()
        await bot.send(ev, '链接成功！')


@sv.on_fullmatch(('启动core'))
async def send_start_msg(bot: HoshinoBot, ev: CQEvent):
    if priv.check_priv(ev, priv.ADMIN):
        await bot.send(ev, await start())
