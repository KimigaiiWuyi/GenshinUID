import asyncio
from pathlib import Path
from typing import List, Union, Optional

from PIL import Image, ImageDraw
from gsuid_core.utils.api.enka.models import EnkaData

from .to_data import enka_to_dict
from ..utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import CHAR_PATH
from ..utils.fonts.genshin_fonts import gs_font_18, gs_font_58
from ..utils.map.name_covert import name_to_avatar_id, avatar_id_to_char_star

half_color = (255, 255, 255, 120)
first_color = (29, 29, 29)
second_color = (67, 61, 56)
white_color = (247, 247, 247)

MAP_PATH = Path(__file__).parent / 'map'
TEXT_PATH = Path(__file__).parent / 'texture2D'
char_mask = Image.open(TEXT_PATH / 'char_mask.png')
tag = Image.open(TEXT_PATH / 'tag.png')
footbar = Image.open(TEXT_PATH / 'footbar.png')
pic_500 = Image.open(TEXT_PATH / '500.png')
pic_204 = Image.open(TEXT_PATH / '204.png')


async def enka_to_card(
    uid: str, enka_data: Optional[EnkaData] = None
) -> Union[str, bytes]:
    char_data_list = await enka_to_dict(uid, enka_data)
    if isinstance(char_data_list, str):
        if '服务器正在维护或者关闭中' in char_data_list:
            return await convert_img(pic_500)
        elif '未打开角色展柜' in char_data_list:
            return await convert_img(pic_204)
        else:
            return await convert_img(pic_500)
    else:
        if char_data_list == []:
            return await convert_img(pic_500)

    img = await draw_enka_card(uid=uid, char_data_list=char_data_list)
    return img


async def draw_enka_card(
    uid: str,
    char_data_list: Optional[List] = None,
    char_list: Optional[List] = None,
):
    if char_list:
        char_data_list = []
        for char in char_list:
            char_data_list.append(
                {'avatarName': char, 'avatarId': await name_to_avatar_id(char)}
            )
        line1 = f'展柜内有 {len(char_data_list)} 个角色!'
    else:
        if char_data_list is None:
            return await convert_img(
                Image.new('RGBA', (0, 1), (255, 255, 255))
            )
        else:
            line1 = '刷新成功!'

    line2 = f'UID {uid}请使用 查询{char_data_list[0]["avatarName"]} 命令进行查询!'
    char_num = len(char_data_list)
    if char_num <= 8:
        based_w, based_h = 1000, 240 + ((char_num + 3) // 4) * 220
    else:
        based_w, based_h = 1200, 660 + (char_num - 5) // 5 * 110
        if (char_num - 5) % 5 >= 4:
            based_h += 110

    img = Image.open(TEXT_PATH / 'shin-w.jpg').resize((based_w, based_h))
    img.paste(tag, (0, 0), tag)
    img.paste(footbar, ((based_w - 800) // 2, based_h - 36), footbar)
    img_draw = ImageDraw.Draw(img, 'RGBA')

    img_draw.text(
        (97, 98),
        line1,
        white_color,
        gs_font_58,
        'lm',
    )
    img_draw.text(
        (99, 140),
        line2,
        white_color,
        gs_font_18,
        'lm',
    )
    tasks = []
    for index, char_data in enumerate(char_data_list):
        tasks.append(draw_enka_char(index, img, char_data))
    await asyncio.gather(*tasks)
    img = await convert_img(img)
    return img


async def draw_enka_char(index: int, img: Image.Image, char_data: dict):
    char_id = char_data['avatarId']
    char_star = await avatar_id_to_char_star(str(char_id))
    char_card = Image.open(TEXT_PATH / f'char_card_{char_star}.png')
    char_img = (
        Image.open(str(CHAR_PATH / f'{char_id}.png'))
        .convert('RGBA')
        .resize((204, 204))
    )
    char_temp = Image.new('RGBA', (220, 220))
    char_temp.paste(char_img, (8, 8), char_img)
    char_card.paste(char_temp, (0, 0), char_mask)
    if index <= 7:
        if img.size[0] <= 1100:
            x = 60 + (index % 4) * 220
        else:
            x = 160 + (index % 4) * 220
        img.paste(
            char_card,
            (x, 187 + (index // 4) * 220),
            char_card,
        )
    elif index <= 12:
        img.paste(
            char_card,
            (50 + (index % 8) * 220, 296),
            char_card,
        )
    else:
        _i = index - 13
        x, y = 50 + (_i % 9) * 220, 512 + (_i // 9) * 220
        if _i % 9 >= 5:
            y += 110
            x = 160 + ((_i - 5) % 9) * 220
        img.paste(
            char_card,
            (x, y),
            char_card,
        )
