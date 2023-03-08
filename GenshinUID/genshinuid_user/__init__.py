import hoshino
from hoshino.typing import CQEvent, HoshinoBot

from .topup import topup_
from ..base import sv, logger
from .qrlogin import qrcode_login
from .get_ck_help_msg import get_ck_help
from .draw_user_card import get_user_card
from ..utils.draw_image_tools.send_image_tool import convert_img
from .add_ck import deal_ck, get_ck_by_stoken, get_ck_by_all_stoken
from ..utils.db_operation.db_operation import bind_db, delete_db, switch_db

hoshino_bot = hoshino.get_bot()


@sv.on_fullmatch(('刷新全部CK', '刷新全部ck', '刷新全部Ck', '刷新全部Cookies'))
async def send_refresh_allck_msg(bot: HoshinoBot, ev: CQEvent):
    if ev.sender:
        qid = int(ev.sender['user_id'])
    else:
        return
    if qid not in bot.config.SUPERUSERS:
        return
    logger.info('开始执行[刷新全部ck]')
    im = await get_ck_by_all_stoken()
    if isinstance(im, bytes):
        im = await convert_img(im)
    await bot.send(ev, im)


@sv.on_fullmatch(('刷新CK', '刷新ck', '刷新Ck', '刷新Cookies'))
async def send_refresh_ck_msg(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[刷新ck]')
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return
    im = await get_ck_by_stoken(qid)
    if isinstance(im, bytes):
        im = await convert_img(im)
    await bot.send(ev, im)


@sv.on_fullmatch('绑定信息')
async def send_bind_card(bot: HoshinoBot, ev: CQEvent):
    logger.info('开始执行[查询用户绑定状态]')
    if ev.sender:
        qid = ev.sender['user_id']
    else:
        return
    im = await get_user_card(qid)
    im = await convert_img(im)
    logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await bot.send(ev, im)


@sv.on_fullmatch(('扫码登陆', '扫码登录', '扫码登入'))
async def send_qr_card(bot: HoshinoBot, ev: CQEvent):
    im = await qrcode_login(hoshino_bot, ev.group_id, ev.user_id)
    if not im:
        return
    im = await deal_ck(im, ev.user_id)  # type: ignore
    if isinstance(im, bytes):
        im = await convert_img(im)
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
    if isinstance(im, bytes):
        im = await convert_img(im)
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


@sv.on_fullmatch(('绑定ck说明', 'ck帮助', '绑定ck'))
async def send_ck_msg(bot: HoshinoBot, ev: CQEvent):
    msg_list = await get_ck_help()
    forward_msg = []
    for msg in msg_list:
        forward_msg.append(
            {
                "type": "node",
                "data": {"name": "小冰", "uin": "2854196306", "content": msg},
            }
        )
    await bot.send_group_forward_msg(
        group_id=ev.group_id, messages=forward_msg
    )


@sv.on_prefix(("gsrc", "原神充值"))
async def topup(bot: HoshinoBot, ev: CQEvent):
    qid = ev.user_id
    goods_id = ev.message.extract_plain_text()
    if goods_id == "":
        goods_id = 0
    else:
        goods_id = int(goods_id)
    group_id = ev.group_id
    await topup_(bot, qid, group_id, goods_id)
