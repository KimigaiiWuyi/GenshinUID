from pathlib import Path
from typing import Dict, Union

import aiofiles
from PIL import Image
from msgspec import json as msgjson
from gsuid_core.help.model import PluginHelp
from gsuid_core.help.draw_plugin_help import get_help
from gsuid_core.help.draw_new_plugin_help import get_new_help

from ..genshinuid_config.gs_config import gsconfig
from ..version import Genshin_version, GenshinUID_version
from ..utils.fonts.genshin_fonts import genshin_font_origin
from ..utils.image.image_tools import get_footer, get_color_bg

ICON = Path(__file__).parent.parent.parent / 'ICON.png'
TEXT_PATH = Path(__file__).parent / 'texture2d'
HELP_DATA = Path(__file__).parent / 'help.json'
ICON_PATH = Path(__file__).parent / 'icon_path'

ITEM_BG = Image.open(TEXT_PATH / 'item_bg_dark.png')
CAG_BG = Image.open(TEXT_PATH / 'cag_bg.png')
BG = Image.open(TEXT_PATH / 'bg.jpg')
BANNER_BG = Image.open(TEXT_PATH / 'banner_bg.jpg')


async def get_help_data() -> Dict[str, PluginHelp]:
    async with aiofiles.open(HELP_DATA, 'rb') as file:
        return msgjson.decode(await file.read(), type=Dict[str, PluginHelp])


async def get_core_help() -> Union[bytes, str]:
    help_data = await get_help_data()
    if help_data is None:
        return '暂未找到帮助数据...'

    column_str: str = gsconfig.get_config('help_column').data
    if column_str.isdigit():
        column = int(column_str)
    else:
        column = 6

    return await get_new_help(
        plugin_name='GenshinUID',
        plugin_info={f'v{GenshinUID_version}': ''},
        plugin_icon=Image.open(ICON),
        plugin_help=await get_help_data(),
        plugin_prefix='',
        help_mode='dark',
        banner_bg=BANNER_BG,
        cag_bg=CAG_BG,
        banner_sub_text='向着星辰与深渊！',
        help_bg=BG,
        icon_path=ICON_PATH,
        footer=get_footer(),
        column=5,
        item_bg=ITEM_BG,
        enable_cache=True,
    )

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
    return img
