from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.params import Depends, CommandArg, RegexGroup
from nonebot.adapters.qqguild import Bot, Message, MessageEvent

from ..utils.nonebot2.send import local_image
from .draw_config_card import draw_config_img
from ..utils.message.error_reply import UID_HINT
from ..utils.message.cast_type import cast_to_int
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from .set_config import set_push_value, set_config_func
from ..utils.exception.handle_exception import handle_exception

open_and_close_switch = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(gs)(开启|关闭)(.*)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$'
)

push_config = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(gs)(设置)([\u4e00-\u9fffa-zA-Z]*)([0-9]*)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$'
)

config_card = on_command('gs配置')


@config_card.handle()
@handle_exception('发送配置表')
async def send_config_card(matcher: Matcher, args: Message = CommandArg()):
    if args:
        await send_config_card.finish()
    logger.info('开始执行[gs配置]')
    im = await draw_config_img()
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(local_image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@push_config.handle()
@handle_exception('设置推送服务')
async def send_config_msg(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[设置阈值信息]')
    logger.info('[设置阈值信息]参数: {}'.format(args))
    qid = cast_to_int(event.author)
    at = custom.get_first_at()

    if at and await SUPERUSER(bot, event):
        qid = at
    elif at and at != qid:
        await matcher.finish('你没有权限操作别人的状态噢~', at_sender=True)
    logger.info('[设置阈值信息]qid: {}'.format(qid))

    try:
        uid = await select_db(str(qid), mode='uid')
    except TypeError:
        await matcher.finish(UID_HINT)

    func = args[4].replace('阈值', '')
    if args[5]:
        try:
            value = int(args[5])
        except ValueError:
            await matcher.finish('请输入数字哦~', at_sender=True)
    else:
        await matcher.finish('请输入正确的阈值数字!', at_sender=True)
    logger.info('[设置阈值信息]func: {}, value: {}'.format(func, value))
    im = await set_push_value(func, str(uid), value)
    await matcher.finish(im, at_sender=True)


# 开启 自动签到 和 推送树脂提醒 功能
@open_and_close_switch.handle()
async def open_switch_func(
    bot: Bot,
    event: MessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    at: ImageAndAt = Depends(),
):
    qid = cast_to_int(event.author)
    if at:
        at = at.get_first_at()  # type: ignore
    config_name = args[4]

    logger.info(f'[{qid}]尝试[{args[3]}]了[{config_name}]功能')

    if args[3] == '开启':
        query = 'OPEN'
        gid = (
            event.get_session_id().split('_')[1]
            if len(event.get_session_id().split('_')) == 3
            else 'on'
        )
    else:
        query = 'CLOSED'
        gid = 'off'
    is_admin = await SUPERUSER(bot, event)
    if at and is_admin:
        qid = at
    elif at and at != qid:
        await matcher.finish('你没有权限操作别人的状态噢~', at_sender=True)

    try:
        uid = await select_db(str(qid), mode='uid')
    except TypeError:
        await matcher.finish(UID_HINT)

    im = await set_config_func(
        config_name=config_name,
        uid=uid,  # type: ignore
        qid=qid,  # type: ignore
        option=gid,
        query=query,
        is_admin=is_admin,
    )
    await matcher.finish(im, at_sender=True)
