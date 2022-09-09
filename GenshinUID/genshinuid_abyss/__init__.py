from typing import Any, Tuple, Union

from nonebot.matcher import Matcher
from nonebot import logger, on_regex
from nonebot.params import Depends, RegexGroup
from nonebot.adapters.onebot.v11 import (
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from ..genshinuid_meta import register_menu
from .draw_abyss_card import draw_abyss_img
from ..utils.message.error_reply import UID_HINT
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid
from ..utils.exception.handle_exception import handle_exception

get_abyss_info = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?(上期)?(深渊|sy)'
    r'(9|10|11|12|九|十|十一|十二)?(层)?'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
    block=True,
)


@get_abyss_info.handle()
@handle_exception('查询深渊信息')
@register_menu(
    '查询深渊信息',
    '查询(@某人)(上期)深渊(xx层)',
    '查询你的或者指定人的深渊战绩',
    detail_des=(
        '指令：'
        '<ft color=(238,120,0)>[查询</ft>'
        '<ft color=(125,125,125)>(@某人)</ft>'
        '<ft color=(238,120,0)>/uidxxx/mysxxx]</ft>'
        '<ft color=(125,125,125)>(上期)</ft>'
        '<ft color=(238,120,0)>深渊</ft>'
        '<ft color=(125,125,125)>(xx层)</ft>\n'
        ' \n'  # 如果想要空行，请在换行符前面打个空格，不然会忽略换行符
        '可以用来查看你的或者指定人的深渊战绩，可以指定层数，默认为最高层数\n'
        '可以在命令文本后带一张图以自定义背景图\n'
        ' \n'
        '示例：\n'
        '<ft color=(238,120,0)>查询深渊</ft>；\n'
        '<ft color=(238,120,0)>uid123456789上期深渊</ft>；\n'
        '<ft color=(238,120,0)>查询</ft><ft color=(0,148,200)>@无疑Wuyi</ft> '
        '<ft color=(238,120,0)>上期深渊12层</ft>'
    ),
)
async def send_abyss_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询深渊信息]')
    logger.info(f'[查询深渊信息]参数: {args}')
    at = custom.get_first_at()
    qid = at or event.user_id
    if args[2] == 'mys':
        uid = await convert_mysid(args[3])
    elif args[3] is None:
        uid = await select_db(qid, mode='uid')
        uid = str(uid)
    elif len(args[3]) != 9:
        return
    else:
        uid = args[3]
    logger.info(f'[查询深渊信息]uid: {uid}')
    if '未找到绑定的UID' in uid:
        await matcher.finish(UID_HINT)
    schedule_type = '1' if args[4] is None else '2'
    logger.info(f'[查询深渊信息]深渊期数: {schedule_type}')
    if args[6] in ['九', '十', '十一', '十二']:
        floor = (
            args[6]
            .replace('九', '9')
            .replace('十一', '11')
            .replace('十二', '12')
            .replace('十', '10')
        )

    else:
        floor = args[6]
    if floor is not None:
        floor = int(floor)
    logger.info(f'[查询深渊信息]深渊层数: {floor}')
    im = await draw_abyss_img(uid, floor, schedule_type)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
