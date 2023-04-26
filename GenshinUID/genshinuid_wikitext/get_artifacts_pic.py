from textwrap import fill
from typing import Tuple, Union

import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.utils.api.minigg.models import Artifact
from gsuid_core.utils.api.minigg.request import get_others_info

from .path import TEXT_PATH
from ..utils.error_reply import get_error
from ..utils.image.image_tools import get_pic
from ..utils.image.convert import str_lenth, convert_img
from ..utils.resource.RESOURCE_PATH import REL_PATH, WIKI_REL_PATH
from ..utils.fonts.genshin_fonts import (
    gs_font_14,
    gs_font_22,
    gs_font_26,
    gs_font_40,
)

img1 = Image.open(TEXT_PATH / 'wiki_artifacts_bg1.png')
img2 = Image.open(TEXT_PATH / 'wiki_artifacts_bg2.png')
img3 = Image.open(TEXT_PATH / 'wiki_artifacts_bg3.png')


async def get_base_img(y1: int, y2: int) -> Tuple[Image.Image, int]:
    img_h = 250 + y1 + y2 + 30 + 500 + 50
    wrap_middle = ((img_h - 760) // 50) + 1

    result_img = Image.new('RGBA', (590, img_h))
    result_img.paste(img1, (0, 0), img1)
    result_img.paste(img3, (0, img_h - 100), img3)
    for i in range(wrap_middle):
        result_img.paste(img2, (0, 660 + i * 50), img2)

    star_bar = Image.open(TEXT_PATH / 'star_bar.png')
    result_img.paste(star_bar, (95, 215), star_bar)
    return result_img, img_h


async def get_artifacts_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_others_info('artifacts', name)
    if isinstance(data, int):
        return get_error(data)
    else:
        art_name = data['name']
        path = WIKI_REL_PATH / f'{art_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_artifacts_wiki_img(data)
    return img


async def draw_artifacts_wiki_img(data: Artifact) -> bytes:
    # 获取资源路径
    artifacts_bar_path = TEXT_PATH / 'artifacts_bar.png'
    slider_path = TEXT_PATH / 'slider.png'

    artifacts_suitbar4_path = TEXT_PATH / 'wiki_artifacts_suitbar4.png'
    artifacts_suitbar2_path = TEXT_PATH / 'wiki_artifacts_suitbar2.png'
    artifacts_suitbar1_path = TEXT_PATH / 'wiki_artifacts_suitbar1.png'

    # 转为全角字符
    """
    pc2 = ''
    pc4 = ''
    for uchar in data['2pc']:
        code = ord(uchar)
        if 32 <= code <= 126:
            code += 65248
            new_char = chr(code)
        else:
            new_char = uchar
        pc2 += new_char
    for uchar in data['4pc']:
        code = ord(uchar)
        if 32 <= code <= 126:
            code += 65248
            new_char = chr(code)
        else:
            new_char = uchar
        pc4 += new_char
    """

    if '1pc' in data:
        suitbar1 = Image.open(artifacts_suitbar1_path)
        pc1 = await str_lenth('　　　　' + data['1pc'], 22, 455)

        # 计算长度
        img_draw = ImageDraw.Draw(img1)
        _, _, _, y1 = img_draw.textbbox((0, 0), pc1, gs_font_22)
        y2 = 0
        result_img, img_h = await get_base_img(y1, y2)
        result_img.paste(suitbar1, (63, 250 + 10), suitbar1)
        pc_list = [pc1]
    else:
        suitbar4 = Image.open(artifacts_suitbar4_path)
        suitbar2 = Image.open(artifacts_suitbar2_path)
        pc2 = await str_lenth('　　　　' + data['2pc'], 22, 455)
        pc4 = await str_lenth('　　　　' + data['4pc'], 22, 455)

        # 计算长度
        img_draw = ImageDraw.Draw(img1)
        _, _, _, y1 = img_draw.textbbox((0, 0), pc2, gs_font_22)
        _, _, _, y2 = img_draw.textbbox((0, 0), pc4, gs_font_22)
        result_img, img_h = await get_base_img(y1, y2)
        result_img.paste(suitbar2, (63, 250 + 10), suitbar2)
        result_img.paste(suitbar4, (63, 250 + y1 + 40), suitbar2)

        slider = Image.open(slider_path)
        result_img.paste(slider, (0, 270 + y1), slider)
        pc_list = [pc2, pc4]

    artifacts_bar = Image.open(artifacts_bar_path)
    artifacts_bar_draw = ImageDraw.Draw(artifacts_bar)
    artifacts_list = ['flower', 'plume', 'sands', 'goblet', 'circlet']

    for index, i in enumerate(artifacts_list):
        if '1pc' in data and i != 'circlet':
            continue

        rel_path = REL_PATH / f'{data[i]["name"]}.png'

        if rel_path.exists():
            artifacts_part_img = Image.open(rel_path)
        else:
            icon_url = data['images'][i]
            if '.png' not in icon_url:
                continue
            artifacts_part_img = await get_pic(icon_url)

        artifacts_part_img = artifacts_part_img.convert('RGBA').resize(
            (70, 70)
        )
        artifacts_bar.paste(
            artifacts_part_img, (81, 37 + index * 90), artifacts_part_img
        )
        artifacts_bar_draw.text(
            (183, 58 + 90 * index),
            data[i]['name'],
            (154, 123, 51),
            gs_font_26,
            'lm',
        )
        artifacts_bar_draw.text(
            (183, 90 + 90 * index),
            fill(data[i]['description'], width=24),
            (182, 173, 165),
            gs_font_14,
            'lm',
        )

    result_img.paste(artifacts_bar, (0, 260 + y2 + y1 + 40), artifacts_bar)

    rarity = '稀有度：' + '/'.join(data['rarity'])

    text_draw = ImageDraw.Draw(result_img)
    text_draw.text((295, 182), data['name'], (154, 123, 51), gs_font_40, 'mm')
    text_draw.text((295, 230), rarity, (175, 145, 75), gs_font_22, 'mm')

    for _i, pc in enumerate(pc_list):
        pos = (63, 263 + (y1 + 30) * _i)
        text_draw.text(pos, pc, (111, 100, 80), gs_font_22)

    logo = Image.open(TEXT_PATH / 'wuyi_dark.png')
    result_img.paste(logo, (370, img_h - 30), logo)

    result_img = result_img.convert('RGB')
    result_img.save(
        WIKI_REL_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=96,
        subsampling=0,
    )
    return await convert_img(result_img)
