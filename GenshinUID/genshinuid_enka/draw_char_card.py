from typing import Tuple, Union, Optional

from PIL import Image, ImageDraw

from .mono.Character import Character
from .dmg_calc.dmg_calc import draw_dmg_img
from ..utils.image.convert import convert_img
from .draw_char_curve import draw_char_curve_card
from .etc.etc import TEXT_PATH, get_all_artifacts_value
from ..utils.fonts.genshin_fonts import gs_font_18, gs_font_50
from .draw_normal import (
    get_bg_card,
    get_char_img,
    get_artifacts_card,
    get_char_card_base,
)


async def draw_char_img(
    char: Character,
    charUrl: Optional[str] = None,
    is_curve: bool = False,
) -> Union[str, Tuple[bytes, Optional[bytes]]]:
    if is_curve:
        res = await draw_char_curve_card(char, charUrl)
    else:
        res = await draw_char_card(char, charUrl)
    return res, char.char_bytes


async def draw_char_card(char: Character, char_url: Optional[str]) -> bytes:
    dmg_img, dmg_len = await draw_dmg_img(char)
    char_img = await get_char_img(char, char_url)
    ex_len = dmg_len * 40 + 765
    img = await get_bg_card(char.char_element, ex_len, char_img)
    img.paste(char_img, (0, 0), char_img)
    char_info_1 = await get_char_card_base(char)
    char_info_2 = Image.open(TEXT_PATH / 'char_info_2.png')
    img.paste(char_info_1, (0, 0), char_info_1)
    img.paste(char_info_2, (0, 1085), char_info_2)
    img.paste(dmg_img, (0, 1850), dmg_img)
    await get_artifacts_card(char, img)
    img_text = ImageDraw.Draw(img)
    artifacts_all_score = await get_all_artifacts_value(
        char.card_prop, char.baseHp, char.baseAtk, char.baseDef, char.char_name
    )
    if char.percent == '0.00':
        percent_str = '暂无匹配'
    else:
        percent_str = f'{char.percent}%'
    # 角色评分
    img_text.text(
        (768, 1564),
        f'{round(artifacts_all_score, 1)}',
        (255, 255, 255),
        gs_font_50,
        anchor='mm',
    )
    img_text.text(
        (768, 1726),
        percent_str,
        (255, 255, 255),
        gs_font_50,
        anchor='mm',
    )
    img_text.text(
        (768, 1673),
        f'{char.seq_str}',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )
    res = await convert_img(img)
    if isinstance(res, str):
        res = b''
    return res
