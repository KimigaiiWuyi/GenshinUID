from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from .qrlogin import qrcode_login
from ..utils.database import get_sqla
from .get_ck_help_msg import get_ck_help
from ..utils.message import send_diff_msg
from .draw_user_card import get_user_card
from .add_ck import deal_ck, get_ck_by_stoken, get_ck_by_all_stoken


@SV('用户管理', pm=2).on_fullmatch(('刷新全部CK', '刷新全部ck'))
async def send_refresh_all_ck_msg(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[刷新全部CK]')
    im = await get_ck_by_all_stoken(ev.bot_id)
    await bot.send(im)


@SV('用户添加').on_fullmatch(('刷新CK', '刷新ck'))
async def send_refresh_ck_msg(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[刷新CK]')
    im = await get_ck_by_stoken(ev.bot_id, ev.user_id)
    await bot.send(im)


@SV('扫码登陆').on_fullmatch(('扫码登陆', '扫码登录'))
async def send_qrcode_login(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[扫码登陆]')
    im = await qrcode_login(bot, ev, ev.user_id)
    if not im:
        return
    im = await deal_ck(ev.bot_id, im, ev.user_id)
    await bot.send(im)


@SV('用户信息').on_fullmatch(('绑定信息'))
async def send_bind_card(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询用户绑定状态]')
    im = await get_user_card(ev.bot_id, ev.user_id)
    await bot.logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await bot.send(im)


@SV('添加CK', area='DIRECT').on_prefix(('添加'))
async def send_add_ck_msg(bot: Bot, ev: Event):
    im = await deal_ck(ev.bot_id, ev.text, ev.user_id)
    await bot.send(im)


@SV('用户信息').on_prefix(('绑定uid', '切换uid', '删除uid', '解绑uid'))
async def send_link_uid_msg(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[绑定/解绑用户信息]')
    qid = ev.user_id
    await bot.logger.info('[绑定/解绑]UserID: {}'.format(qid))

    sqla = get_sqla(ev.bot_id)
    uid = ev.text

    if ev.command.startswith('绑定'):
        data = await sqla.insert_bind_data(qid, uid=uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'绑定UID{uid}成功！',
                -1: f'UID{uid}的位数不正确！',
                -2: f'UID{uid}已经绑定过了！',
            },
        )
    elif ev.command.startswith('切换'):
        data = await sqla.switch_uid(qid, uid=uid)
        if isinstance(data, List):
            return await bot.send(f'切换UID{uid}成功！')
        else:
            return await bot.send(f'尚未绑定该UID{uid}')
    else:
        data = await sqla.delete_bind_data(qid, uid=uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'删除UID{uid}成功！',
                -1: f'该UID{uid}不在已绑定列表中！',
            },
        )


@SV('帮助').on_fullmatch(('ck帮助', '绑定帮助'))
async def send_ck_help(bot: Bot, ev: Event):
    msg_list = await get_ck_help()
    await bot.send(MessageSegment.node(msg_list))
