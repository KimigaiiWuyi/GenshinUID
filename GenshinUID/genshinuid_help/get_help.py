from pathlib import Path
from typing import Dict, Union, Optional

import aiofiles
from PIL import Image
from msgspec import json as msgjson
from gsuid_core.help.model import PluginHelp
from gsuid_core.help.draw_plugin_help import get_help

from ..genshinuid_config.gs_config import gsconfig
from ..utils.image.image_tools import get_color_bg
from ..version import Genshin_version, GenshinUID_version
from ..utils.fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'
HELP_DATA = Path(__file__).parent / 'help.json'


async def get_help_data() -> Optional[Dict[str, PluginHelp]]:
    if HELP_DATA.exists():
        async with aiofiles.open(HELP_DATA, 'rb') as file:
            return msgjson.decode(
                await file.read(), type=Dict[str, PluginHelp]
            )


async def get_core_help() -> Union[bytes, str]:
    help_data = await get_help_data()
    if help_data is None:
        return '暂未找到帮助数据...'

    column_str: str = gsconfig.get_config('help_column').data
    if column_str.isdigit():
        column = int(column_str)
    else:
        column = 6

    img = await get_help(
        'GenshinUID',
        f'版本号：{GenshinUID_version}',
        help_data,
        await get_color_bg(1080, 1920),
        Image.open(TEXT_PATH / 'icon.png'),
        Image.open(TEXT_PATH / 'badge.png'),
        Image.open(TEXT_PATH / 'banner.png'),
        Image.open(TEXT_PATH / 'button.png'),
        genshin_font_origin,
        False,
        (5, 5, 5),
        column=column,
        extra_message=[f'数据版本 {Genshin_version}'],
    )
    return img
