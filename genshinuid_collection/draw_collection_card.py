from pathlib import Path
from typing import List, Union

from nonebot.log import logger
from PIL import Image, ImageDraw

from ..utils.get_cookies.get_cookies import GetCookies
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_simple_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2D'
collection_fg_pic = Image.open(TEXT_PATH / 'collection_fg.png')

text_color = (31, 32, 26)
gs_font_23 = genshin_font_origin(23)
gs_font_26 = genshin_font_origin(26)

based_w = 500
based_h = 750
white_overlay = Image.new('RGBA', (based_w, based_h), (255, 255, 255, 222))

max_data = {
    '成就': 649,
    '华丽的宝箱': 139,
    '珍贵的宝箱': 368,
    '精致的宝箱': 1303,
    '普通的宝箱': 1774,
}


async def dataToDataStr(max: int, my: int) -> List:
    return [
        str(100 * float('{:.2f}'.format(my / max)))
        + '% | '
        + str(my)
        + '/'
        + str(max),
        float('{:.2f}'.format(my / max)) * 450,
    ]


async def draw_collection_img(uid: str) -> Union[bytes, str]:
    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid)
    if retcode:
        return retcode
    raw_data = data_def.raw_data
    if data_def.uid:
        uid = data_def.uid

    # 获取数据
    if raw_data:
        raw_data = raw_data['data']
    else:
        return '获取数据为空!'

    # 获取背景图片各项参数
    img = await get_simple_bg(based_w, based_h)
    img.paste(white_overlay, (0, 0), white_overlay)
    img.paste(collection_fg_pic, (0, 0), collection_fg_pic)
    text_draw = ImageDraw.Draw(img)

    # 处理数据
    achieve = raw_data['stats']['achievement_number']
    chest4 = raw_data['stats']['common_chest_number']
    chest3 = raw_data['stats']['exquisite_chest_number']
    chest2 = raw_data['stats']['precious_chest_number']
    chest1 = raw_data['stats']['luxurious_chest_number']

    achieveStr = await dataToDataStr(max_data['成就'], achieve)
    chest1Str = await dataToDataStr(max_data['华丽的宝箱'], chest1)
    chest2Str = await dataToDataStr(max_data['珍贵的宝箱'], chest2)
    chest3Str = await dataToDataStr(max_data['精致的宝箱'], chest3)
    chest4Str = await dataToDataStr(max_data['普通的宝箱'], chest4)

    # 计算
    val = (
        str(
            float(
                '{:.2f}'.format(
                    (
                        achieveStr[1]
                        + chest1Str[1]
                        + chest2Str[1]
                        + chest3Str[1]
                        + chest4Str[1]
                    )
                    / 24.5
                )
            )
        )
        + '%'
    )
    left = (
        (max_data['华丽的宝箱'] - chest1) * 10
        + (max_data['珍贵的宝箱'] - chest2) * 5
        + (max_data['精致的宝箱'] - chest3) * 2
        + (max_data['普通的宝箱'] - chest4) * 0
        + (max_data['成就'] - achieve) * 5
    )

    # 用户信息
    text_draw.text(
        (50, 135),
        f'UID{uid}',
        text_color,
        gs_font_26,
        anchor='lm',
    )

    text_draw.text((130, 200), str(val), text_color, gs_font_26, anchor='lm')
    text_draw.text(
        (360, 200),
        f'约{str(left)}',
        text_color,
        gs_font_26,
        anchor='lm',
    )

    # 成就
    text_draw.text(
        (470, 275),
        achieveStr[0],
        text_color,
        gs_font_23,
        anchor='rm',
    )

    # 宝箱
    text_draw.text(
        (470, 275 + 100),
        chest1Str[0],
        text_color,
        gs_font_23,
        anchor='rm',
    )
    text_draw.text(
        (470, 275 + 100 * 2),
        chest2Str[0],
        text_color,
        gs_font_23,
        anchor='rm',
    )
    text_draw.text(
        (470, 275 + 100 * 3),
        chest3Str[0],
        text_color,
        gs_font_23,
        anchor='rm',
    )
    text_draw.text(
        (470, 275 + 100 * 4),
        chest4Str[0],
        text_color,
        gs_font_23,
        anchor='rm',
    )

    base = 304
    offset = 99.5

    # 进度条
    text_draw.rounded_rectangle(
        (23, base, 22 + achieveStr[1], base + 13),
        fill=(234, 210, 124),
        radius=20,
    )
    text_draw.rounded_rectangle(
        (23, base + offset, 22 + chest1Str[1], base + offset + 13),
        fill=(235, 173, 43),
        radius=20,
    )
    text_draw.rounded_rectangle(
        (23, base + offset * 2, 22 + chest2Str[1], base + offset * 2 + 13),
        fill=(218, 128, 248),
        radius=20,
    )
    text_draw.rounded_rectangle(
        (23, base + offset * 3, 22 + chest3Str[1], base + offset * 3 + 13),
        fill=(60, 122, 227),
        radius=20,
    )
    text_draw.rounded_rectangle(
        (23, base + offset * 4, 22 + chest4Str[1], base + offset * 4 + 13),
        fill=(168, 248, 177),
        radius=20,
    )

    res = await convert_img(img)
    return res
