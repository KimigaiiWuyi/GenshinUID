from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw

from ..utils.image.convert import convert_img
from ..utils.map.GS_MAP_PATH import artifact2attr
from ..utils.image.image_tools import get_color_bg, draw_pic_with_ring
from ..utils.resource.generate_char_card import create_single_item_card
from .get_all_char_data import get_abyssinfo_data, get_akasha_char_data
from ..utils.map.name_covert import name_to_avatar_id, alias_to_char_name
from ..utils.resource.RESOURCE_PATH import REL_PATH, CHAR_PATH, WEAPON_PATH
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_30,
    gs_font_40,
    gs_font_44,
)

black = (10, 10, 10)
grey = (40, 40, 40)

green = (205, 255, 168)
red = (255, 168, 168)

TEXT_PATH = Path(__file__).parent / 'texture2d'

rank_dict = {
    90: (189, 64, 64),
    80: (189, 64, 148),
    60: (95, 64, 189),
    40: (64, 140, 189),
    20: (64, 189, 125),
    0: (134, 107, 71),
}


async def draw_char_abyss_info(char_name: str) -> Union[bytes, str]:
    char_name = await alias_to_char_name(char_name)
    char_id = await name_to_avatar_id(char_name)
    abyss_info = await get_abyssinfo_data()

    # _char_id = char_id[1:].lstrip('0')
    char_useage_rank = []
    char_img = Image.open(CHAR_PATH / f'{char_id}.png')
    char_pic = await draw_pic_with_ring(char_img, 264)

    _data = await get_akasha_char_data(char_name)
    if _data is None:
        return '没有该角色的数据...'

    all_char_info, char_useage_rank = _data[0], _data[1]

    char_useage_rank.sort(key=lambda d: int(d['v']))

    title_bg = Image.open(TEXT_PATH / 'title_bg.png')

    # 计算宽高
    h = 1230 + len(char_useage_rank) * 30

    # 开始绘图
    img = await get_color_bg(900, h, '_abyss_char')
    _img = Image.new('RGBA', img.size)
    img.paste(char_pic, (300, 118), char_pic)
    img.paste(title_bg, (0, 400), title_bg)

    # 基础文字部分
    img_draw = ImageDraw.Draw(_img)
    img_draw.text((450, 450), f'{char_name}的深渊统计', 'White', gs_font_40, 'mm')

    # 绘图
    r = 20
    bg_color = (255, 255, 255, 120)
    h0 = 653
    h1 = 208
    # h2 = h - 1028

    img_draw.rounded_rectangle((24, 518, 876, h0), r, bg_color)

    xy1 = (24, h0 + 20, 876, h0 + 20 + h1)
    xy2 = (24, h0 + 20 + h1 + 20, 876, h0 + 20 + h1 * 2 + 20)
    xy3 = (24, h0 + 20 + h1 * 2 + 40, 876, h - 40)

    img_draw.rounded_rectangle(xy1, r, bg_color)
    img_draw.rounded_rectangle(xy2, r, bg_color)
    img_draw.rounded_rectangle(xy3, r, bg_color)

    char_data_list = []
    char_data_list.append(
        '{:.1f}%'.format(float(all_char_info['abyss']['use_rate']) * 100)
    )
    char_data_list.append(
        '{:.1f}%'.format(float(all_char_info['abyss']['maxstar_rate']) * 100)
    )
    char_data_list.append(
        '{:.1f}%'.format(all_char_info['abyss']['come_rate'])
    )
    char_data_list.append(str(all_char_info['abyss']['avg_level']))
    char_data_list.append(str(all_char_info['abyss']['avg_constellation']))

    for index, i in enumerate(['使用率', '满星率', '出场率', '平均等级', '平均命座']):
        _it = index * 161
        img_draw.text((127 + _it, 618), i, (67, 46, 26), gs_font_30, 'mm')
        img_draw.text(
            (127 + _it, 566), char_data_list[index], 'Black', gs_font_44, 'mm'
        )

    _start = 1135
    bar_bg = (0, 0, 0, 128)

    for index, rank in enumerate(char_useage_rank):
        _intent = _start + index * 30 + 20
        y1, y2 = _intent + 9, _intent + 23
        img_draw.rounded_rectangle((108, y1, 708, y2), r, bar_bg)

        d = float(rank["d"])
        _pixel = int((d / 100) * 600)
        for _p in rank_dict:
            if d >= _p:
                fill = rank_dict[_p]
                break
        else:
            fill = (255, 255, 255)
        img_draw.rounded_rectangle((108, y1, 108 + _pixel, y2), r, fill)

        value = f'{rank["d"]}% / {rank["r"]}名'
        if rank['v'] in abyss_info:
            version = abyss_info[rank['v']]['version']
        else:
            version = f'版本{rank["v"]}'

        if version == '版本0':
            version = '平均'

        version = version.replace('-', ' - ')

        img_draw.text((95, 16 + _intent), version, 'Black', gs_font_20, 'rm')
        img_draw.text((726, 16 + _intent), value, 'Black', gs_font_20, 'lm')

    img.paste(_img, (0, 0), _img)

    # 开始
    for index, weapon in enumerate(all_char_info['weapons']):
        if weapon['name'] == '渔获':
            weapon_name = '「渔获」'
        else:
            weapon_name = weapon['name']
        weapon_img = Image.open(WEAPON_PATH / f'{weapon_name}.png')
        item = await create_single_item_card(weapon_img, weapon['rarity'])
        item_draw = ImageDraw.Draw(item)
        weapon_rate = weapon['rate'] + '%'
        item_draw.text((128, 280), weapon_rate, 'Black', gs_font_40, 'mm')
        item = item.resize((128, 155))
        img.paste(item, (47 + 135 * index, xy1[1] + 25), item)
        if index >= 5:
            break

    for index, equip in enumerate(all_char_info['equips']):
        item_list = []
        item_type = 0
        for set in equip['set_list']:
            for part in artifact2attr:
                if artifact2attr[part] == set['name']:
                    part_name = part
                    break
            else:
                part_name = '冰风迷途的勇士'
            item = Image.open(REL_PATH / f'{part_name}.png')
            item_list.append(item)
            item_type += int(set['count'])

        item = await create_single_item_card(item_list, '5')

        item_draw = ImageDraw.Draw(item)
        equip_rate = equip['rate'] + '%'
        item_draw.text((128, 280), equip_rate, 'Black', gs_font_40, 'mm')

        item_draw.rounded_rectangle((200, 20, 240, 60), 15, (255, 255, 255))
        item_draw.text((220, 40), f'{item_type}', 'Black', gs_font_40, 'mm')

        item = item.resize((128, 155))
        img.paste(item, (47 + 135 * index, xy2[1] + 25), item)
        if index >= 5:
            break
    return await convert_img(img)
