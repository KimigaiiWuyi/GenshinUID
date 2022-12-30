import asyncio
import threading
from pathlib import Path

from ..base import sv, logger
from .draw_help_card import draw_help_img
from ..utils.draw_image_tools.send_image_tool import convert_img

HELP_IMG = Path(__file__).parent / 'help.png'


@sv.on_fullmatch(('gs帮助', 'genshin帮助', 'ys帮助', '原神帮助'))
async def send_guide_pic(bot, ev):
    img = await convert_img(HELP_IMG)
    logger.info('获得gs帮助图片成功！')
    await bot.send(ev, img)


threading.Thread(
    target=lambda: asyncio.run(draw_help_img()), daemon=True
).start()
