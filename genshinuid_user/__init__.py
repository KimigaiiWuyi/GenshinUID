from ..all_import import *
from .add_ck import deal_ck
from .draw_user_card import get_user_card
from ..utils.db_operation.db_operation import bind_db, delete_db, switch_db

add_cookie = on_command('添加', permission=PRIVATE_FRIEND)
bind_info = on_command('绑定信息', priority=2, block=True)
bind = on_regex(r'^(绑定|切换|解绑|删除)(uid|UID|mys|MYS)([0-9]+)?$', priority=2)


@bind_info.handle()
async def send_bind_card(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    if args:
        return
    logger.info('开始执行[查询用户绑定状态]')
    qid = event.sender.user_id
    if qid is None:
        await matcher.finish('QID为空，请重试！')
    im = await get_user_card(qid)
    logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await matcher.finish(MessageSegment.image(im))


@add_cookie.handle()
@handle_exception('Cookie', '校验失败！请输入正确的Cookies！')
async def send_add_ck_msg(
    event: MessageEvent, matcher: Matcher, args: Message = CommandArg()
):
    mes = args.extract_plain_text().strip().replace(' ', '')
    im = await deal_ck(mes, int(event.sender.user_id))  # type: ignore
    await matcher.finish(im)


# 群聊内 绑定uid或者mysid 的命令，会绑定至当前qq号上
@bind.handle()
@handle_exception('绑定ID', '绑定ID异常')
async def send_link_uid_msg(
    event: MessageEvent, matcher: Matcher, args: Tuple[Any, ...] = RegexGroup()
):
    logger.info('开始执行[绑定/解绑用户信息]')
    logger.info('[绑定/解绑]参数: {}'.format(args))
    qid = event.sender.user_id
    if qid is None:
        await matcher.finish('QID为空，请重试！')
    logger.info('[绑定/解绑]UserID: {}'.format(qid))

    if args[0] in ('绑定'):
        if args[2] is None:
            await matcher.finish('请输入正确的uid或者mysid！')

        if args[1] in ('uid', 'UID'):
            im = await bind_db(qid, args[2])
        else:
            im = await bind_db(qid, None, args[2])
    elif args[0] in ('切换'):
        im = await switch_db(qid, args[2])
    else:
        if args[1] in ('uid', 'UID'):
            im = await delete_db(qid, {'UID': args[2]})
        else:
            im = await delete_db(qid, {'MYSID': args[2]})
    await matcher.finish(im, at_sender=True)
