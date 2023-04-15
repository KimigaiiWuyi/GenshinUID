import math
from typing import List, Union

import aiofiles
from PIL import Image, ImageDraw

from .path import TEXT_PATH
from ..utils.colors import white_color
from ..utils.error_reply import get_error
from ..utils.get_assets import get_assets_from_ambr
from ..utils.image.convert import str_lenth, convert_img
from ..utils.resource.RESOURCE_PATH import WIKI_WEAPON_PATH
from ..gsuid_utils.api.minigg.models import Weapon, WeaponStats
from ..utils.image.image_tools import (
    get_color_bg,
    get_star_png,
    get_unknown_png,
)
from ..gsuid_utils.api.minigg.request import (
    get_others_info,
    get_weapon_info,
    get_weapon_stats,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_22,
    gs_font_28,
    gs_font_36,
    gs_font_44,
)


async def get_artifacts_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_weapon_info(name)
    stats = await get_weapon_stats(name, 90)
    if isinstance(data, int):
        return get_error(data)
    elif isinstance(stats, int):
        return get_error(stats)
    elif isinstance(data, List) or isinstance(stats, List):
        return get_error(-400)
    else:
        art_name = data['name']
        path = WIKI_WEAPON_PATH / f'{art_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_weapons_wiki_img(data, stats)
    return img


async def draw_weapons_wiki_img(data: Weapon, stats: WeaponStats):
    gray_color = (175, 173, 176)
    img_test = Image.new('RGBA', (1, 1))
    img_test_draw = ImageDraw.Draw(img_test)
    effect = data['effect']
    effect = await str_lenth(effect, 22, 540)
    _, _, _, y1 = img_test_draw.textbbox((0, 0), effect, gs_font_22)
    w, h = 600, 1040 + y1

    star_pic = get_star_png(data['rarity'])
    type_pic = Image.open(TEXT_PATH / f'{data["weapontype"]}.png')
    gacha_pic = await get_assets_from_ambr(data['images']['namegacha'])
    if gacha_pic is None:
        gacha_pic = Image.new('RGBA', (333, 666))
    else:
        gacha_pic = gacha_pic.resize((333, 666))

    img = await get_color_bg(w, h, 'wiki_weapon_bg')
    img_draw = ImageDraw.Draw(img)

    img_draw.text((44, 59), data['name'], white_color, gs_font_44, 'lm')
    img.paste(star_pic, (45, 83), star_pic)
    img.paste(type_pic, (44, 158), type_pic)
    img.paste(gacha_pic, (134, 81), gacha_pic)
    img_draw.text((45, 744), '基础攻击力', gray_color, gs_font_18, 'lm')
    img_draw.text((545, 744), data['substat'], gray_color, gs_font_18, 'rm')

    if data['subvalue'] != '':
        sub_val = (
            (data['subvalue'] + '%')
            if data['substat'] != '元素精通'
            else data['subvalue']
        )
    else:
        sub_val = ''

    if data['substat'] != '':
        sp = (
            '%.1f%%' % (stats['specialized'] * 100)
            if data['substat'] != '元素精通'
            else str(math.floor(stats['specialized']))
        )
    else:
        sp = ''

    atk = f'{data["baseatk"]} · {stats["attack"]}'
    subval = f'{sub_val} · {sp}'

    img_draw.text((45, 779), atk, white_color, gs_font_36, 'lm')
    img_draw.text((545, 779), subval, white_color, gs_font_36, 'rm')

    effect_name = f'{data["effectname"]}・精炼5' if data['effectname'] else '无特效'
    img_draw.text((46, 837), effect_name, white_color, gs_font_28, 'lm')
    img_draw.text((46, 866), effect, gray_color, gs_font_28)

    # 计算材料
    temp = {}
    cost = data['costs']
    for i in reversed(cost.values()):
        for j in i:  # type:ignore
            for name in temp.keys():
                similarity = len(set(j['name']) & set(name))
                if similarity >= len(j['name']) / 2:
                    continue
                elif j['name'] == name:
                    temp[name] += j['count']
                else:
                    temp[j['name']] = j['count']

    if data['rarity'] == '5':
        temp['精锻用魔矿'] = 907
    elif data['rarity'] == '4':
        temp['精锻用魔矿'] = 605
    elif data['rarity'] == '3':
        temp['精锻用魔矿'] = 399
    elif data['rarity'] == '2':
        temp['精锻用魔矿'] = 108
    elif data['rarity'] == '1':
        temp['精锻用魔矿'] = 72

    wiki_cost_bg = Image.open(TEXT_PATH / 'wiki_weapon_cost.png')
    wiki_cost_draw = ImageDraw.Draw(wiki_cost_bg)
    for index, cost_name in enumerate(temp):
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
        val = str(temp[cost_name])
        wiki_cost_draw.text((99 + t, 123), val, white_color, gs_font_18, 'mm')

    img.paste(wiki_cost_bg, (0, 850 + y1), wiki_cost_bg)

    return await convert_img(img)
