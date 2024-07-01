import re

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import UID_HINT

from ..utils.convert import get_uid
from .draw_poetry_abyss import draw_poetry_abyss_img

sv_poetry_abyss = SV('查询幻想真境剧诗')


@sv_poetry_abyss.on_command(
    ('查询幻想真境剧诗', '幻想真境剧诗', '新深渊', '查询新深渊', '真剧诗'),
    block=True,
)
async def send_poetry_abyss_info(bot: Bot, ev: Event):
    name = ''.join(re.findall('[\u4e00-\u9fa5]', ev.text))
    if name:
        return

    await bot.logger.info('开始执行[幻想真境剧诗]')
    uid, user_id = await get_uid(bot, ev, True)
    if uid is None:
        return await bot.send(UID_HINT)
    await bot.logger.info('[幻想真境剧诗]uid: {}'.format(uid))

    im = await draw_poetry_abyss_img(uid, ev)

    await bot.send(im)
