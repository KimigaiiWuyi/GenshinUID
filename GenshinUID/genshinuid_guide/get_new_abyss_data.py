from pathlib import Path
from typing import List, Literal

import httpx
import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.ambr.request import get_ambr_icon
from gsuid_core.utils.image.image_tools import get_color_bg

from ..version import Genshin_version
from .abyss_new_history import history_data
from ..utils.resource.RESOURCE_PATH import TEXT2D_PATH, MONSTER_ICON_PATH
from ..utils.map.GS_MAP_PATH import abyss_data, monster_data, ex_monster_data
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_26,
    gs_font_28,
    gs_font_36,
    gs_font_84,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'
monster_fg = Image.open(TEXT_PATH / 'monster_fg.png')
upper_tag = Image.open(TEXT_PATH / 'upper_tag.png')
lower_tag = Image.open(TEXT_PATH / 'lower_tag.png')


async def download_Oceanid():
    path = MONSTER_ICON_PATH / 'UI_MonsterIcon_Oceanid_Underling.png'
    if path.exists():
        return
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://enka.network/ui/UI_MonsterIcon_Oceanid_Underling.png'
        )
        async with aiofiles.open(path, 'wb') as file:
            await file.write(response.content)


async def get_half_img(data: List, half: Literal['Upper', 'Lower']):
    half_img = Image.new('RGBA', (1100, 3000), (0, 0, 0, 0))
    half_draw = ImageDraw.Draw(half_img)
    upper_h = 60
    temp = 0
    for index, wave in enumerate(data):
        monsters = wave['Monsters']
        wave_monster_uh = (((len(monsters) - 1) // 3) + 1) * 125 + 40
        upper_h += wave_monster_uh

        wave_tag = Image.open(TEXT_PATH / 'wave_tag.png')
        wave_tag_draw = ImageDraw.Draw(wave_tag)
        wave_tag_draw.text(
            (36, 20), f'第{index+1}波', (210, 210, 210), gs_font_24, 'lm'
        )
        if 'ExtraDesc' in wave:
            ExtraDesc: str = wave['ExtraDesc']['CH']
            ExtraDesc = ' > ' + ExtraDesc.replace('<b>', '').replace(
                '</b>', ''
            )
            half_draw.text(
                (150, 65 + temp), ExtraDesc, (210, 210, 210), gs_font_24, 'lm'
            )
        half_img.paste(wave_tag, (53, 45 + temp), wave_tag)
        for m_index, monster in enumerate(monsters):
            monster_id = monster['ID']
            real_id = str(monster_id)
            while len(real_id) < 5:
                real_id = '0' + real_id
            real_id = '2' + real_id + '01'
            monster_num = monster['Num']

            if real_id not in monster_data:
                monster_name = ex_monster_data[real_id]['name']
                icon_name = ex_monster_data[real_id]['icon']
            else:
                monster_name = monster_data[real_id]['name']
                icon_name = monster_data[real_id]['icon']

            if 'Mark' in monster:
                if monster['Mark']:
                    monster_name = '*' + monster_name

            monster_icon = await get_ambr_icon(
                'monster', icon_name, MONSTER_ICON_PATH
            )
            monster_icon = monster_icon.resize((89, 89))
            monster_img = Image.open(TEXT_PATH / 'monster_bg.png')
            monster_img.paste(monster_icon, (31, 19), monster_icon)
            monster_img.paste(monster_fg, (0, 0), monster_fg)

            monster_draw = ImageDraw.Draw(monster_img)
            monster_draw.text(
                (137, 52), monster_name[:10], 'white', gs_font_24, 'lm'
            )
            monster_draw.text(
                (137, 82),
                f'x{monster_num}',
                (210, 210, 210),
                gs_font_24,
                'lm',
            )
            half_img.paste(
                monster_img,
                (5 + (m_index % 3) * 360, 83 + (m_index // 3) * 110 + temp),
                monster_img,
            )
        temp += wave_monster_uh

    tag = upper_tag if half == 'Upper' else lower_tag
    half_img.paste(tag, (0, 0), tag)
    upper_bg = Image.new('RGBA', (1100, upper_h), (0, 0, 0, 0))
    upper_bg_draw = ImageDraw.Draw(upper_bg)
    upper_bg_draw.rounded_rectangle(
        (20, 30, 1080, upper_h - 20), 10, (16, 13, 13, 120)
    )
    half_img = half_img.crop((0, 0, 1100, upper_h))
    upper_bg.paste(half_img, (0, 0), half_img)
    return half_img


async def get_review_data(
    version: str = Genshin_version[:3], floor: str = '12'
):
    floor_data = history_data[version][floor]
    data = abyss_data[floor_data]
    floor_buff = data['Disorder']['CH'].replace('<b>', '').replace('</b>', '')
    floor_monster = data['Chambers']

    icon = Image.open(TEXT2D_PATH / 'icon.png')
    img = await get_color_bg(1100, 6000, TEXT_PATH / 'bg', True)
    img_draw = ImageDraw.Draw(img)

    img_draw.rounded_rectangle((421, 272, 548, 310), 10, (144, 0, 0))
    img_draw.rounded_rectangle((570, 272, 772, 310), 10, (27, 82, 155))

    img_draw.text((429, 239), floor_buff, (215, 215, 215), gs_font_26, 'lm')
    img_draw.text((425, 175), f'深境螺旋 {floor}层', 'white', gs_font_84, 'lm')

    img_draw.text((485, 291), f'版本{version}', 'white', gs_font_28, 'mm')
    img_draw.text((670, 291), '数据 妮可少年', 'white', gs_font_28, 'mm')

    img.paste(icon, (45, 80), icon)

    level_h = 456
    temp = 0
    for f_index, level in enumerate(floor_monster):
        level_monster_lv = level['Level']  # 72
        level_name = level['Name']  # '12-1'
        upper = level['Upper']
        lower = level['Lower']

        upper_img = await get_half_img(upper, 'Upper')
        lower_img = await get_half_img(lower, 'Lower')

        upper_h = upper_img.height
        lower_h = lower_img.height

        level_img = Image.new(
            'RGBA', (1100, upper_h + lower_h + 70), (0, 0, 0, 0)
        )

        level_draw = ImageDraw.Draw(level_img)
        level_draw.rounded_rectangle((320, 20, 780, 72), 10, (16, 13, 13, 120))
        level_draw.text(
            (550, 46),
            f'{level_name} · 怪物等级 Lv{level_monster_lv}',
            'white',
            gs_font_36,
            'mm',
        )

        level_img.paste(upper_img, (0, 60), upper_img)
        level_img.paste(lower_img, (0, 50 + upper_h), lower_img)
        level_h += upper_h + lower_h + 70
        img.paste(level_img, (0, 456 + temp), level_img)
        temp += level_img.height

    img = img.crop((0, 0, 1100, level_h))
    # 最后生成图片
    all_black = Image.new('RGBA', img.size, (0, 0, 0))
    img = Image.alpha_composite(all_black, img)
    return await convert_img(img)
