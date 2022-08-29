from ..all_import import *
from .add_ck import deal_ck
from .draw_user_card import get_user_card
from ..utils.db_operation.db_operation import bind_db, delete_db, switch_db


@sv.on_fullmatch('绑定信息')
async def send_bind_card(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[查询用户绑定状态]')
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return
    im = await get_user_card(qid)
    im = await convert_img(im)
    print(im)
    logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await bot.send(ev, im)


@hoshino_bot.on_message('private')  # type: ignore
async def send_add_ck_msg(ctx):
    message = ctx['raw_message']
    sid = int(ctx['self_id'])
    userid = int(ctx['sender']['user_id'])
    gid = 0
    if message.startswith('添加'):
        message = message.replace('添加', '').replace(' ', '')
        im = await deal_ck(message, userid)  # type: ignore
    else:
        return
    await hoshino_bot.send_msg(
        self_id=sid, user_id=userid, group_id=gid, message=im
    )


# 群聊内 绑定uid或者mysid 的命令，会绑定至当前qq号上
@sv.on_rex(r'^(绑定|切换|解绑|删除)(uid|UID|mys|MYS)([0-9]+)?$')
async def send_link_uid_msg(bot: HoshinoBot, ev: CQEvent):
    args = ev['match'].groups()
    logger.info('开始执行[绑定/解绑用户信息]')
    logger.info('[绑定/解绑]参数: {}'.format(str(args)))
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return
    logger.info('[绑定/解绑]UserID: {}'.format(qid))

    if args[0] in ('绑定'):
        if args[2] is None:
            await bot.send(ev, '请输入正确的uid或者mysid！')

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
    await bot.send(ev, im, at_sender=True)
