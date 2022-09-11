from .draw_roleinfo_card import draw_pic
from ..all_import import *  # noqa: F403,F401
from ..utils.db_operation.db_operation import select_db
from ..utils.mhy_api.convert_mysid_to_uid import convert_mysid


@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(uid|查询|mys)?([0-9]+)?'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$',
)
async def send_role_info(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

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

    logger.info('开始执行[查询角色信息]')
    logger.info('[查询角色信息]参数: {}'.format(args))
    logger.info('[查询角色信息]uid: {}'.format(uid))

    if '未找到绑定的UID' in uid:
        await bot.send(ev, UID_HINT)

    im = await draw_pic(uid)

    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')
