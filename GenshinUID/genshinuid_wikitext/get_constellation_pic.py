from typing import Dict, List, Tuple, Union

import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.api.minigg.request import (
    get_character_info,
    get_constellation_info,
)
from gsuid_core.utils.api.minigg.models import (
    Character,
    CharacterConstellation,
    CharacterConstellations,
)

from .path import TEXT_PATH
from ..utils.resource.download_url import download
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.image.convert import str_lenth, convert_img
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    ICON_PATH,
    CONSTELLATION_PATH,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_20,
    gs_font_28,
    gs_font_32,
)
from ..utils.image.image_tools import (
    get_star_png,
    get_simple_bg,
    get_unknown_png,
    draw_pic_with_ring,
)

COLOR_MAP = {
    'Anemo': (0, 145, 137),
    'Cryo': (4, 126, 152),
    'Dendro': (28, 145, 0),
    'Electro': (133, 12, 159),
    'Geo': (147, 112, 3),
    'Hydro': (51, 73, 162),
    'Pyro': (136, 28, 33),
}


async def get_constellation_wiki_img(name: str) -> Union[str, bytes]:
    data = await get_constellation_info(name)
    char_data = await get_character_info(name)
    if isinstance(data, int):
        return get_error(data)
    elif isinstance(char_data, int):
        return get_error(char_data)
    elif isinstance(char_data, List):
        return get_error(-400)
    else:
        full_name = data['name']
        path = CONSTELLATION_PATH / f'{full_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    img = await draw_constellation_wiki_img(data, char_data)
    return img


async def get_single_constellation_img(
    name: str, num: int
) -> Union[str, bytes]:
    data = await get_constellation_info(name)
    if isinstance(data, int):
        return get_error(data)
    else:
        full_name = data['name']
        path = CONSTELLATION_PATH / f'{full_name}_{num}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
    con = data[f'c{num}']
    url = data['images'][f'c{num}']
    img = await draw_single_constellation(con, url, num, data['name'], True)
    return await convert_img(img)


async def draw_single_constellation(
    data: CharacterConstellation,
    image: str,
    num: int,
    char_name: str,
    is_single: bool = False,
) -> Image.Image:
    # 计算长度
    effect = data['effect']
    for i in range(1, 10):
        if i % 2 != 0:
            effect = effect.replace('**', '「', 1)
        else:
            effect = effect.replace('**', '」', 1)

    effect = await str_lenth(effect, 20, 420)

    img1 = Image.new('RGBA', (1, 1))
    img1_draw = ImageDraw.Draw(img1)
    _, _, _, y1 = img1_draw.textbbox((0, 0), effect, gs_font_20)

    y = 90 + y1
    if is_single:
        bg = Image.open(TEXT_PATH / 'wiki_weapon_bg.jpg')
        img = await get_simple_bg(600, y, bg)
    else:
        img = Image.new('RGBA', (600, y))

    img_draw = ImageDraw.Draw(img)

    if is_single:
        img_test = Image.new('RGBA', (600, y))
        img_test_draw = ImageDraw.Draw(img_test)
        img_test_draw.rounded_rectangle(
            (28, 7, 572, 80 + y1),
            fill=(255, 255, 255, 60),
            radius=20,
        )
        img.paste(img_test, (0, 0), img_test)

    icon_bg = Image.open(TEXT_PATH / 'ring_bg.png').resize((74, 74))
    img.paste(icon_bg, (38, 20), icon_bg)

    icon_name = image.split('/')[-1]
    path = ICON_PATH / icon_name
    if not path.exists():
        await download(image, 8, icon_name)
    icon = Image.open(path).resize((38, 38))
    img.paste(icon, (57, 37), icon)
    img_draw.text(
        (134, 40),
        f'{data["name"]}',
        (255, 206, 51),
        gs_font_28,
        'lm',
    )
    img_draw.text((130, 60), effect, (230, 230, 230), gs_font_20)
    if is_single:
        img = img.convert('RGB')
        img.save(
            CONSTELLATION_PATH / f'{char_name}_{num}.jpg',
            format='JPEG',
            quality=95,
            subsampling=0,
        )
    return img


async def draw_constellation_wiki_img(
    data: CharacterConstellations, char_data: Character
) -> bytes:
    img_list: Dict[int, Tuple[Image.Image, int]] = {}
    # element = avatarName2Element[data['name']]
    # bg_color = COLOR_MAP[element]

    y = 0
    for i in range(1, 7):
        _img = await draw_single_constellation(
            data[f'c{i}'], data['images'][f'c{i}'], i, char_data['name']
        )
        img_list[i] = (_img, _img.size[1])
        y += _img.size[1]

    bg = Image.open(TEXT_PATH / 'wiki_weapon_bg.jpg')
    img = await get_simple_bg(600, 280 + y, bg)
    img_draw = ImageDraw.Draw(img)

    desc = await str_lenth(char_data['description'], 18, 350)

    avatar_id = await name_to_avatar_id(data['name'])
    char_img = Image.open(CHAR_PATH / f'{avatar_id}.png')
    icon = await draw_pic_with_ring(char_img, 148)
    img.paste(icon, (40, 77), icon)

    img_draw.text((205, 161), desc, (230, 230, 230), gs_font_18)
    img_draw.text(
        (232, 102),
        f'{char_data["title"]}·{char_data["name"]}',
        (255, 255, 255),
        gs_font_32,
        'lm',
    )

    star_pic = get_star_png(char_data['rarity'])
    element_pic_path = TEXT_PATH / f'{char_data["element"]}.png'
    if element_pic_path.exists():
        element_pic = Image.open(element_pic_path).resize((36, 36))
    else:
        element_pic = get_unknown_png().resize((36, 36))
    img.paste(element_pic, (188, 81), element_pic)
    img.paste(star_pic, (201, 120), star_pic)

    temp = 253
    for index in img_list:
        _img = img_list[index][0]
        img.paste(_img, (0, temp), _img)
        temp += img_list[index][1]

    img = img.convert('RGB')
    img.save(
        CONSTELLATION_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=96,
        subsampling=0,
    )
    return await convert_img(img)
