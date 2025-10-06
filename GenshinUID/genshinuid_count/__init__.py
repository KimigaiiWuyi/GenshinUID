from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger

from ..utils.convert import get_uid
from ..utils.message import UID_HINT
from .draw_char_count import draw_char_count_list

sv_get_count = SV('毕业度统计')


@sv_get_count.on_command(('毕业度统计', '毕业都统计', '练度统计'))
async def send_charcard_list(bot: Bot, ev: Event):
    uid = await get_uid(bot, ev)
    if uid is None:
        return await bot.send(UID_HINT)
    im = await draw_char_count_list(str(uid), ev)
    logger.info(f'[毕业度统计] UID{uid}获取角色数据成功！')
    await bot.send(im)
