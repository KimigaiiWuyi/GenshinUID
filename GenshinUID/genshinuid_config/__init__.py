from typing import Any, Tuple

from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot import on_regex, on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.ntchat import Bot, MessageSegment, TextMessageEvent

from ..genshinuid_meta import register_menu
from ..utils.nonebot2.rule import FullCommand
from .draw_config_card import draw_config_img
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
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

config_card = on_command('gs配置', rule=FullCommand())


@config_card.handle()
@handle_exception('发送配置表')
@register_menu(
    '发送配置表',
    'gs配置',
    '查看插件当前配置项开关情况',
    detail_des=(
        '介绍：\n'
        '查看插件当前配置项开关情况\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>gs配置</ft>'
    ),
)
async def send_config_card(matcher: Matcher):
    logger.info('开始执行[gs配置]')
    im = await draw_config_img()
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@push_config.handle()
@handle_exception('设置推送服务')
@register_menu(
    '设置推送阈值',
    'gs设置xx(@某人)',
    '设置自己或指定人的推送服务阈值',
    detail_des=(
        '介绍：\n'
        '设置某人的推送服务阈值\n'
        '超级用户可以设置他人的推送服务阈值\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>gs设置</ft>'
        '<ft color=(0,148,200)>[服务名称][阈值]</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>gs设置推送140</ft>'
    ),
)
async def send_config_msg(
    bot: Bot,
    event: TextMessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    logger.info('开始执行[设置阈值信息]')
    logger.info('[设置阈值信息]参数: {}'.format(args))
    wxid_list = []
    wxid_list.append(event.from_wxid)
    qid = event.from_wxid
    if event.at_user_list:
        for user in event.at_user_list:
            user = user.strip()
            if user != "" and await SUPERUSER(bot, event):
                qid = user
            else:
                await matcher.finish(MessageSegment.room_at_msg(content= "{$@}你没有权限操作别人的状态噢~", at_list= wxid_list))

    logger.info('[设置阈值信息]qid: {}'.format(qid))

    try:
        uid = await select_db(qid, mode='uid')
    except TypeError:
        await matcher.finish(MessageSegment.room_at_msg(content= '{$@}'+UID_HINT, at_list= wxid_list))

    func = args[4].replace('阈值', '')
    if args[5]:
        try:
            value = int(args[5])
        except ValueError:
            await matcher.finish(MessageSegment.room_at_msg(content= "{$@}请输入数字哦~", at_list= wxid_list))
    else:
        await matcher.finish(MessageSegment.room_at_msg(content= "{$@}请输入正确的阈值数字!", at_list= wxid_list))
    logger.info('[设置阈值信息]func: {}, value: {}'.format(func, value))
    im = await set_push_value(func, str(uid), value)
    await matcher.finish(MessageSegment.room_at_msg(content= "{$@}"+f"{im}", at_list= wxid_list))


# 开启 自动签到 和 推送树脂提醒 功能
@open_and_close_switch.handle()
@register_menu(
    '开关推送服务',
    'gs{开启|关闭}xx(@某人)',
    '开关自己或指定人的推送服务状态',
    detail_des=(
        '介绍：\n'
        '设置某人的推送服务开关状态\n'
        '超级用户可以设置他人的推送服务状态\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>gs{开启|关闭}</ft>'
        '<ft color=(0,148,200)>[服务名称]</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>gs开启推送</ft>'
    ),
)
async def open_switch_func(
    bot: Bot,
    event: TextMessageEvent,
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
):
    wxid_list = []
    wxid_list.append(event.from_wxid)
    qid = event.from_wxid
    if event.at_user_list:
        for user in event.at_user_list:
            user = user.strip()
            if user != "" and await SUPERUSER(bot, event):
                qid = user
            else:
                await matcher.finish(MessageSegment.room_at_msg(content= "{$@}你没有权限操作别人的状态噢~", at_list= wxid_list))

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

    uid = await select_db(qid, mode='uid')
    if uid is None or not isinstance(uid, str) or not uid.isdecimal():
        await matcher.finish(MessageSegment.room_at_msg(content= '{$@}'+UID_HINT, at_list= wxid_list))

    im = await set_config_func(
        config_name=config_name,
        uid=uid,
        qid=str(qid),
        option=gid,
        query=query,
        is_admin=await SUPERUSER(bot, event),
    )
    await matcher.finish(MessageSegment.room_at_msg(content= "{$@}"+f"{im}", at_list= wxid_list))
