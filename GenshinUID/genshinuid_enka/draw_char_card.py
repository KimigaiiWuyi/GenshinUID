from io import BytesIO
from typing import Tuple, Union, Optional

from PIL import Image, ImageDraw

from .mono.Fight import Character
from .dmg_calc.dmg_calc import draw_dmg_img
from .draw_char_curve import draw_char_curve_card
from .etc.etc import TEXT_PATH, get_all_artifacts_value
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from .draw_normal import (
    get_bg_card,
    get_char_img,
    get_artifacts_card,
    get_char_card_base,
)


async def draw_char_img(
    raw_data: dict,
    weapon: Optional[str] = None,
    weapon_affix: Optional[int] = None,
    talent_num: Optional[int] = None,
    charUrl: Optional[str] = None,
    is_curve: bool = False,
) -> Union[str, Tuple[bytes, Optional[bytes]]]:

    char = Character(card_prop=raw_data)
    err = await char.new(
        weapon=weapon,
        weapon_affix=weapon_affix,
        talent_num=talent_num,
    )
    if isinstance(err, str):
        return err

    await char.init_prop()

    if is_curve:
        res = await draw_char_curve_card(char, charUrl)
    else:
        res = await draw_char_card(char, charUrl)
    return res, char.char_bytes


async def get_dmg_card(
    card_prop: dict, fight_prop: dict, power_list: dict
) -> Tuple[Image.Image, int]:
    # 拿到倍率表
    if power_list == {}:
        dmg_img, dmg_len = Image.new('RGBA', (950, 1)), 0
    else:
        dmg_img, dmg_len = await draw_dmg_img(
            card_prop, power_list, fight_prop
        )
    return dmg_img, dmg_len


async def draw_char_card(char: Character, char_url: Optional[str]) -> bytes:
    dmg_img, dmg_len = await get_dmg_card(
        char.card_prop, char.fight_prop, char.power_list
    )
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
    # 角色评分
    img_text.text(
        (768, 1564),
        f'{round(artifacts_all_score, 1)}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )
    img_text.text(
        (768, 1726),
        f'{str(char.percent)+"%"}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )
    img_text.text(
        (768, 1673),
        f'{char.seq_str}',
        (255, 255, 255),
        genshin_font_origin(18),
        anchor='mm',
    )
    res = await convert_img(img)
    if isinstance(res, str):
        res = b''
    return res
