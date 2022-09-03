from .draw_config_card import draw_config_img
from ..all_import import *  # noqa: F403, F401
from ..utils.db_operation.db_operation import select_db
from .set_config import set_push_value, set_config_func
from ..utils.message.error_reply import *  # noqa: F403,F401


@sv.on_fullmatch('gs配置')
async def send_config_card(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[gs配置]')
    im = await draw_config_img()
    if isinstance(im, str):
        await bot.send(ev, im)
    elif isinstance(im, bytes):
        im = await convert_img(im)
        await bot.send(ev, im)
    else:
        await bot.send(ev, '发生了未知错误,请联系管理员检查后台输出!')


@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(gs)(设置)([\u4e00-\u9fffa-zA-Z]*)([0-9]*)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$'
)
async def send_config_msg(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info('开始执行[设置阈值信息]')
    logger.info('[设置阈值信息]参数: {}'.format(args))

    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    if qid in bot.config.SUPERUSERS:
        is_admin = True
    else:
        is_admin = False

    if at and is_admin:
        qid = at
    elif at and at != qid:
        await bot.send(ev, '你没有权限操作别人的状态噢~', at_sender=True)
    logger.info('[设置阈值信息]qid: {}'.format(qid))

    try:
        uid = await select_db(qid, mode='uid')
    except TypeError:
        await bot.send(ev, UID_HINT)
        return

    func = args[4].replace('阈值', '')
    if args[5]:
        try:
            value = int(args[5])
        except ValueError:
            await bot.send(ev, '请输入数字哦~', at_sender=True)
            return
    else:
        await bot.send(ev, '请输入正确的阈值数字!', at_sender=True)
        return
    logger.info('[设置阈值信息]func: {}, value: {}'.format(func, value))
    im = await set_push_value(func, str(uid), value)
    await bot.send(ev, im, at_sender=True)


# 开启 自动签到 和 推送树脂提醒 功能
@sv.on_rex(
    r'^(\[CQ:at,qq=[0-9]+\])?( )?'
    r'(gs)(开启|关闭)(.*)'
    r'(\[CQ:at,qq=[0-9]+\])?( )?$'
)
async def open_switch_func(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    at = re.search(r'\[CQ:at,qq=(\d*)]', str(ev.message))

    if at:
        qid = int(at.group(1))
    else:
        if ev.sender:
            qid = int(ev.sender['user_id'])
        else:
            return

    config_name = args[4]

    logger.info(f'[{qid}]尝试[{args[3]}]了[{config_name}]功能')

    if args[3] == '开启':
        query = 'OPEN'
        gid = str(ev.group_id) if ev.group_id else 'on'
    else:
        query = 'CLOSED'
        gid = 'off'

    if qid in bot.config.SUPERUSERS:
        is_admin = True
    else:
        is_admin = False

    if at and is_admin:
        qid = at
    elif at and at != qid:
        bot.send(ev, '你没有权限操作别人的状态噢~', at_sender=True)
        return

    try:
        uid = await select_db(qid, mode='uid')
    except TypeError:
        await bot.send(ev, UID_HINT)
        return

    im = await set_config_func(
        config_name=config_name,
        uid=uid,  # type: ignore
        qid=qid,  # type: ignore
        option=gid,
        query=query,
        is_admin=is_admin,
    )
    await bot.send(ev, im, at_sender=True)
