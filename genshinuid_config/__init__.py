from ..all_import import *  # noqa: F403, F401
from ..utils.db_operation.db_operation import select_db
from ..utils.message.get_image_and_at import ImageAndAt
from .set_config import set_push_value, set_config_func
from ..utils.message.error_reply import *  # noqa: F403,F401

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


@push_config.handle()
@handle_exception('设置推送服务')
async def send_config_msg(
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    custom: ImageAndAt = Depends(),
):
    logger.info('开始执行[设置阈值信息]')
    logger.info('[设置阈值信息]参数: {}'.format(args))
    qid = event.sender.user_id
    at = custom.get_first_at()
    if qid in SUPERUSERS:
        is_admin = True
    else:
        is_admin = False

    if at and is_admin:
        qid = at
    elif at and at != qid:
        await matcher.finish('你没有权限操作别人的状态噢~', at_sender=True)
    logger.info('[设置阈值信息]qid: {}'.format(qid))

    try:
        uid = await select_db(qid, mode='uid')
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
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    matcher: Matcher,
    args: Tuple[Any, ...] = RegexGroup(),
    at: ImageAndAt = Depends(),
):
    qid = event.sender.user_id
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

    if qid in SUPERUSERS:
        is_admin = True
    else:
        is_admin = False

    if at and is_admin:
        qid = at
    elif at and at != qid:
        await matcher.finish('你没有权限操作别人的状态噢~', at_sender=True)

    try:
        uid = await select_db(qid, mode='uid')
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
