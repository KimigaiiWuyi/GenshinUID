from PIL import Image
from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.help.utils import register_help

from .get_help import ICON, get_core_help

sv_gs_help = SV('gs帮助')


@sv_gs_help.on_fullmatch(('gs帮助'))
async def send_help_img(bot: Bot, ev: Event):
    logger.info('开始执行[gs帮助]')
    im = await get_core_help()
    await bot.send(im)


register_help('GenshinUID', 'gs帮助', Image.open(ICON))
