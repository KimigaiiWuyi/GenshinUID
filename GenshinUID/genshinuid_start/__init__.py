import asyncio
import threading

from gsuid_core.logger import logger

from ..utils.database import get_sqla
from ..genshinuid_resource import startup
from ..genshinuid_xkdata import draw_xk_abyss_img
from ..genshinuid_help.draw_help_card import draw_help_img
from ..genshinuid_guide.get_abyss_data import generate_data
from ..utils.resource.generate_char_card import create_all_char_card
from ..genshinuid_xkdata.get_all_char_data import (
    save_all_char_info,
    save_all_abyss_rank,
)


async def all_start():
    try:
        get_sqla('TEMP')
        await draw_help_img()
        await startup()
        await create_all_char_card()
        await draw_xk_abyss_img()
        await generate_data()
        await save_all_char_info()
        await save_all_abyss_rank()
    except Exception as e:
        logger.exception(e)


threading.Thread(target=lambda: asyncio.run(all_start()), daemon=True).start()
