import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_hard_challenge import draw_hard_challenge_img

sv_hard_abyss = SV('查询肃靖险乱')


@sv_hard_abyss.on_command(
    ('查询肃靖险乱', '肃靖险乱', '新新深渊', '三路深渊', 'sjxl'),
    block=True,
)
async def send_hard_abyss_info(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    if name:
        return

    await bot.logger.info('开始执行[肃靖险乱]')
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[肃靖险乱]uid: {}'.format(uid))

    im = await draw_hard_challenge_img(uid, ev)

    await bot.send(im)
