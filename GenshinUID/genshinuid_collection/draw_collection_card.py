from pathlib import Path
from typing import Dict, Tuple, Union, Literal

from PIL import Image, ImageDraw

from ..utils.convert import GsCookie
from ..utils.image.convert import convert_img
from ..utils.map.GS_MAP_PATH import avatarId2Name
from ..gsuid_utils.api.mys.models import IndexData
from ..utils.fonts.genshin_fonts import gs_font_30, gs_font_40
from ..utils.image.image_tools import (
    draw_bar,
    get_color_bg,
    get_qq_avatar,
    draw_pic_with_ring,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'

first_color = (29, 29, 29)
brown_color = (41, 25, 0)
red_color = (255, 66, 66)
green_color = (74, 189, 119)

max_data = {
    '成就': 945,
    '华丽的宝箱': 192,
    '珍贵的宝箱': 510,
    '精致的宝箱': 1639,
    '普通的宝箱': 2690,
    '奇馈宝箱': 161,
    '解锁传送点': 304,
    '解锁秘境': 51,
}

award_data = {
    '成就': 5,
    '华丽的宝箱': 10,
    '珍贵的宝箱': 8,
    '精致的宝箱': 3,
    '普通的宝箱': 1,
    '奇馈宝箱': 2,
    '解锁传送点': 0,
    '解锁秘境': 0,
}

expmax_data = {
    '获得角色数': len(avatarId2Name) - 2,
    '风神瞳': 66,
    '岩神瞳': 131,
    '雷神瞳': 181,
    '草神瞳': 271,
}


async def draw_collection_img(
    qid: Union[str, int], uid: str
) -> Union[str, bytes]:
    return await draw_base_img(qid, uid, '收集')


async def draw_explora_img(
    qid: Union[str, int], uid: str
) -> Union[str, bytes]:
    return await draw_base_img(qid, uid, '探索')


async def get_base_data(uid: str) -> Union[str, IndexData]:
    # 获取Cookies
    data_def = GsCookie()
    retcode = await data_def.get_cookie(uid)
    if retcode:
        return retcode
    raw_data = data_def.raw_data
    if raw_data is None:
        return '数据异常！'
    return raw_data


async def get_explore_data(
    uid: str,
) -> Union[str, Tuple[Dict[str, float], Dict[str, str], str, str, str]]:
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, str):
        return raw_data

    # 处理数据
    data: Dict[str, int] = {
        '获得角色数': raw_data['stats']['avatar_number'],
        '风神瞳': raw_data['stats']['anemoculus_number'],
        '岩神瞳': raw_data['stats']['geoculus_number'],
        '雷神瞳': raw_data['stats']['electroculus_number'],
        '草神瞳': raw_data['stats']['dendroculus_number'],
    }
    for i in raw_data['world_explorations']:
        data[i['name']] = i['exploration_percentage']

    percent_data = {}
    value_data = {}
    day: str = str(raw_data['stats']['active_day_number'])
    me_percent = 0
    world_percent = 0

    for name in data:
        # 百分比
        p_str = f'{data[name]}'
        if name in expmax_data:
            percent = data[name] / expmax_data[name]
            if name != '获得角色数':
                me_percent += percent
            value = f'{p_str} / {expmax_data[name]} | {_f(percent * 100)}'
        else:
            percent = data[name] / 1000
            world_percent += percent
            value = f'{_f(percent * 100)}'

        percent_data[name] = percent
        value_data[name] = value

    me_percent = _f(me_percent * 100 / (len(expmax_data) - 1))
    world_percent = _f(world_percent * 100 / (len(data) - len(expmax_data)))

    return percent_data, value_data, day, me_percent, world_percent


async def get_collection_data(
    uid: str,
) -> Union[str, Tuple[Dict[str, float], Dict[str, str], str, str, str]]:
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, str):
        return raw_data
    raw_data = raw_data['stats']

    # 处理数据
    data: Dict[str, int] = {
        '成就': raw_data['achievement_number'],
        '普通的宝箱': raw_data['common_chest_number'],
        '精致的宝箱': raw_data['exquisite_chest_number'],
        '珍贵的宝箱': raw_data['precious_chest_number'],
        '华丽的宝箱': raw_data['luxurious_chest_number'],
        '奇馈宝箱': raw_data['magic_chest_number'],
        '解锁传送点': raw_data['way_point_number'],
        '解锁秘境': raw_data['domain_number'],
    }
    percent_data = {}
    value_data = {}
    left = 0
    day: str = str(raw_data['active_day_number'])
    all_percent = 0

    for name in data:
        # 百分比
        percent = data[name] / max_data[name]
        all_percent += percent
        p_str = f'{data[name]} / {max_data[name]}'
        value = f'{p_str} | {_f(percent * 100)}'
        # 可获石头
        left += award_data[name] * (max_data[name] - data[name])
        percent_data[name] = percent
        value_data[name] = value

    all_percent = _f(all_percent * 100 / len(data))

    return percent_data, value_data, day, all_percent, f'约{left}'


async def draw_base_img(
    qid: Union[str, int], uid: str, mode: Literal['探索', '收集'] = '收集'
) -> Union[str, bytes]:
    # 获取数据
    if mode == '收集':
        data = await get_collection_data(uid)
    else:
        data = await get_explore_data(uid)
    if isinstance(data, str):
        return data
    percent_data, value_data = data[0], data[1]

    # 获取背景图片各项参数
    _id = str(qid)
    if _id.startswith('http'):
        char_pic = await get_qq_avatar(avatar_url=_id)
    else:
        char_pic = await get_qq_avatar(qid=qid)
    char_pic = await draw_pic_with_ring(char_pic, 264)

    if mode == '收集':
        title = Image.open(TEXT_PATH / 'collection_title.png')
    else:
        title = Image.open(TEXT_PATH / 'explora_title.png')

    img = await get_color_bg(750, 600 + len(percent_data) * 115)
    img.paste(title, (0, 0), title)
    img.paste(char_pic, (241, 40), char_pic)

    for index, name in enumerate(percent_data):
        percent = percent_data[name]
        value = value_data[name]
        bar = await draw_bar(f'·{name}', percent, value)
        img.paste(bar, (0, 600 + index * 115), bar)

    # 头
    img_draw = ImageDraw.Draw(img)
    img_draw.text((378, 357), f'UID {uid}', first_color, gs_font_30, 'mm')
    img_draw.text((137, 498), data[2], first_color, gs_font_40, 'mm')
    img_draw.text((372, 498), data[3], first_color, gs_font_40, 'mm')
    img_draw.text((607, 498), data[4], first_color, gs_font_40, 'mm')

    res = await convert_img(img)
    return res


def _f(value: float) -> str:
    return '{:.2f}%'.format(value)
