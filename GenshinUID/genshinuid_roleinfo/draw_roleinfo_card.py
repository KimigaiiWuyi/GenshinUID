from typing import Union

from PIL import Image
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import easy_alpha_composite

from ..utils.mys_api import get_base_data
from .draw_all_char import _draw_char_pic
from ..genshinuid_collection.draw_new_collection_card import _draw_explore
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_v4_title,
)


async def draw_pic(ev: Event, uid: str) -> Union[str, bytes]:
    img = await _draw_pic(ev, uid)
    if isinstance(img, (bytes, str)):
        return img
    elif isinstance(img, (bytearray, memoryview)):
        return bytes(img)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    return await convert_img(bg)


async def _draw_pic(ev: Event, uid: str) -> Union[str, bytes, Image.Image]:
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    char_img = await _draw_char_pic(uid, raw_data)
    explore_img = await _draw_explore(raw_data)
    if isinstance(char_img, (bytes, str)):
        return char_img
    elif isinstance(char_img, (bytearray, memoryview)):
        return bytes(char_img)

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

    w = char_img.size[0]
    h = char_img.size[1] + explore_img.size[1] + 560
    o = 150

    img = Image.new('RGBA', (w, h))

    img.paste(title_img, (0, 0), title_img)
    img = easy_alpha_composite(
        img,
        explore_img,
        (-int((explore_img.size[0] - char_img.size[0]) / 2), 500 + o),
    )
    img = easy_alpha_composite(
        img, char_img, (0, 500 + explore_img.size[1] - 110 + o)
    )
    img = add_footer(img)
    return img
