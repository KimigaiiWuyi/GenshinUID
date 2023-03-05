import asyncio
import threading

from ..genshinuid_resource import startup
from ..genshinuid_xkdata import draw_xk_abyss_img
from ..genshinuid_help.draw_help_card import draw_help_img


async def all_start():
    await startup()
    await draw_xk_abyss_img()
    await draw_help_img()


threading.Thread(target=lambda: asyncio.run(all_start()), daemon=True).start()
