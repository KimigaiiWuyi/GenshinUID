import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.message_models import Button
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .draw_abyss_card import draw_abyss_img

sv_abyss = SV('查询深渊')


@sv_abyss.on_command(
    ('查询深渊', 'sy', '查询上期深渊', 'sqsy', '上期深渊', '深渊'), block=True
)
async def send_abyss_info(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    if name:
        return

    await bot.logger.info('开始执行[查询深渊信息]')
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[查询深渊信息]uid: {}'.format(uid))

    if 'sq' in ev.command or '上期' in ev.command:
        schedule_type = '2'
    else:
        schedule_type = '1'
    await bot.logger.info('[查询深渊信息]深渊期数: {}'.format(schedule_type))

    if ev.text in ['九', '十', '十一', '十二']:
        floor = (
            ev.text.replace('九', '9')
            .replace('十一', '11')
            .replace('十二', '12')
            .replace('十', '10')
        )
    else:
        floor = ev.text
    if floor and floor.isdigit():
        floor = int(floor)
    else:
        floor = None

    await bot.logger.info('[查询深渊信息]深渊层数: {}'.format(floor))

    im = await draw_abyss_img(user_id, uid, floor, schedule_type)
    a = Button('🔍查询深渊11', '查询深渊11')
    b = Button('🔚查询上期深渊', '查询上期深渊')
    c = Button('♾️深渊概览', '深渊概览')
    d = Button('👾怪物阵容', '版本深渊')
    await bot.send_option(im, [a, b, c, d])
