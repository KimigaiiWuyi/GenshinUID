from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.segment import MessageSegment
from gsuid_core.utils.database.models import GsBind

from .get_ck_help_msg import get_ck_help
from ..utils.message import send_diff_msg

sv_user_info = SV('用户信息')
sv_user_help = SV('绑定帮助')


@sv_user_info.on_command(
    (
        '绑定uid',
        '绑定UID',
        '切换uid',
        '切换UID',
        '删除uid',
        '删除UID',
        '解绑uid',
        '解绑UID',
    )
)
async def send_link_uid_msg(bot: Bot, ev: Event):
    await bot.logger.info('开始执行[绑定/解绑用户信息]')
    qid = ev.user_id
    await bot.logger.info('[绑定/解绑]UserID: {}'.format(qid))

    uid = ev.text.strip()
    if uid and not uid.isdigit():
        return await bot.send('你输入了错误的格式!')

    a = Button('🔍查询探索', '查询探索')
    b = Button('🔍查询收集', '查询收集')
    c = Button('💖刷新面板', '刷新面板')
    d2 = Button('🔔绑定UID', '绑定uid')
    d = Button('🔔绑定更多UID', '绑定uid')
    e = Button('🔄切换UID', '切换uid')
    f = Button('❌删除uid', '删除uid')

    if '绑定' in ev.command:
        data = await GsBind.insert_uid(qid, ev.bot_id, uid, ev.group_id, 9)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'绑定UID{uid}成功！',
                -1: f'UID{uid}的位数不正确！',
                -2: f'UID{uid}已经绑定过了！',
                -3: '你输入了错误的格式!',
            },
            [[d, e, f], [a, b, c]],
        )
    elif '切换' in ev.command:
        data = await GsBind.switch_uid_by_game(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'切换UID{uid}成功！',
                -1: f'不存在UID{uid}的绑定记录！',
                -2: f'UID{uid}不在绑定列表中！',
                -3: '请绑定大于等于两个UID以进行切换!',
            },
            [[d, e, f], [a, b, c]],
        )
    else:
        data = await GsBind.delete_uid(qid, ev.bot_id, uid)
        return await send_diff_msg(
            bot,
            data,
            {
                0: f'删除UID{uid}成功！',
                -1: f'该UID{uid}不在已绑定列表中！',
            },
            [[d2, e, f]],
        )


@sv_user_help.on_fullmatch(('ck帮助', '绑定帮助'))
async def send_ck_help(bot: Bot, ev: Event):
    msg_list = await get_ck_help()
    await bot.send(MessageSegment.node(msg_list))
