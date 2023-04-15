from typing import Dict, Tuple, Union

from PIL import Image, ImageDraw

from .path import TEXT_PATH
from ..utils.colors import first_color
from ..utils.error_reply import get_error
from ..utils.resource.download_url import download
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.map.GS_MAP_PATH import avatarName2Element
from ..utils.image.convert import str_lenth, convert_img
from ..utils.fonts.genshin_fonts import gs_font_20, gs_font_28
from ..gsuid_utils.api.minigg.request import get_constellation_info
from ..utils.image.image_tools import get_color_bg, draw_pic_with_ring
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    ICON_PATH,
    CONSTELLATION_PATH,
)
from ..gsuid_utils.api.minigg.models import (
    CharacterConstellation,
    CharacterConstellations,
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
    if isinstance(data, int):
        return get_error(data)
    else:
        pass
        '''
        full_name = data['name']
        path = CONSTELLATION_PATH / f'{full_name}.jpg'
        if path.exists():
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
        '''
    img = await draw_constellation_wiki_img(data)
    return img


async def draw_single_constellation(
    data: CharacterConstellation,
    image: str,
    num: int,
    color: Tuple[int, int, int],
) -> Image.Image:
    # 计算长度
    effect = data['effect']
    for i in range(1, 10):
        if i % 2 != 0:
            effect = effect.replace('**', '「', 1)
        else:
            effect = effect.replace('**', '」', 1)

    effect = '　　' + effect.replace('\n', '\n　　')
    effect = await str_lenth(effect, 20, 465)
    effect += '\n'
    img1 = Image.new('RGBA', (600, 1400))
    img1_draw = ImageDraw.Draw(img1)
    _, _, _, y1 = img1_draw.textbbox((0, 0), effect, gs_font_20)

    y = 110 + y1
    img = Image.new('RGBA', (600, y))
    img_draw = ImageDraw.Draw(img)

    img_draw.rounded_rectangle(
        (45, 18, 555, y),
        fill=(255, 255, 255, 125),
        radius=20,
    )

    icon_name = image.split('/')[-1]
    path = ICON_PATH / icon_name
    if not path.exists():
        await download(image, 8, icon_name)
    icon = Image.open(path).resize((51, 51))
    img.paste(icon, (60, 28), icon)
    img_draw.text(
        (128, 52),
        f'{num}命 | {data["name"]}',
        color,
        gs_font_28,
        'lm',
    )
    # line = '·' * 25 + '\n'
    # img_draw.text((300, 95), line, (243, 180, 133), gs_font_20, 'mm')
    img_draw.text((60, 95), effect, first_color, gs_font_20)
    # img_draw.text((300, 120 + y1), line, (243, 180, 133), gs_font_20, 'mm')
    return img


async def draw_constellation_wiki_img(data: CharacterConstellations) -> bytes:
    img_list: Dict[int, Tuple[Image.Image, int]] = {}
    element = avatarName2Element[data['name']]
    bg_color = COLOR_MAP[element]

    y = 0
    for i in range(1, 7):
        _img = await draw_single_constellation(
            data[f'c{i}'], data['images'][f'c{i}'], i, bg_color
        )
        img_list[i] = (_img, _img.size[1])
        y += _img.size[1]
    title = Image.open(TEXT_PATH / 'con_title.png')
    avatar_id = await name_to_avatar_id(data['name'])
    char_img = Image.open(CHAR_PATH / f'{avatar_id}.png')
    icon = await draw_pic_with_ring(char_img, 210)
    title.paste(icon, (192, 44), icon)
    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (300, 296), f'{data["name"]}命座', bg_color, gs_font_28, 'mm'
    )
    '''
    overlay = Image.open(TEXT_PATH / 'wiki_grad_black.png').resize(
        (600, y + 400)
    )
    color_img = Image.new('RGBA', overlay.size, bg_color)
    img = ImageChops.difference(color_img, overlay)
    '''
    img = await get_color_bg(600, y + 400)

    '''
    gacha_img = Image.open(GACHA_IMG_PATH / f'{data["name"]}.png')
    gacha_img.putalpha(
        gacha_img.getchannel('A').point(
            lambda x: round(x * 0.2) if x > 0 else 0
        )
    )
    img.paste(gacha_img, (-724, 275), gacha_img)
    '''

    temp = 365
    for index in img_list:
        _img = img_list[index][0]
        img.paste(_img, (0, temp), _img)
        temp += img_list[index][1]

    img.paste(title, (0, 0), title)

    img = img.convert('RGB')
    img.save(
        CONSTELLATION_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=100,
        subsampling=0,
    )
    return await convert_img(img)
