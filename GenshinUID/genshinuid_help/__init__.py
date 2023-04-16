from pathlib import Path

from gsuid_core.sv import SV
from gsuid_core.bot import Bot
from gsuid_core.models import Event

from ..utils.image.convert import convert_img

HELP_IMG = Path(__file__).parent / 'help.jpg'

sv_gsuid_help = SV('原神帮助')


@sv_gsuid_help.on_fullmatch('gs帮助')
async def send_guide_pic(bot: Bot, ev: Event):
    img = await convert_img(HELP_IMG)
    await bot.logger.info('获得gs帮助图片成功！')
    await bot.send(img)
