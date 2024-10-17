import asyncio
import threading

from gsuid_core.logger import logger

from ..genshinuid_resource import startup

# from ..genshinuid_xkdata import draw_teyvat_abyss_img
from ..genshinuid_guide.get_new_abyss_data import download_Oceanid

# from ..genshinuid_enka.start import check_artifacts_list
# from ..genshinuid_guide.get_abyss_data import generate_data
from ..utils.resource.generate_char_card import create_all_char_card
from ..genshinuid_xkdata.get_all_char_data import (
    save_all_char_info,
    save_all_abyss_rank,
)


async def all_start():
    try:
        await download_Oceanid()
        await startup()
        # await check_artifacts_list()
        await create_all_char_card()
        # await draw_teyvat_abyss_img()
        # await generate_data()
        await save_all_char_info()
        await save_all_abyss_rank()
    except Exception as e:
        logger.exception(e)


threading.Thread(target=lambda: asyncio.run(all_start()), daemon=True).start()
