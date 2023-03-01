import asyncio
import threading
from pathlib import Path

from gsuid_core.sv import SV
from gsuid_core.bot import Bot

from .draw_help_card import draw_help_img
from ..utils.image.convert import convert_img

HELP_IMG = Path(__file__).parent / 'help.png'


@SV('原神帮助').on_fullmatch('gs帮助')
async def send_guide_pic(bot: Bot):
    img = await convert_img(HELP_IMG)
    await bot.logger.info('获得gs帮助图片成功！')
    await bot.send(img)


threading.Thread(
    target=lambda: asyncio.run(draw_help_img()), daemon=True
).start()
