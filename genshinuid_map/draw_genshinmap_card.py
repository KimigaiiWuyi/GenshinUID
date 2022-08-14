from io import BytesIO
from pathlib import Path
from typing import Union

import httpx
from PIL import Image, ImageDraw

from .genshinmap import img, utils, models, request
from ..utils.minigg_api.get_minigg_data import get_misc_info
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_simple_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

MAP_DATA = Path(__file__).parent / 'map_data'
TEXT_PATH = Path(__file__).parent / 'texture2d'
resource_card = Image.open(TEXT_PATH / 'resource_card.png')
mark_quest = Image.open(TEXT_PATH / 'mark_quest.png').resize((32, 32))
Image.MAX_IMAGE_PIXELS = 333120000

gs_font_68 = genshin_font_origin(68)
gs_font_30 = genshin_font_origin(30)


async def make_bound(x: float, y: float, width: int):
    return (x - width, y - width, x + width, y + width)


async def draw_genshin_map(
    map_id: models.MapID, resource_name: str
) -> Union[bytes, str]:
    resource_img = Image.new('RGBA', (1000, 1400), 'white')
    maps = await request.get_maps(map_id)
    labels = await request.get_labels(map_id)
    resource_id = 0
    resource_icon = ''
    desc_list = []
    adv_list = ['推荐采集地点:']
    for label in labels:
        for child in label.children:
            if resource_name == child.name:
                resource_id = child.id
                resource_icon = child.icon
                resource_name = child.name
                resource_data = await get_misc_info('materials', resource_name)
                if 'description' in resource_data:
                    desc_data = resource_data['description'].replace('，', '\n')
                    desc_list.extend(desc_data.split('\n'))
                else:
                    desc_list.append('暂无描述...')
                if 'source' in resource_data:
                    adv_list.extend(resource_data['source'])
                break

    if resource_id == 0:
        return '资源点不存在!'

    points = await request.get_points(map_id)
    transmittable = utils.get_points_by_id(resource_id, points)
    # 转换坐标
    transmittable_converted = utils.convert_pos(
        transmittable, maps.detail.origin
    )
    if len(transmittable_converted) >= 3:
        group_point = img.k_means_points(transmittable_converted)
    elif len(transmittable_converted) == 0:
        return f'该资源点{resource_name}不存在!\n请尝试[切换地图]或者查找其他资源点!'
    else:
        x1_temp = int(transmittable_converted[0].x) - 470
        x2_temp = int(transmittable_converted[0].x) + 470
        y1_temp = int(transmittable_converted[0].y) - 500
        y2_temp = int(transmittable_converted[0].y) + 500
        group_point = [
            [
                models.XYPoint(x1_temp, y1_temp),
                models.XYPoint(x2_temp, y2_temp),
                transmittable_converted,
            ]
        ]
    genshin_map = Image.open(MAP_DATA / f'{map_id.name}.png')
    lt_point = group_point[0][0]
    rb_point = group_point[0][1]
    genshin_map = genshin_map.crop(
        (int(lt_point.x), int(lt_point.y), int(rb_point.x), int(rb_point.y))
    )
    for point in group_point[0][2]:
        point_trans = (
            int(point.x) - int(lt_point.x),
            int(point.y) - int(lt_point.y),
        )
        genshin_map.paste(
            mark_quest, (point_trans[0] - 16, point_trans[1] - 16), mark_quest
        )
    genshin_map = await get_simple_bg(950, 1010, genshin_map)
    resource_img.paste(genshin_map, (25, 25))
    resource_img.paste(resource_card, (0, 0), resource_card)
    resource_pic = (
        Image.open(BytesIO(httpx.get(resource_icon).content))
        .convert('RGBA')
        .resize((150, 150))
    )
    resource_img.paste(resource_pic, (81, 1096), resource_pic)
    resource_draw = ImageDraw.Draw(resource_img)
    resource_draw.text(
        (248, 1128), resource_name, (75, 48, 0), font=gs_font_68, anchor='lm'
    )
    for desc_index, desc in enumerate(desc_list):
        resource_draw.text(
            (248, 1198 + desc_index * 34),
            desc,
            (154, 138, 110),
            font=gs_font_30,
            anchor='lm',
        )
    if len(adv_list) == 1:
        adv_list.append('暂无')
    resource_draw.text(
        (73, 1332),
        ' '.join(adv_list),
        (154, 138, 110),
        font=gs_font_30,
        anchor='lm',
    )
    resource_img.convert('RGB').save(
        MAP_DATA / f'{map_id.name}_{resource_name}.jpg', 'JPEG', quality=85
    )
    resource_img = await convert_img(resource_img)
    return resource_img
