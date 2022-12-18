from typing import Any, Tuple, Union

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, CommandArg
from nonebot.adapters.qqguild import Message, MessageEvent

from ..genshinuid_meta import register_menu
from ..utils.nonebot2.send import local_image
from ..utils.data_convert.get_uid import get_uid
from ..utils.message.error_reply import UID_HINT
from ..utils.message.cast_type import cast_to_int
from ..utils.message.get_image_and_at import ImageAndAt
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
        '指令：'
        '<ft color=(238,120,0)>[查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>/uidxxx/mysxxx]</ft>'
        '<ft color=(238,120,0)>[收集/宝箱/sj/bx]</ft>\n'
        ' \n'
        '可以用来查看你的或者指定人的宝箱收集度\n'
        '可以在命令文本后带一张图以自定义背景图\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>查询收集</ft>；\n'
        '<ft color=(238,120,0)>uid123456789宝箱</ft>；\n'
        '<ft color=(238,120,0)>查询</ft><ft color=(0,148,200)>@无疑Wuyi'
        '</ft> <ft color=(238,120,0)>bx</ft>'
    ),
)
async def send_collection_info(
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询收集信息]')
    logger.info('[查询收集信息]参数: {}'.format(args))
    raw_mes = args.extract_plain_text().strip()
    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    qid = str(qid)

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询收集信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_collection_img(qid, uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(local_image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@get_explora_info.handle()
@handle_exception('查询探索信息')
async def send_explora_info(
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询探索信息]')
    logger.info('[查询探索信息]参数: {}'.format(args))
    raw_mes = args.extract_plain_text().strip()
    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    qid = str(qid)

    uid = await get_uid(qid, raw_mes)
    logger.info('[查询探索信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_explora_img(qid, uid)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(local_image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
