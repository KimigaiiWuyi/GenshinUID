from gsuid_core.gss import gss

from ..genshinuid_resource import startup
from ..genshinuid_xkdata import draw_xk_abyss_img
from ..genshinuid_help.draw_help_card import draw_help_img
from ..genshinuid_guide.get_abyss_data import generate_data


@gss.on_bot_connect
async def all_start():
    await startup()
    await draw_xk_abyss_img()
    await draw_help_img()
    await generate_data()
