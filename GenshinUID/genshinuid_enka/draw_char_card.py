from typing import Tuple, Union, Optional

from PIL import Image

from .html_char_card import AkashaSideInject, render_char_card_html
from .mono.Character import Character


async def draw_char_img(
    char: Character,
    charUrl: Optional[str] = None,
    *,
    akasha_side: AkashaSideInject | None = None,
) -> Union[str, Tuple[Image.Image, Optional[bytes]]]:
    res = await draw_char_card(char, charUrl, akasha_side=akasha_side)
    return res, char.char_bytes


async def draw_char_card(
    char: Character,
    char_url: Optional[str],
    *,
    akasha_side: AkashaSideInject | None = None,
) -> Image.Image:
    return await render_char_card_html(char, char_url, akasha_side=akasha_side)
