from typing import List, Union

import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.utils.api.minigg.models import Food
from gsuid_core.utils.api.minigg.request import get_others_info

from .path import TEXT_PATH
from ..utils.colors import white_color
from ..utils.error_reply import get_error
from ..utils.get_assets import get_assets_from_ambr
from ..utils.resource.RESOURCE_PATH import WIKI_FOOD_PATH
from ..utils.image.convert import convert_img, get_str_size
from ..utils.image.image_tools import (
    get_star_png,
    get_simple_bg,
    get_unknown_png,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_22,
    gs_font_36,
    gs_font_44,
)


async def get_foods_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_others_info('foods', name)
    if isinstance(data, int):
        return get_error(data)
    elif isinstance(data, List):
        return get_error(-400)
    else:
        food_name = data['name']
        path = WIKI_FOOD_PATH / f'{food_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_foods_wiki_img(data)
    return img


async def draw_foods_wiki_img(data: Food):
    gray_color = (230, 230, 230)
    img_test = Image.new('RGBA', (1, 1))
    img_test_draw = ImageDraw.Draw(img_test)
    effect = data['effect']
    desc = data['description']

    effect = get_str_size(effect, gs_font_22, 440)
    desc = get_str_size(desc, gs_font_22, 440)

    _, _, _, y1 = img_test_draw.textbbox((0, 0), effect, gs_font_22)
    _, _, _, y2 = img_test_draw.textbbox((0, 0), desc, gs_font_22)
    w, h = 600, 750 + y1 + y2

    star_pic = get_star_png(data['rarity'])
    path = TEXT_PATH / f'UI_Buff_Item_{data["foodcategory"]}.png'
    if path.exists():
        type_pic = Image.open(path)
    else:
        type_pic = await get_assets_from_ambr(
            f'UI_Buff_Item_{data["foodcategory"]}'
        )
        if type_pic is None:
            type_pic = get_unknown_png()
    type_pic = type_pic.convert('RGBA').resize((40, 40))

    food_pic = await get_assets_from_ambr(data['images']['nameicon'])
    if food_pic is None:
        food_pic = Image.new('RGBA', (320, 320))
    else:
        food_pic = food_pic.resize((320, 320))

    bg = Image.open(TEXT_PATH / 'wiki_weapon_bg.jpg')
    img = await get_simple_bg(w, h, bg)
    img_draw = ImageDraw.Draw(img)

    img.paste(type_pic, (49, 38), type_pic)
    img_draw.text((105, 59), data['name'], white_color, gs_font_44, 'lm')
    img.paste(star_pic, (45, 83), star_pic)

    btag = Image.open(TEXT_PATH / 'btag.png')
    img.paste(btag, (50, 29), btag)

    img.paste(food_pic, (140, 119), food_pic)
    img_draw.text((45, 465), '食物类型', gray_color, gs_font_18, 'lm')
    img_draw.text((45, 500), data['foodfilter'], white_color, gs_font_36, 'lm')

    wiki_cost_tag = Image.open(TEXT_PATH / 'cost_tag.png')
    img.paste(wiki_cost_tag, (25, 550), wiki_cost_tag)

    wiki_desc_tag = Image.open(TEXT_PATH / 'desc_tag.png')
    img.paste(wiki_desc_tag, (25, 570 + y1), wiki_desc_tag)

    img_draw.text((90, 560), effect, gray_color, gs_font_22)
    img_draw.text((90, 580 + y1), desc, gray_color, gs_font_22)

    wiki_cost_bg = Image.open(TEXT_PATH / 'wiki_weapon_cost.png')
    wiki_cost_draw = ImageDraw.Draw(wiki_cost_bg)

    for index, cost in enumerate(data['ingredients']):
        cost_name = cost['name']
        material = await get_others_info('materials', cost_name)
        if isinstance(material, int):
            cost_pic = get_unknown_png()
        else:
            name_icon = material['images']['nameicon']
            _cost_pic = await get_assets_from_ambr(name_icon)
            if _cost_pic is None:
                cost_pic = get_unknown_png()
            else:
                cost_pic = _cost_pic.resize((64, 64))

        t = 100 * index
        wiki_cost_bg.paste(cost_pic, (67 + t, 46), cost_pic)
        val = str(cost['count'])
        wiki_cost_draw.text((99 + t, 123), val, white_color, gs_font_18, 'mm')

    img.paste(wiki_cost_bg, (0, 580 + y1 + y2), wiki_cost_bg)

    img = img.convert('RGB')
    img.save(
        WIKI_FOOD_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=96,
        subsampling=0,
    )
    return await convert_img(img)
