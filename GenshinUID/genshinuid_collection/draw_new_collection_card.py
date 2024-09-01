from typing import Dict, List, Tuple

from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.mys.models import Offering, IndexData
from gsuid_core.utils.download_resource.download_image import get_image

from ..utils.colors import get_color
from .const import max_data, cal_level, expmax_data
from ..utils.resource.RESOURCE_PATH import ICON_PATH
from .draw_collection_card import TEXT_PATH, get_base_data
from ..utils.image.image_tools import get_v4_bg, add_footer, shift_image_hue
from ..utils.fonts.genshin_fonts import (
    gs_font_15,
    gs_font_20,
    gs_font_24,
    gs_font_32,
)

# 五个阶段，每个阶段需要的数量
CMAP = {
    '枫丹': [10, 8, 6, 4, 2],
    '须弥': [10, 8, 6, 4, 2],
    '地下矿区': [10, 8, 6, 4, 2],
    '层岩巨渊': [10, 8, 6, 4, 2],
    '渊下宫': [0, 0, 0, 0, 0],
    '稻妻': [10, 8, 6, 4, 2],
    '龙脊雪山': [12, 10, 8, 5, 2],
    '璃月': [8, 7, 6, 4, 2],
    '蒙德': [8, 7, 6, 4, 2],
    '露景泉': [20, 16, 12, 8, 4],
    '梦之树': [50, 40, 30, 20, 10],
    '流明石触媒': [10, 8, 6, 4, 2],
    '神樱眷顾': [50, 40, 30, 20, 10],
    '忍冬之树': [12, 10, 8, 5, 2],
    '风神瞳': [66, 50, 35, 25, 10],
    '岩神瞳': [131, 100, 70, 40, 10],
    '雷神瞳': [181, 141, 100, 60, 15],
    '草神瞳': [271, 211, 150, 90, 20],
    '水神瞳': [271, 211, 150, 90, 20],
    '冰神瞳': [271, 211, 150, 90, 20],
    '火神瞳': [271, 211, 150, 90, 20],
    '华丽的宝箱': cal_level(max_data['华丽的宝箱']),
    '珍贵的宝箱': cal_level(max_data['珍贵的宝箱']),
    '精致的宝箱': cal_level(max_data['精致的宝箱']),
    '普通的宝箱': cal_level(max_data['普通的宝箱']),
    '奇馈宝箱': cal_level(max_data['奇馈宝箱']),
}

# 颜色HUE旋转
DMAP = {
    '枫丹': 14,
    '须弥': 250,
    '地下矿区': 220,
    '层岩巨渊': 220,
    '渊下宫': 45,
    '稻妻': 30,
    '龙脊雪山': -60,
    '璃月': 200,
    '蒙德': 300,
}

# 神瞳中文名
STCMAP = {
    'electro': '雷神瞳',
    'geo': '岩神瞳',
    'hydro': '水神瞳',
    'anemo': '风神瞳',
    'dendro': '草神瞳',
    'cryo': '冰神瞳',
    'pyro': '火神瞳',
}

STLMAP = {
    'electro': '雷神瞳',
    'geo': '岩神瞳',
    'hydro': '水神瞳',
    'anemo': '风神瞳',
    'dendro': '草神瞳',
    'cryo': '冰神瞳',
    'pyro': '火神瞳',
}

r = 20
half_white = (255, 255, 255, 120)
white = (255, 255, 255)
black = (2, 2, 2)


async def draw_explore(uid: str):
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, str) or isinstance(
        raw_data, (bytes, bytearray, memoryview)
    ):
        return raw_data
    img = await _draw_explore(raw_data)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    bg = add_footer(bg)

    return await convert_img(bg)


