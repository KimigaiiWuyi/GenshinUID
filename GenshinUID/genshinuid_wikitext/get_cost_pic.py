from typing import Dict, List, Tuple, Union

import aiofiles
from PIL import Image, ImageDraw

from .path import TEXT_PATH
from ..utils.colors import white_color
from ..utils.error_reply import get_error
from ..utils.get_assets import get_assets_from_ambr
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.image.convert import str_lenth, convert_img
from ..gsuid_utils.api.minigg.models import Character, CharacterTalents
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, WIKI_COST_CHAR_PATH
from ..gsuid_utils.api.minigg.request import (
    get_others_info,
    get_talent_info,
    get_character_info,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_26,
    gs_font_30,
    gs_font_36,
    gs_font_44,
)
from ..utils.image.image_tools import (
    get_star_png,
    get_simple_bg,
    get_unknown_png,
    draw_pic_with_ring,
)


async def get_char_cost_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_character_info(name)
    talent_data = await get_talent_info(name)
    if isinstance(data, int):
        return get_error(data)
    elif isinstance(data, List):
        return get_error(-400)
    elif isinstance(talent_data, int):
        return get_error(talent_data)
    else:
        char_name = talent_data['name']
        path = WIKI_COST_CHAR_PATH / f'{char_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_char_cost_img(data, talent_data)
    return img


async def draw_single_cost(title: str, data: Dict) -> Tuple[Image.Image, str]:
    img = Image.new('RGBA', (900, 450))
    img_draw = ImageDraw.Draw(img)
    wiki_cost_bg = Image.open(TEXT_PATH / 'wiki_weapon_cost.png').resize(
        (900, 255)
    )
    cost_bg = Image.open(TEXT_PATH / 'cost_bg.png')
    img.paste(cost_bg, (0, 0), cost_bg)
    img.paste(wiki_cost_bg, (0, 15), wiki_cost_bg)
    img.paste(wiki_cost_bg, (0, 180), wiki_cost_bg)

    wiki_cost_tag = Image.open(TEXT_PATH / 'cost_tag.png').resize((75, 75))
    img.paste(wiki_cost_tag, (65, -20), wiki_cost_tag)
    img_draw.text((130, 22), title, white_color, gs_font_36, 'lm')
    cost_pos = ''
    for index, cost_name in enumerate(data):
        material = await get_others_info('materials', cost_name)
        if isinstance(material, int):
            cost_pic = get_unknown_png()
        else:
            name_icon = material['images']['nameicon']
            _cost_pic = await get_assets_from_ambr(name_icon)
            if _cost_pic is None:
                cost_pic = get_unknown_png().resize((96, 96))
            else:
                cost_pic = _cost_pic.resize((96, 96))

            if (
                material['materialtype'] == '武器突破素材'
                or material['materialtype'] == '角色天赋素材'
            ) and 'daysofweek' in material:
                pos = material['dropdomain']
                days = material['daysofweek']
                if '周日' in days:
                    days.remove('周日')
                cost_pos = f'{pos} - {"/".join(days)}'
            else:
                cost_pos = ''

        t = 150 * (index % 5)
        y = 165 * (index // 5)
        tent_x = 34
        tent_y = 23
        img.paste(cost_pic, (67 + tent_x + t, 61 + tent_y + y), cost_pic)
        val = str(data[cost_name])
        img_draw.text(
            (114 + tent_x + t, 175 + tent_y + y),
            val,
            white_color,
            gs_font_26,
            'mm',
        )
    return img, cost_pos


async def draw_char_cost_img(data: Character, talent_data: CharacterTalents):
    talent_costs = {}
    talent_cost = talent_data['costs']
    for i in talent_cost.values():
        for j in i:  # type:ignore
            if j['name'] not in talent_costs:
                talent_costs[j['name']] = j['count']
            else:
                talent_costs[j['name']] = talent_costs[j['name']] + j['count']

    ascend_costs = {}
    char_cost = data['costs']
    for i in range(1, 7):
        for j in char_cost[f'ascend{i}']:
            if j['name'] not in ascend_costs:
                ascend_costs[j['name']] = j['count']
            else:
                ascend_costs[j['name']] = ascend_costs[j['name']] + j['count']

    bg = Image.open(TEXT_PATH / 'wiki_weapon_bg.jpg')
    img = await get_simple_bg(900, 1800, bg)
    img_draw = ImageDraw.Draw(img)

    desc = await str_lenth(data['description'], 18, 341)

    avatar_id = await name_to_avatar_id(data['name'])
    char_img = Image.open(CHAR_PATH / f'{avatar_id}.png')
    icon = await draw_pic_with_ring(char_img, 222)
    img.paste(icon, (80, 90), icon)

    title = data["title"].replace('「', '').replace('」', '')
    img_draw.text((336, 230), desc, (230, 230, 230), gs_font_24)
    img_draw.text(
        (400, 161),
        f'{title}·{data["name"]}',
        (255, 255, 255),
        gs_font_44,
        'lm',
    )

    star_pic = get_star_png(data['rarity'])
    element_pic_path = TEXT_PATH / f'{data["element"]}.png'
    if element_pic_path.exists():
        element_pic = Image.open(element_pic_path).resize((54, 54))
    else:
        element_pic = get_unknown_png().resize((54, 54))
    img.paste(element_pic, (330, 130), element_pic)
    img.paste(star_pic, (335, 188), star_pic)

    talent_costs = dict(sorted(talent_costs.items(), key=lambda x: len(x[0])))
    ascend_costs = dict(sorted(ascend_costs.items(), key=lambda x: len(x[0])))

    cost1, pos1 = await draw_single_cost('突破素材消耗', ascend_costs)
    cost2, pos2 = await draw_single_cost(
        '天赋素材消耗', {i: talent_costs[i] * 3 for i in talent_costs}
    )
    cost3, pos3 = await draw_single_cost('天赋素材消耗 (一份)', talent_costs)

    pos = max(pos1, pos2, pos3, key=len)
    cost_title = Image.open(TEXT_PATH / 'cost_title.png')
    img.paste(cost_title, (0, 338), cost_title)

    img_draw.text((450, 383), pos, (255, 255, 255), gs_font_30, 'mm')

    img.paste(cost1, (0, 360 + 100), cost1)
    img.paste(cost2, (0, 705 + 100 + 100), cost2)
    img.paste(cost3, (0, 1050 + 100 + 100 + 100), cost3)

    img = img.convert('RGB')
    img.save(
        WIKI_COST_CHAR_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=97,
        subsampling=0,
    )
    return await convert_img(img)
