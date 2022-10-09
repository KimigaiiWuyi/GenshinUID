import json
import asyncio
from pathlib import Path
from typing import List, Union, Optional

from PIL import Image, ImageDraw

from ...version import Genshin_version
from .enka_to_data import enka_to_dict
from ..download_resource.RESOURCE_PATH import CHAR_PATH
from ..draw_image_tools.send_image_tool import convert_img
from ..draw_image_tools.draw_image_tool import get_color_bg
from ..genshin_fonts.genshin_fonts import genshin_font_origin

half_color = (255, 255, 255, 120)
first_color = (29, 29, 29)
second_color = (67, 61, 56)
white_color = (247, 247, 247)
gs_font_26 = genshin_font_origin(26)
gs_font_28 = genshin_font_origin(28)

MAP_PATH = Path(__file__).parent / 'map'
TEXT_PATH = Path(__file__).parent / 'texture2d'
char_mask = Image.open(TEXT_PATH / 'char_mask.png')
char_cover = Image.open(TEXT_PATH / 'char_cover.png')
pic_500 = Image.open(TEXT_PATH / '500.png')
pic_204 = Image.open(TEXT_PATH / '204.png')
avatarId2Star_fileName = f'avatarId2Star_mapping_{Genshin_version}.json'

with open(MAP_PATH / avatarId2Star_fileName, "r", encoding='UTF-8') as f:
    avatarId2Star_data = json.load(f)


async def enka_to_card(
    uid: str, enka_data: Optional[dict] = None
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

    based_w, based_h = 950, ((len(char_data_list) + 3) // 4) * 220 + 200
    img = await get_color_bg(based_w, based_h, 'shin-w')
    img_rect = Image.new('RGBA', (based_w, based_h))
    img_rect_draw = ImageDraw.Draw(img_rect, 'RGBA')
    img_draw = ImageDraw.Draw(img, 'RGBA')

    img_rect_draw.rounded_rectangle(
        (45, 57, 907, 107), fill=half_color, radius=30
    )
    lu = (45, 134)
    rd = (907, based_h - 40)
    img_rect_draw.rounded_rectangle((lu, rd), fill=half_color, radius=50)
    img_rect.putalpha(
        img_rect.getchannel('A').point(
            lambda x: round(x * 0.4) if x > 0 else 0
        )
    )
    img.paste(img_rect, (0, 0), img_rect)
    img_draw.text(
        (476, 82),
        f'UID {uid} 刷新 {len(char_data_list)} 个角色! 使用 查询{char_data_list[0]["avatarName"]} 命令进行查询!',
        white_color,
        gs_font_28,
        'mm',
    )
    tasks = []
    for index, char_data in enumerate(char_data_list):
        tasks.append(draw_enka_char(index, img, char_data))
    await asyncio.gather(*tasks)
    img = await convert_img(img)
    return img


async def draw_enka_char(index: int, img: Image.Image, char_data: dict):
    char_name = char_data['avatarName']
    char_id = char_data['avatarId']
    char_star = avatarId2Star_data[str(char_id)]
    char_card = Image.open(TEXT_PATH / f'char_card_{char_star}.png')
    char_img = (
        Image.open(CHAR_PATH / f'{char_id}.png')
        .convert('RGBA')
        .resize((149, 149))
    )
    char_temp = Image.new('RGBA', char_card.size)
    char_temp.paste(char_img, (16, 16), char_mask)
    char_card.paste(char_temp, (0, 0), char_temp)
    char_card.paste(char_cover, (0, 0), char_cover)
    char_card_draw = ImageDraw.Draw(char_card)
    char_card_draw.text((90, 196), char_name, white_color, gs_font_26, 'mm')
    img.paste(
        char_card,
        (75 + (index % 4) * 210, 134 + (index // 4) * 220),
        char_card,
    )
