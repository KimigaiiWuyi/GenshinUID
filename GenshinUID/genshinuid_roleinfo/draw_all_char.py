from pathlib import Path

from PIL import Image, ImageDraw
from gsuid_core.utils.api.mys.models import IndexData
from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.image.convert import convert_img

from ..utils.image.image_tools import get_v4_bg
from ..utils.mys_api import mys_api, get_base_data
from ..utils.fonts.genshin_fonts import gs_font_28, gs_font_30
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    WEAPON_PATH,
    CHAR_NAMECARDPIC_PATH,
)

# 确定路径
TEXT_PATH = Path(__file__).parent / 'texture2d'
char_mask = Image.open(TEXT_PATH / 'charcard_mask.png')
char_fg = Image.open(TEXT_PATH / 'char_fg.png')


async def _draw_char_pic(uid: str, raw_data: IndexData):
    # 记录数据
    if raw_data:
        char_data = raw_data['avatars']
    else:
        return '没有找到角色信息!'

    char_ids = []
    for i in char_data:
        char_ids.append(i['id'])

    char_rawdata = await mys_api.get_character(uid, char_ids)
    if isinstance(char_rawdata, int):
        return await get_error_img(char_rawdata)
    char_datas = char_rawdata['list']

    for index, i in enumerate(char_datas):
        if i['rarity'] > 5:
            char_datas[index]['rarity'] = 4
            break

    char_datas.sort(
        key=lambda x: (
            -x['rarity'],
            -x['fetter'],
            -x['actived_constellation_num'],
        )
    )

    # 确定角色占用行数
    char_num = len(char_datas)
    char_hang = 1 + (char_num - 1) // 4

    # 获取背景图片各项参数
    target = (374, 195)
    based_w = 1680
    based_h = char_hang * target[1] + 160 + 80

    img = Image.new('RGBA', (based_w, based_h))

    div_d = Image.open(TEXT_PATH / 'div_d.png')
    img.paste(div_d, (0, 65), div_d)

    for index, char in enumerate(char_datas):
        char_star = char['rarity']
        char_id = char['id']
        char_talent = char['actived_constellation_num']
        char_fetter = char['fetter']
        char_lv = char['level']

        weapon_star = char['weapon']['rarity']
        weapon_name = char['weapon']['name']
        weapon_lv = char['weapon']['level']
        weapon_affix = char['weapon']['affix_level']

        char_bg = Image.open(TEXT_PATH / f'char_bg{char_star}.png')
        weapon_bg = Image.open(TEXT_PATH / f'weapon{weapon_star}.png')
        char_icon = Image.open(CHAR_PATH / f'{char_id}.png').convert('RGBA')
        talent_icon = Image.open(TEXT_PATH / 'mz' / f'{char_talent}.png')
        fetter_icon = Image.open(TEXT_PATH / 'hg' / f'{char_fetter}.png')
        weapon_icon = Image.open(WEAPON_PATH / f'{weapon_name}.png')

        char_card_path = CHAR_NAMECARDPIC_PATH / f'{char_id}.png'
        if char_card_path.exists():
            char_card = Image.open(
                CHAR_NAMECARDPIC_PATH / f'{char_id}.png'
            ).convert('RGBA')
        else:
            char_card = Image.new('RGBA', (560, 268))

        weapon_icon = weapon_icon.resize((174, 174)).convert('RGBA')
        char_card = char_card.resize((560, 268))

        char_bg.paste(char_card, (32, 29), char_mask)
        char_bg.paste(char_icon, (43, 35), char_icon)
        char_bg.paste(weapon_bg, (343, 33), weapon_bg)
        char_bg.paste(weapon_icon, (366, 55), weapon_icon)
        char_bg.paste(char_fg, (0, 0), char_fg)
        char_bg.paste(talent_icon, (273, 55), talent_icon)
        char_bg.paste(fetter_icon, (273, 124), fetter_icon)

        char_draw = ImageDraw.Draw(char_bg)
        char_draw.text((110, 261), f'Lv{char_lv}', 'White', gs_font_30, 'mm')
        char_draw.text((453, 264), weapon_name, 'White', gs_font_28, 'mm')
        char_draw.text((496, 212), f'Lv{weapon_lv}', 'White', gs_font_28, 'mm')
        char_draw.text((513, 80), str(weapon_affix), 'White', gs_font_28, 'mm')

        char_bg = char_bg.resize(target)

        img.paste(
            char_bg,
            (
                95 + (index % 4) * (target[0] + 5),
                80 + 80 + (index // 4) * target[1],
            ),
            char_bg,
        )

    return img


async def draw_char_pic(uid: str):
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes, bytearray, memoryview)):
        return raw_data

    img = await _draw_char_pic(uid, raw_data)
    if isinstance(img, (bytes, str)):
        return img
    elif isinstance(img, (bytearray, memoryview)):
        return bytes(img)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    return await convert_img(bg)
