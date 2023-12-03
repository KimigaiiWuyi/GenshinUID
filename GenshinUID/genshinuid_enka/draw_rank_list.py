from typing import Dict, Union

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.image.image_tools import crop_center_img

from .etc.etc import TEXT_PATH
from ..utils.colors import get_color
from .get_akasha_data import _get_rank
from ..utils.image.image_tools import get_avatar
from ..utils.map.name_covert import avatar_id_to_name
from .to_card import draw_char_card, draw_weapon_card
from ..utils.fonts.genshin_fonts import (
    gs_font_15,
    gs_font_22,
    gs_font_26,
    gs_font_32,
    gs_font_44,
)

RANK_TEXT = TEXT_PATH / 'rank_img'
BG_PATH = RANK_TEXT / 'dark_blue.jpg'
TITLE_PATH = RANK_TEXT / 'title.png'

grey = (191, 191, 191)


async def draw_rank_img(ev: Event, uid: str) -> Union[bytes, str]:
    rank_data = await _get_rank(uid)
    if isinstance(rank_data, str):
        return rank_data

    user_pic = await get_avatar(ev, 314)
    title = Image.open(TITLE_PATH)
    title_draw = ImageDraw.Draw(title)

    title.paste(user_pic, (318, 57), user_pic)
    title_draw.text((475, 425), f'UID {uid}', 'white', gs_font_26, 'mm')

    w, h = 950, 500 + len(rank_data) * 305 + 50
    img = crop_center_img(Image.open(BG_PATH), w, h)

    img.paste(title, (0, 0), title)

    for index, char in enumerate(rank_data):
        raw_data = rank_data[char]

        time = raw_data['time']
        data = raw_data['calculations']['fit']
        stats: Dict = data['stats']
        char_name = await avatar_id_to_name(char)
        result = '{:.2f}'.format(data['result'])
        rank = data['ranking']
        if isinstance(rank, str):
            rank = int(rank[1:])
        outof = data['outOf']
        _pc = float('{:.2f}'.format((rank / outof) * 100))

        _hp = str(int(float(stats['maxHP'])))
        _atk = str(int(float(stats['maxATK'])))
        _def = str(int(float(stats['maxDEF'])))
        _em = str(int(float(stats['elementalMastery'])))
        _er = '{:.2f}%'.format(stats['energyRecharge'])
        _cr = '{:.2f}%'.format(stats['critRate'])
        _cd = '{:.2f}%'.format(stats['critDMG'])
        _cv = int(float(stats['critValue']))
        _dmg = '{:.1f}%'.format(list(stats.values())[-1])

        char_card = await draw_char_card(char)
        weapon_card = await draw_weapon_card(
            data['weapon']['icon'], data['weapon']['rarity']
        )
        weapon_card = weapon_card.resize((110, 110))

        _color = get_color(_pc, [10, 23, 34, 55], True)
        cv_color = get_color(_cv, [210, 185, 170, 150])

        color = Image.new('RGBA', (950, 300), _color)

        tag_weapon = Image.open(
            TEXT_PATH / f'char_card_{data["weapon"]["refinement"]}.png'
        ).resize((40, 40))

        if index % 2 == 0:
            char_img = Image.open(RANK_TEXT / 'left.png')
            bar = Image.open(RANK_TEXT / 'left_bar.png')
            char_img.paste(color, (0, 0), bar)
            char_img.paste(char_card, (-40, 1), char_card)
            char_img.paste(weapon_card, (78, 166), weapon_card)
            char_img.paste(tag_weapon, (140, 140), tag_weapon)

            char_draw = ImageDraw.Draw(char_img)

            char_draw.text(
                (880, 39), f'数据最后更新于 {time}', grey, gs_font_15, 'rm'
            )
            char_draw.text(
                (174, 37), f'{char_name}', 'white', gs_font_32, 'lm'
            )

            char_draw.text(
                (161, 161),
                str(data["weapon"]["refinement"]),
                'white',
                gs_font_26,
                'mm',
            )

            char_draw.text((361, 129), _hp, 'white', gs_font_26, 'lm')
            char_draw.text((361, 169), _atk, 'white', gs_font_26, 'lm')
            char_draw.text((361, 210), _def, 'white', gs_font_26, 'lm')

            char_draw.text((564, 129), _em, 'white', gs_font_26, 'lm')
            char_draw.text((564, 169), _er, 'white', gs_font_26, 'lm')
            char_draw.text((564, 210), _dmg, 'white', gs_font_26, 'lm')

            char_draw.text((791, 129), _cr, 'white', gs_font_26, 'lm')
            char_draw.text((791, 169), _cd, 'white', gs_font_26, 'lm')

            char_draw.text((263, 260), '测试项目: 未知', grey, gs_font_22, 'lm')
            char_draw.text(
                (716, 257), str(int(float(result))), 'white', gs_font_44, 'lm'
            )

            char_draw.rounded_rectangle((258, 65, 384, 95), 20, cv_color)
            char_draw.rounded_rectangle((389, 65, 547, 95), 20, _color)
            char_draw.rounded_rectangle((552, 65, 710, 95), 20, _color)

            char_draw.text((321, 80), f'{_cv}分', 'white', gs_font_26, 'mm')
            char_draw.text((467, 80), f'{rank}名', 'white', gs_font_26, 'mm')
            char_draw.text((631, 80), f'前{_pc}%', 'white', gs_font_26, 'mm')
        else:
            char_img = Image.open(RANK_TEXT / 'right.png')
            bar = Image.open(RANK_TEXT / 'right_bar.png')
            char_img.paste(color, (0, 0), bar)
            char_img.paste(char_card, (775, 1), char_card)
            char_img.paste(weapon_card, (770, 166), weapon_card)
            char_img.paste(tag_weapon, (768, 140), tag_weapon)

            char_draw = ImageDraw.Draw(char_img)

            char_draw.text((65, 39), f'数据最后更新于 {time}', grey, gs_font_15, 'lm')
            char_draw.text(
                (760, 37), f'{char_name}', 'white', gs_font_32, 'rm'
            )

            char_draw.text(
                (789, 161),
                str(data["weapon"]["refinement"]),
                'white',
                gs_font_26,
                'mm',
            )

            char_draw.text((599, 129), _hp, 'white', gs_font_26, 'lm')
            char_draw.text((599, 169), _atk, 'white', gs_font_26, 'lm')
            char_draw.text((599, 210), _def, 'white', gs_font_26, 'lm')

            char_draw.text((386, 129), _em, 'white', gs_font_26, 'lm')
            char_draw.text((386, 169), _er, 'white', gs_font_26, 'lm')
            char_draw.text((386, 210), _dmg, 'white', gs_font_26, 'lm')

            char_draw.text((169, 129), _cr, 'white', gs_font_26, 'lm')
            char_draw.text((169, 169), _cd, 'white', gs_font_26, 'lm')

            char_draw.text((669, 260), '测试项目: 未知', grey, gs_font_22, 'rm')
            char_draw.text(
                (237, 249), str(int(float(result))), 'white', gs_font_44, 'rm'
            )

            char_draw.rounded_rectangle((52, 65, 177, 95), 20, cv_color)
            char_draw.rounded_rectangle((183, 65, 341, 95), 20, _color)
            char_draw.rounded_rectangle((346, 65, 504, 95), 20, _color)

            char_draw.text((115, 80), f'{_cv}分', 'white', gs_font_26, 'mm')
            char_draw.text((261, 80), f'{rank}名', 'white', gs_font_26, 'mm')
            char_draw.text((425, 80), f'前{_pc}%', 'white', gs_font_26, 'mm')

        img.paste(char_img, (0, 485 + index * 305), char_img)

    return await convert_img(img)
