from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .draw_gcgdesk import draw_deck_img
from .draw_gcginfo import draw_gcg_info

sv_gcg = SV('查询七圣')


@sv_gcg.on_command(('七圣召唤', 'qszh'))
async def send_gcg_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[七圣召唤]uid: {}'.format(uid))

    im = await draw_gcg_info(uid)
    await bot.send(im)


@sv_gcg.on_command(('我的卡组', '我的牌组'))
async def send_deck_pic(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[我的卡组]uid: {}'.format(uid))
    if not ev.text:
        deck_id = 1
    elif ev.text.strip().isdigit():
        deck_id = int(ev.text.strip())
    else:
        return bot.send('请输入正确的序号, 例如我的卡组1...')
    im = await draw_deck_img(ev.user_id, uid, deck_id)
    await bot.send(im)
