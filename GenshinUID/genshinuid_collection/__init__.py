from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.ntchat.message import Message
from nonebot.adapters.ntchat import MessageSegment, TextMessageEvent

from ..genshinuid_meta import register_menu
from ..utils.data_convert.get_uid import get_uid
from ..utils.message.error_reply import UID_HINT
from ..utils.exception.handle_exception import handle_exception
from .draw_collection_card import draw_explora_img, draw_collection_img

get_collection_info = on_command('查询收集', aliases={'收集', 'sj'}, block=True)
get_explora_info = on_command('查询探索', aliases={'探索', 'ts'}, block=True)


@get_collection_info.handle()
@handle_exception('查询收集信息')
@register_menu(
    '查询收集信息',
    '查询(@某人)收集',
    '查询你的或者指定人的宝箱收集度',
    detail_des=(
        '介绍：\n'
        '可以用来查看你的或者指定人的宝箱收集度\n'
        '可以在命令文本后带一张图以自定义背景图\n'
        ' \n'
        '指令：\n'
        '- <ft color=(238,120,0)>{查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>|uid</ft><ft color=(0,148,200)>xx</ft>'
        '<ft color=(238,120,0)>|mys</ft><ft color=(0,148,200)>xx</ft>'
        '<ft color=(238,120,0)>}</ft>'
        '<ft color=(238,120,0)>{收集|宝箱|sj|bx}</ft>\n'
        ' \n'
        '示例：\n'
        '- <ft color=(238,120,0)>查询收集</ft>\n'
        '- <ft color=(238,120,0)>uid123456789宝箱</ft>\n'
        '- <ft color=(238,120,0)>查询</ft><ft color=(0,123,67)>@无疑Wuyi'
        '</ft> <ft color=(238,120,0)>bx</ft>'
    ),
)
async def send_collection_info(
    event: TextMessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    logger.info('开始执行[查询收集信息]')
    logger.info('[查询收集信息]参数: {}'.format(args))
    raw_mes = args.extract_plain_text().strip()
    if event.at_user_list:
        qid = event.at_user_list[0]
    else:
        qid = event.from_wxid

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询收集信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_collection_img(qid, uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@get_explora_info.handle()
@handle_exception('查询探索信息')
async def send_explora_info(
    event: TextMessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
):
    logger.info('开始执行[查询探索信息]')
    logger.info('[查询探索信息]参数: {}'.format(args))
    raw_mes = args.extract_plain_text().strip()
    if event.at_user_list:
        qid = event.at_user_list[0]
    else:
        qid = event.from_wxid

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询探索信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_explora_img(qid, uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
