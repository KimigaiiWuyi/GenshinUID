import re

from nonebot import on_command
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import Depends, CommandArg
from nonebot.adapters.qqguild import Message, MessageEvent, MessageSegment

from .get_regtime import calc_reg_time
from .draw_roleinfo_card import draw_pic
from ..utils.nonebot2.rule import FullCommand
from ..utils.message.error_reply import UID_HINT
from ..utils.message.cast_type import cast_to_int
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.exception.handle_exception import handle_exception

get_role_info = on_command('uid', aliases={'查询'})
get_reg_time = on_command(
    '原神注册时间', aliases={'注册时间', '查询注册时间'}, rule=FullCommand()
)


@get_role_info.handle()
@handle_exception('查询角色信息')
async def send_role_info(
    event: MessageEvent,
    matcher: Matcher,
    args: Message = CommandArg(),
    custom: ImageAndAt = Depends(),
):
    raw_mes = args.extract_plain_text().strip().replace(' ', '')
    name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
    if name:
        return

    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    if at:
        qid = at
    qid = str(qid)

    # 获取uid
    uid = re.findall(r'\d+', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    logger.info('开始执行[查询角色信息]')

    logger.info('[查询角色信息]参数: {}'.format(args))
    logger.info('[查询角色信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await draw_pic(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.file_image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')


@get_reg_time.handle()
async def regtime(
    event: MessageEvent,
    matcher: Matcher,
    custom: ImageAndAt = Depends(),
):
    at = custom.get_first_at()
    qid = at or cast_to_int(event.author)
    if at:
        qid = at
    qid = str(qid)

    uid = await select_db(qid, mode='uid')
    uid = str(uid)

    logger.info('开始执行[查询注册时间]')
    logger.info('[查询注册时间]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)

    im = await calc_reg_time(uid)

    if isinstance(im, str):
        await matcher.finish(im)
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
