from gsuid_core.logger import logger
from gsuid_core.server import on_core_start

from ..genshinuid_resource import startup
from ..utils.resource.generate_char_card import create_all_char_card
from ..genshinuid_guide.get_new_abyss_data import download_Oceanid


@on_core_start
async def all_start():
    try:
        await download_Oceanid()
        await startup()
        await create_all_char_card()
    except Exception as e:
        logger.exception(e)
