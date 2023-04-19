import math
from typing import Dict, List, Union

import aiofiles
from PIL import Image, ImageDraw

from .path import TEXT_PATH
from ..utils.colors import white_color
from ..utils.error_reply import get_error
from ..utils.get_assets import get_assets_from_ambr
from ..utils.image.convert import convert_img, get_str_size
from ..utils.resource.RESOURCE_PATH import WIKI_WEAPON_PATH
from ..gsuid_utils.api.minigg.models import Weapon, WeaponStats
from ..utils.image.image_tools import (
    get_star_png,
    get_simple_bg,
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


async def get_weapons_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_weapon_info(name)
    if isinstance(data, int):
        return get_error(data)
    elif isinstance(data, List):
        return get_error(-400)
    else:
        if int(data['rarity']) < 3:
            stats = await get_weapon_stats(name, 70)
        else:
            stats = await get_weapon_stats(name, 90)

    if isinstance(stats, int):
        return get_error(stats)
    elif isinstance(stats, List):
        return get_error(-400)
    else:
        weapon_name = data['name']
        path = WIKI_WEAPON_PATH / f'{weapon_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_weapons_wiki_img(data, stats)
    return img


async def draw_weapons_wiki_img(data: Weapon, stats: WeaponStats):
    spec_rank = ['孢囊晶尘', '荧光孢粉', '蕈兽孢子']
    gray_color = (214, 214, 214)
    img_test = Image.new('RGBA', (1, 1))
    img_test_draw = ImageDraw.Draw(img_test)
    effect = data['effect']
    effect = effect.replace('/', '·')
    rw_ef = []
    for i in range(len(data['r1'])):
        now = ''
        for j in range(1, 6):
            ef_val = data[f'r{j}'][i].replace('/', '·')
            now += ef_val + ' / '
        now = f'{now[:-2]}'
        rw_ef.append(now)

    if effect:
        effect = effect.format(*rw_ef)
    else:
        effect = '无特效'

    effect = get_str_size(effect, gs_font_22, 490)

    _, _, _, y1 = img_test_draw.textbbox((0, 0), effect, gs_font_22)
    w, h = 600, 1110 + y1

    star_pic = get_star_png(data['rarity'])
    type_pic = Image.open(TEXT_PATH / f'{data["weapontype"]}.png')
    gacha_pic = await get_assets_from_ambr(data['images']['namegacha'])
    if gacha_pic is None:
        gacha_pic = Image.new('RGBA', (333, 666))
    else:
        gacha_pic = gacha_pic.resize((333, 666))

    bg = Image.open(TEXT_PATH / 'wiki_weapon_bg.jpg')
    img = await get_simple_bg(w, h, bg)
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
            else str(math.ceil(stats['specialized']))
        )
    else:
        sp = ''

    atk = f'{data["baseatk"]}/{math.ceil(stats["attack"])}'
    subval = f'{sub_val}/{sp}'

    img_draw.text((45, 779), atk, white_color, gs_font_36, 'lm')
    img_draw.text((545, 779), subval, white_color, gs_font_36, 'rm')

    effect_name = f'{data["effectname"]}' if data['effectname'] else '无特效'
    img_draw.text((46, 837), effect_name, (255, 206, 51), gs_font_28, 'lm')
    img_draw.text((46, 866), effect, gray_color, gs_font_22)

    # 计算材料
    temp: Dict[str, List[int]] = {}
    name_temp: Dict[str, List[str]] = {}
    cost_data = data['costs']
    for i in reversed(cost_data.values()):
        for j in i:  # type:ignore
            for k in list(temp.keys()):
                sim = len(set(j['name']) & set(k))
                # 如果材料名称完全相同
                if k == j['name']:
                    if k not in name_temp:
                        name_temp[k] = [k]
                        temp[k] = [j['count']]
                    else:
                        temp[k][0] += j['count']
                    break
                # 如果两种材料的相似性超过50%
                elif sim >= len(j['name']) / 2:
                    if j['name'] not in name_temp[k]:
                        name_temp[k].append(j['name'])
                        temp[k].append(j['count'])
                    else:
                        _i = name_temp[k].index(j['name'])
                        temp[k][_i] += j['count']
                    break
                elif j['name'] in spec_rank:
                    if spec_rank[0] in temp:
                        if j['name'] not in name_temp[spec_rank[0]]:
                            name_temp[spec_rank[0]].append(j['name'])
                            temp[spec_rank[0]].append(j['count'])
                        else:
                            _i = name_temp[spec_rank[0]].index(j['name'])
                            temp[spec_rank[0]][_i] += j['count']
                        break
            else:
                name_temp[j['name']] = [j['name']]
                temp[j['name']] = [j['count']]

    if data['rarity'] == '5':
        temp['精锻用魔矿'] = [907]
    elif data['rarity'] == '4':
        temp['精锻用魔矿'] = [605]
    elif data['rarity'] == '3':
        temp['精锻用魔矿'] = [399]
    elif data['rarity'] == '2':
        temp['精锻用魔矿'] = [108]
    elif data['rarity'] == '1':
        temp['精锻用魔矿'] = [72]

    wiki_cost_bg = Image.open(TEXT_PATH / 'wiki_weapon_cost.png')
    wiki_cost_tag = Image.open(TEXT_PATH / 'cost_tag.png')
    img.paste(wiki_cost_tag, (37, 890 + y1), wiki_cost_tag)
    wiki_cost_draw = ImageDraw.Draw(wiki_cost_bg)

    cost_pos = ''
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

            if not cost_pos and material['materialtype'] == '武器突破素材':
                pos = material['dropdomain']
                days = material['daysofweek']
                cost_pos = f'{pos} - {"/".join(days)}'

        t = 100 * index
        wiki_cost_bg.paste(cost_pic, (67 + t, 46), cost_pic)
        val_list = [str(x) for x in temp[cost_name]]
        val = '/'.join(val_list)
        wiki_cost_draw.text((99 + t, 123), val, white_color, gs_font_18, 'mm')

    img_draw.text((88, 918 + y1), cost_pos, white_color, gs_font_22, 'lm')
    img.paste(wiki_cost_bg, (0, 920 + y1), wiki_cost_bg)

    img = img.convert('RGB')
    img.save(
        WIKI_WEAPON_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=95,
        subsampling=0,
    )
    return await convert_img(img)
