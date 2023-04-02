import asyncio
import threading

from gsuid_core.logger import logger

from ..genshinuid_resource import startup
from ..genshinuid_xkdata import draw_xk_abyss_img
from ..genshinuid_help.draw_help_card import draw_help_img
from ..genshinuid_guide.get_abyss_data import generate_data
from ..utils.resource.generate_char_card import create_all_char_card


async def all_start():
    try:
        await startup()
        await create_all_char_card()
        await draw_xk_abyss_img()
        await draw_help_img()
        await generate_data()
    except Exception as e:
        logger.exception(e)


threading.Thread(target=lambda: asyncio.run(all_start()), daemon=True).start()