async def _draw_explore(raw_data: IndexData):
    worlds = raw_data['world_explorations']
    worlds.sort(key=lambda x: (-x['id']), reverse=True)

    new_culus: Dict[str, str] = {}
    for _culus in raw_data['stats']:
        if _culus.endswith('culus_number'):
            new_culus[_culus] = raw_data['stats'][_culus]

    div_a = Image.open(TEXT_PATH / 'div_a.png')
    div_b = Image.open(TEXT_PATH / 'div_b.png')
    div_c = Image.open(TEXT_PATH / 'div_c.png')

    x = 1680
    # c = int(x / 2)
    title_offer = 50
    line = 390
    div_h = div_a.size[1] - 10
    column = 6
    card_x = 255
    card_act_x = 300
    footer = 80
    offer_x = int((x - column * card_x) / 2 - (card_act_x - card_x) / 2)

    image = Image.new(
        'RGBA',
        (
            x,
            line
            * (
                (((len(worlds) - 1) // column) + 1)
                + (((len(new_culus) - 1) // column) + 1)
                + 1
            )
            + title_offer
            + div_h * 3
            + footer,
        ),
    )

    image.paste(div_a, (0, title_offer), div_a)

    for index_e, _culus in enumerate(new_culus):
        _culus_name = _culus.replace('culus_number', '')
        culus_name = _culus_name.capitalize()
        num: int = raw_data['stats'][_culus]
        culus_zh = STCMAP[_culus_name]

        culus_icon = Image.open(TEXT_PATH / f'Item_{culus_name}culus.webp')
        culus_icon = culus_icon.resize((154, 154))

        if num >= CMAP[culus_zh][0]:
            level_name = '已集齐'
        else:
            level_name = '未集齐'

        area_bg = await draw_area(
            culus_icon,
            (73, 50),
            (num / expmax_data[culus_zh]) * 100,
            f'进度：{num} / {expmax_data[culus_zh]}',
            '收集完成度',
            culus_zh,
            num,
            level_name,
            [],
            15,
        )

        image.paste(
            area_bg,
            (
                offer_x + card_x * (index_e % column),
                div_h + line * (index_e // column) + title_offer,
            ),
            area_bg,
        )

    # 宝箱收集

    common_chest = raw_data['stats']['common_chest_number']
    exq_chest = raw_data['stats']['exquisite_chest_number']
    pre_chest = raw_data['stats']['precious_chest_number']
    lux_chest = raw_data['stats']['luxurious_chest_number']
    magic_chest = raw_data['stats']['magic_chest_number']

    CHEST_ = {
        '普通的宝箱': common_chest,
        '精致的宝箱': exq_chest,
        '珍贵的宝箱': pre_chest,
        '华丽的宝箱': lux_chest,
        '奇馈宝箱': magic_chest,
    }

    image.paste(
        div_b,
        (
            0,
            div_h
            + line * (((len(new_culus) - 1) // column) + 1)
            + title_offer,
        ),
        div_b,
    )

    for index_c, chest_name in enumerate(CHEST_):
        chest_icon = Image.open(TEXT_PATH / f'{chest_name}.png')
        max_num = max_data[chest_name]
        precent = CHEST_[chest_name] / max_num

        if CHEST_[chest_name] >= max_num:
            level_name = '已集齐'
        else:
            level_name = '未集齐'

        area_bg = await draw_area(
            chest_icon,
            (75, 55),
            precent * 100,
            f'进度：{CHEST_[chest_name]} / {max_num}',
            '收集完成度',
            chest_name,
            CHEST_[chest_name],
            level_name,
            [],
            8,
        )

        image.paste(
            area_bg,
            (
                offer_x + card_x * (index_c % column),
                +div_h * 2
                + line * (((len(new_culus) - 1) // column) + 1)
                + line * (index_c // column)
                + title_offer,
            ),
            area_bg,
        )

    image.paste(
        div_c,
        (
            0,
            div_h * 2
            + line * (((len(new_culus) - 1) // column) + 2)
            + title_offer,
        ),
        div_c,
    )

    for index, world in enumerate(worlds):
        icon = await get_image(world['icon'], ICON_PATH)
        icon = icon.resize((150, 150)).convert('RGBA')

        name = world['name']
        if '·' in name:
            name = name.split('·')[-1]
        level = world["level"]
        level_name = f'等阶{level}'
        offerings = world['offerings']

        area_bg = await draw_area(
            icon,
            (75, 36),
            world['exploration_percentage'] / 10,
            '',
            '探索完成度',
            name,
            level,
            level_name,
            offerings,
        )

        image.paste(
            area_bg,
            (
                offer_x + card_x * (index % column),
                +div_h * 3
                + line * (((len(new_culus) - 1) // column) + 2)
                + line * (index // column)
                + title_offer,
            ),
            area_bg,
        )

    return image


async def draw_area(
    icon: Image.Image,
    icon_pos: Tuple[int, int],
    percent: float,
    sub_text: str,
    com_text: str,
    name: str,
    level: int,
    level_name: str,
    offerings: List[Offering],
    offer: int = 0,
) -> Image.Image:
    area_bg = Image.open(TEXT_PATH / 'area_bg.png')
    area_alpha = Image.new('RGBA', area_bg.size, (0, 0, 0, 0))
    alpha_draw = ImageDraw.Draw(area_alpha)

    shift = DMAP.get(name, 5)
    area_bg = await shift_image_hue(area_bg, shift)

    main_color = get_color(level, CMAP.get(name, [10, 8, 6, 4, 2]))

    completion = '{}: {:.1f}%'.format(com_text, percent)

    area_bg.paste(icon, icon_pos, icon)

    area_draw = ImageDraw.Draw(area_bg)

    # 标题
    area_draw.text((150, 216 + offer), name, white, gs_font_32, 'mm')

    # 等阶
    l_r = (98, 240 + offer, 201, 270 + offer)
    alpha_draw.rounded_rectangle(l_r, r, main_color)
    alpha_draw.text((150, 256 + offer), level_name, white, gs_font_24, 'mm')

    # 进度条
    lenth = percent * 1820 / 1000
    p_r_n = (59, 283 + offer, 241, 295 + offer)
    p_r_c = (59, 283 + offer, 59 + lenth, 295 + offer)
    alpha_draw.rounded_rectangle(p_r_n, r, half_white)
    alpha_draw.rounded_rectangle(p_r_c, r, white)
    alpha_draw.text((150, 320 + offer), completion, white, gs_font_20, 'mm')
    if sub_text:
        alpha_draw.text((150, 350 + offer), sub_text, white, gs_font_20, 'mm')

    # 副等阶，如果有的话
    if offerings:
        odata = offerings[0]
        oicon = await get_image(odata['icon'], ICON_PATH)
        oicon = oicon.resize((38, 38)).convert('RGBA')
        orank = f"等阶{odata['level']}"
        oname = odata['name']

        sub_color = get_color(
            odata['level'], CMAP.get(oname, [10, 8, 6, 4, 2])
        )

        o_r_1 = (59, 340 + offer, 241, 387 + offer)
        o_r_2 = (107, 364 + offer, 173, 384 + offer)

        alpha_draw.rounded_rectangle(o_r_1, 5, half_white)

        area_bg.alpha_composite(area_alpha)
        area_bg.paste(oicon, (63, 343 + offer), oicon)
        area_draw.text((107, 352 + offer), oname, black, gs_font_20, 'lm')
        area_draw.rounded_rectangle(o_r_2, r, sub_color)
        area_draw.text((140, 374 + offer), orank, white, gs_font_15, 'mm')
    else:
        area_bg.alpha_composite(area_alpha)

    return area_bg
