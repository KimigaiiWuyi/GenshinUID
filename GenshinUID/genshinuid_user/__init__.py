from typing import List

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.segment import MessageSegment

from ..utils.database import get_sqla
from .get_ck_help_msg import get_ck_help
from ..utils.message import send_diff_msg
from .draw_user_card import get_user_card

sv_user_info = SV('用户信息')
sv_user_help = SV('绑定帮助')


@sv_user_info.on_fullmatch(('绑定信息'))
async def send_bind_card(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[查询用户绑定状态]')
    im = await get_user_card(ev.bot_id, ev.user_id)
    await bot.logger.info('[查询用户绑定状态]完成!等待图片发送中...')
    await bot.send(im)


@sv_user_info.on_command(('绑定uid', '切换uid', '删除uid', '解绑uid'))
async def send_link_uid_msg(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[绑定/解绑用户信息]')
    qid = ev.user_id
    await bot.logger.info('[绑定/解绑]UserID: {}'.format(qid))

    sqla = get_sqla(ev.bot_id)
    uid = ev.text.strip()
    if uid and not uid.isdigit():
        return await bot.send('你输入了错误的格式!')

    if ev.command.startswith('绑定'):
        data = await sqla.insert_bind_data(qid, uid=uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'绑定UID{uid}成功！',
                -1: f'UID{uid}的位数不正确！',
                -2: f'UID{uid}已经绑定过了！',
                -3: '你输入了错误的格式!',
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


@sv_user_help.on_fullmatch(('ck帮助', '绑定帮助'))
async def send_ck_help(bot: Bot, ev: Event):
    msg_list = await get_ck_help()
    await bot.send(MessageSegment.node(msg_list))
