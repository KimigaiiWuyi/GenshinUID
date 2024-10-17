from typing import List
from pathlib import Path

from PIL import Image, ImageDraw
from gsuid_core.utils.error_reply import get_error

from ..utils.image.convert import convert_img
from ..utils.api.teyvat.request import teyvat_api
from ..utils.api.teyvat.models import FakeTeyvatRank
from ..utils.resource.RESOURCE_PATH import CHAR_PATH
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.image.image_tools import get_v4_bg, add_footer
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_26,
    gs_font_30,
    gs_font_32,
    gs_font_36,
)

TEXT_PATH = Path(__file__).parent / 'texture2d2'
TOTAL_IMG = Path(__file__).parent / 'abyss_total.png'

GREY = (200, 200, 200)

COLOR_MAP = {
    'S+': (225, 67, 67),
    'S': (255, 188, 0),
    'A': (189, 0, 255),
    'B': (0, 186, 255),
    'C': (148, 204, 97),
}


async def draw_teyvat_abyss_img():
    data = await teyvat_api.get_abyss_rank()
    if isinstance(data, int):
        return get_error(data)

    version = data['version'].replace('当前版本：', '')
    data_time = data['update']
    tip1 = data['tips']
    tip2 = data['tips2']

    w, h = 1500, 500
    result = data['result'][0]

    temp_result: List[FakeTeyvatRank] = []
    for rank_data in result:
        char_lst = rank_data['list']
        h += 90
        h += (((len(char_lst) - 1) // 7) + 1) * 266
        lst = []
        for char in char_lst:
            char_name = char['name']
            for e_char in data['result'][1]:
                if e_char['name'] == char_name:
                    char['use_rate'] = e_char['use_rate']
                    lst.append(e_char)

        temp_result.append(
            {
                'rank_name': rank_data['rank_name'],
                'rank_class': rank_data['rank_class'],
                'list': lst,
            },
        )

    h += 200
    title = Image.open(TEXT_PATH / 'title_bg.png')
    title_draw = ImageDraw.Draw(title)

    title_draw.text((664, 318), version, 'white', gs_font_36, 'mm')
    title_draw.text((287, 364), data_time, GREY, gs_font_26, 'lm')

    img = get_v4_bg(w, h)
    img.paste(title, (0, 0), title)

    img_draw = ImageDraw.Draw(img)

    img_draw.text((750, h - 130), tip1, GREY, gs_font_26, 'mm')
    img_draw.text((750, h - 80), tip2, GREY, gs_font_26, 'mm')

    y = 500
    for rank_data in temp_result:
        rank_name = rank_data['rank_name']  # S+
        img_draw.rounded_rectangle(
            (50, y + 30, 1450, y + 66),
            4,
            COLOR_MAP.get(rank_name, (44, 44, 44)),
        )
        img_draw.text((750, y + 48), rank_name, 'white', gs_font_30, 'mm')

        for c_index, char in enumerate(rank_data['list']):
            char_star = char['star']
            char_use_rate = f"{char['use_rate']}%"
            use_rate_change = char['use_rate_change']
            if use_rate_change < 0:
                rate_color = (49, 165, 57)
                rate_change = f'{use_rate_change}%'
            else:
                rate_color = (255, 57, 57)
                rate_change = f'+{use_rate_change}%'

            char_bg = Image.open(TEXT_PATH / f'star{char_star}_bg.png')
            char_draw = ImageDraw.Draw(char_bg)

            char_id = await name_to_avatar_id(char['name'])
            char_path = CHAR_PATH / f'{char_id}.png'
            char = Image.open(char_path)
            char = char.resize((158, 158))
            char = char.convert('RGBA')

            char_bg.paste(char, (19, 28), char)
            char_draw.text((98, 240), '使用率', GREY, gs_font_24, 'mm')
            char_draw.text((98, 211), char_use_rate, 'white', gs_font_32, 'mm')

            char_draw.rounded_rectangle((46, 22, 150, 48), 20, rate_color)
            char_draw.text((98, 35), rate_change, 'white', gs_font_26, 'mm')

            img.paste(
                char_bg,
                (65 + (c_index % 7) * 194, y + 100 + (c_index // 7) * 266),
                char_bg,
            )
        y += (((len(rank_data['list']) - 1) // 7) + 1) * 266 + 100

    img = add_footer(img)
    img = img.convert('RGB')
    '''
    img.save(
        TOTAL_IMG,
        format='JPEG',
        quality=90,
        subsampling=0,
    )
    '''
    return await convert_img(img)
