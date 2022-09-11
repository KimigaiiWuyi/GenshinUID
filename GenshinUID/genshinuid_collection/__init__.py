from ..all_import import *  # noqa: F403,F401
from .draw_collection_card import draw_collection_img
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from ..utils.message.error_reply import *  # noqa: F403,F401
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid


@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?'
    r'(收集|宝箱|sj|bx)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
)
async def send_collection_info(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info('开始执行[查询收集信息]')
    logger.info('[查询收集信息]参数: {}'.format(args))
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    if args[2] != 'mys':
        if args[3] is None:
            uid = await select_db(qid, mode='uid')
            uid = str(uid)
        elif len(args[3]) != 9:
            return
        else:
            uid = args[3]
    else:
        uid = await convert_mysid(args[3])
    logger.info('[查询收集信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_collection_img(uid)
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')
