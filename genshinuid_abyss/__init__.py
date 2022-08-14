from .draw_abyss_card import draw_abyss_img
from ..all_import import *  # noqa: F403,F401
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid

get_abyss_info = on_regex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?(上期)?(深渊|sy)'
    r'(9|10|11|12|九|十|十一|十二)?(层)?'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
    block=True,
)


@get_abyss_info.handle()
@handle_exception('查询深渊信息')
async def send_abyss_info(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[查询深渊信息]')
    logger.info('[查询深渊信息]参数: {}'.format(args))
    at = custom.get_first_at()
    if at:
        qid = at
    else:
        qid = event.user_id

    # 判断uid
    if args[2] != 'mys':
        if args[3] is None:
            if args[2] is None:
                return
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])

    logger.info('[查询深渊信息]uid: {}'.format(uid))

    # 判断深渊期数
    if args[4] is None:
        schedule_type = '1'
    else:
        schedule_type = '2'
    logger.info('[查询深渊信息]深渊期数: {}'.format(schedule_type))

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
    logger.info('[查询深渊信息]深渊层数: {}'.format(floor))

    im = await draw_abyss_img(uid, floor, schedule_type)
    if isinstance(im, str):
        await matcher.finish(im)
    elif isinstance(im, bytes):
        await matcher.finish(MessageSegment.image(im))
    else:
        await matcher.finish('发生了未知错误,请联系管理员检查后台输出!')
