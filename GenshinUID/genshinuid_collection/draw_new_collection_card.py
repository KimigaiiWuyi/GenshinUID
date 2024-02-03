from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img
from gsuid_core.utils.download_resource.download_image import get_image

from ..utils.colors import get_color
from ..utils.resource.RESOURCE_PATH import ICON_PATH
from ..utils.image.image_tools import shift_image_hue
from .draw_collection_card import TEXT_PATH, get_base_data
from ..utils.fonts.genshin_fonts import (
    gs_font_15,
    gs_font_20,
    gs_font_24,
    gs_font_32,
)

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
}

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


async def draw_explore(uid: str):
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, str) or isinstance(
        raw_data, (bytes, bytearray, memoryview)
    ):
        return raw_data

    r = 20
    half_white = (255, 255, 255, 120)
    white = (255, 255, 255)
    black = (2, 2, 2)

    worlds = raw_data['world_explorations']
    worlds.sort(key=lambda x: (-x['id']), reverse=True)

    image = crop_center_img(
        Image.open(TEXT_PATH / 'bg.jpg'),
        1400,
        450 * ((len(worlds) // 5) + 1) + 50,
    )

    for index, world in enumerate(worlds):
        area_bg = Image.open(TEXT_PATH / 'area_bg.png')

        icon = await get_image(world['icon'], ICON_PATH)
        icon = icon.resize((150, 150)).convert('RGBA')

        percent = world['exploration_percentage']
        name = world['name']
        if '·' in name:
            name = name.split('·')[-1]

        shift = DMAP.get(name, 5)
        area_bg = await shift_image_hue(area_bg, shift)

        main_color = get_color(
            world["level"], CMAP.get(name, [10, 8, 6, 4, 2])
        )

        rank = f'等阶{world["level"]}'

        completion = f'探索完成度: {percent / 10}%'

        area_bg.paste(icon, (75, 36), icon)

        area_draw = ImageDraw.Draw(area_bg)

        # 标题
        area_draw.text((150, 216), name, white, gs_font_32, 'mm')

        # 等阶
        area_draw.rounded_rectangle((98, 240, 201, 270), r, main_color)
        area_draw.text((150, 256), rank, white, gs_font_24, 'mm')

        # 进度条
        lenth = percent * 182 / 1000
        area_draw.rounded_rectangle((59, 283, 241, 295), r, half_white)
        area_draw.rounded_rectangle((59, 283, 59 + lenth, 295), r, white)
        area_draw.text((150, 320), completion, white, gs_font_20, 'mm')

        # 副等阶，如果有的话
        if world['offerings']:
            odata = world['offerings'][0]
            oicon = await get_image(odata['icon'], ICON_PATH)
            oicon = oicon.resize((38, 38)).convert('RGBA')
            orank = f"等阶{odata['level']}"
            oname = odata['name']

            sub_color = get_color(
                odata['level'], CMAP.get(oname, [10, 8, 6, 4, 2])
            )

            area_draw.rounded_rectangle((59, 340, 241, 387), 5, half_white)
            area_bg.paste(oicon, (63, 343), oicon)
            area_draw.text((107, 352), oname, black, gs_font_20, 'lm')
            area_draw.rounded_rectangle((107, 364, 173, 384), r, sub_color)
            area_draw.text((140, 374), orank, white, gs_font_15, 'mm')

        image.paste(
            area_bg,
            (75 + 240 * (index % 5), 30 + 450 * (index // 5)),
            area_bg,
        )
    return await convert_img(image)
