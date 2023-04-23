from typing import Optional

from PIL import Image, ImageDraw

from .etc.etc import TEXT_PATH
from .mono.Character import Character
from .curve_calc.curve_calc import draw_char_curve_data
from ..utils.fonts.genshin_fonts import genshin_font_origin
from .draw_normal import (
    get_bg_card,
    get_char_img,
    get_artifacts_card,
    get_char_card_base,
)


async def get_adv_card() -> Image.Image:
    adv_img = Image.open(TEXT_PATH / 'adv.png')
    return adv_img


async def draw_char_curve_card(
    char: Character, char_url: Optional[str]
) -> Image.Image:
    await get_artifacts_card(char, Image.new('RGB', (1, 1)))
    curve_img, curve_len = await draw_char_curve_data(
        char.char_name, char.card_prop
    )
    curve2_img, curve2_len = await draw_char_curve_data(
        char.char_name, char.fight_prop
    )
    char_img = await get_char_img(char, char_url)
    adv_img = await get_adv_card()
    img = await get_bg_card(
        char.char_element, curve_len + curve2_len + 460, char_img
    )
    img.paste(char_img, (0, 0), char_img)
    char_info_1 = await get_char_card_base(char)
    img.paste(char_info_1, (0, 0), char_info_1)
    img.paste(curve_img, (0, 1085), curve_img)
    img.paste(curve2_img, (0, 1085 + curve_len), curve2_img)
    img.paste(adv_img, (0, 1085 + curve_len + curve2_len), adv_img)
    img_text = ImageDraw.Draw(img)
    # 顶栏
    img_text.text(
        (475, 2240),
        '曲线(上)为正常面板,曲线(下)为触发各种战斗buff后面板',
        (255, 255, 255),
        genshin_font_origin(32),
        anchor='mm',
    )
    # 角色评分
    img_text.text(
        (785, 2380),
        f'{round(char.artifacts_all_score, 1)}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )
    img_text.text(
        (785, 2542),
        f'{str(char.percent)+"%"}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )
    img_text.text(
        (785, 2490),
        f'{char.seq_str}',
        (255, 255, 255),
        genshin_font_origin(18),
        anchor='mm',
    )

    img = img.convert('RGB')
    '''
    result_buffer = BytesIO()
    img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    res = result_buffer.getvalue()
    '''
    return img
