import json
from typing import Dict, Union
from pathlib import Path

import aiofiles
from PIL import Image

from gsuid_core.help.model import PluginHelp
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..version import GenshinUID_version
from ..utils.message import PREFIX
from ..utils.image.image_tools import get_ICON, get_footer
from ..genshinuid_config.gs_config import gsconfig

TEXT_PATH = Path(__file__).parent / "texture2d"
HELP_DATA = Path(__file__).parent / "help.json"
ICON_PATH = Path(__file__).parent / "icon_path"

ITEM_BG = Image.open(TEXT_PATH / "item_bg_dark.png")
CAG_BG = Image.open(TEXT_PATH / "cag_bg.png")
BG = Image.open(TEXT_PATH / "bg.jpg")
BANNER_BG = Image.open(TEXT_PATH / "banner_bg.jpg")


async def get_help_data() -> Dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, "rb") as file:
        return json.loads(await file.read())


async def get_core_help() -> Union[bytes, str]:
    help_data = await get_help_data()
    column_str: str = gsconfig.get_config("help_column").data
    if column_str.isdigit():
        column = int(column_str)
    else:
        column = 6

    return await get_new_help(
        plugin_name="GenshinUID",
        plugin_info={f"v{GenshinUID_version}": ""},
        plugin_icon=get_ICON(),
        plugin_help=help_data,
        plugin_prefix=PREFIX,
        help_mode="dark",
        banner_bg=BANNER_BG,
        cag_bg=CAG_BG,
        banner_sub_text="向着星辰与深渊！",
        help_bg=BG,
        icon_path=ICON_PATH,
        footer=get_footer(),
        column=column,
        item_bg=ITEM_BG,
        enable_cache=True,
    )
