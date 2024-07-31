from typing import Union, Optional

from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img

from ..utils.colors import get_color
from .draw_rank_list import RANK_TEXT
from .get_akasha_data import _get_rank
from ..utils.api.cv.request import _CvApi
from ..utils.map.GS_MAP_PATH import icon2Name
from ..genshinuid_config.gs_config import gsconfig
from ..utils.resource.RESOURCE_PATH import REL_PATH, CHAR_PATH
from ..utils.map.name_covert import name_to_avatar_id, alias_to_char_name
from ..utils.image.image_tools import (
    get_talent_pic,
    draw_pic_with_ring,
    get_weapon_affix_pic,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_20,
    gs_font_24,
    gs_font_26,
    gs_font_30,
)

is_enable_akasha = gsconfig.get_config('EnableAkasha').data

REGION_MAP = {
    'CN': (255, 58, 58),
    'ASIA': (169, 109, 57),
    'NA': (255, 165, 0),
    'EU': (80, 98, 255),
    'TW': (37, 37, 37),
    'B': (128, 35, 151),
}

grey = (170, 170, 170)


async def draw_role_rank_img(
    char_name: str, player_uid: Optional[str] = None
) -> Union[str, bytes]:
    if not is_enable_akasha:
        return '未开启排名系统...'
    cv_api = _CvApi()

    char_name = await alias_to_char_name(char_name)
    char_id = await name_to_avatar_id(char_name)

    if player_uid:
        rank_data = await _get_rank(player_uid)
        if isinstance(rank_data, str):
            return rank_data
        if char_id not in rank_data:
            return f'你还暂无{char_name}的数据, 请先[强制刷新]...'

        fit = rank_data[char_id]['calculations']['fit']
        calculation_id = fit['calculationId']
        r0 = int(fit["result"])
        r1 = int(r0 * 1.00005)
        raw_data = await cv_api.get_sort_list(char_id, calculation_id, r1)
        tag = '角色附近'
    else:
        raw_data = await cv_api.get_sort_list(char_id)
        tag = '前20'

    if raw_data is None:
        return '该角色尚未有排名...'

    data, count = raw_data

    img = Image.open(RANK_TEXT / 'deep_grey.jpg').resize((950, 2450))
    title = Image.open(RANK_TEXT / 'title.png')
    user_pic = await draw_pic_with_ring(
        Image.open(CHAR_PATH / f'{char_id}.png'), 314
    )
    title.paste(user_pic, (318, 57), user_pic)
    img.paste(title, (0, 0), title)

    img_draw = ImageDraw.Draw(img)
    img_draw.text(
        (475, 425), f'{tag} / 总数据 {count}条', 'white', gs_font_26, 'mm'
    )

    rank = 0
    for index, char in enumerate(data):
        region: str = char['owner']['region']
        nickname: str = char['owner']['nickname']

        if index == 0:
            _rank: str = char['index']
            rank = (
                int(_rank[1:])
                if isinstance(_rank, str) and _rank.startswith('~')
                else int(_rank)
            )
        else:
            rank += 1

        uid: str = char['uid']

        char_c = 'white'
        if player_uid and player_uid == uid:
            bar = Image.open(RANK_TEXT / 'sp.png')
        elif index % 2 == 0:
            bar = Image.open(RANK_TEXT / 'white.png')
        else:
            bar = Image.open(RANK_TEXT / 'black.png')

        _c: int = char['constellation']
        _wc: int = char['weapon']['weaponInfo']['refinementLevel']['value'] + 1
        hp: int = int(char['stats']['maxHp']['value'])
        atk: int = int(char['stats']['atk']['value'])
        cr = '{:.1f}'.format(char['stats']['critRate']['value'] * 100)
        cd = '{:.1f}'.format(char['stats']['critDamage']['value'] * 100)
        cv = '{:.1f}'.format(char['critValue'])

        cv_color = get_color(float(cv), [260, 245, 225, 180])

        affix_pic = await get_weapon_affix_pic(_wc)
        talent_pic = await get_talent_pic(_c)

        if region in REGION_MAP:
            region_color = REGION_MAP[region]
        else:
            region_color = (128, 128, 128)

        icon_list = []
        for art in char['artifactSets']:
            item = char['artifactSets'][art]
            if item['count'] >= 2:
                url: str = item['icon']
                icon_name = url.split('/')[-1].split('.')[0]
                icon_img = Image.open(REL_PATH / f'{icon2Name[icon_name]}.png')
                icon_img = icon_img.convert('RGBA')
                if item['count'] >= 4:
                    icon_list.clear()
                    icon_list.append(icon_img.resize((64, 64)))
                else:
                    icon_list.append(icon_img.resize((51, 51)))

        x1, x2 = 15, 64 + 15 * len(str(rank))
        x3 = int((x1 + x2) / 2)

        bar_draw = ImageDraw.Draw(bar)

        bar_draw.rounded_rectangle((x1, 0, x2, 25), 9, (96, 33, 109))
        bar_draw.text((x3 + 1, 13), f'#{rank}名', 'white', gs_font_24, 'mm')

        bar_draw.rounded_rectangle((47, 35, 150, 75), 10, region_color)
        bar_draw.text((99, 55), region, 'white', gs_font_30, 'mm')

        bar_draw.text((162, 41), nickname, char_c, gs_font_26, 'lm')
        bar_draw.text((162, 66), f'UID {uid}', grey, gs_font_20, 'lm')
        bar_draw.text((398, 42), f'{cr}: {cd}', 'white', gs_font_26, 'lm')
        bar_draw.text((398, 66), f'{cv} cv', cv_color, gs_font_20, 'lm')
        bar_draw.text((665, 34), f'{hp}', 'white', gs_font_26, 'lm')
        bar_draw.text((665, 70), f'{atk}', 'white', gs_font_26, 'lm')
        bar.paste(talent_pic, (764, 35), talent_pic)
        bar.paste(affix_pic, (840, 35), affix_pic)

        if len(icon_list) == 1:
            bar.paste(icon_list[0], (325, 18), icon_list[0])
            text = '4'
        elif len(icon_list) == 2:
            text = '2+2'
            bar.paste(icon_list[0], (334, 15), icon_list[0])
            bar.paste(icon_list[1], (318, 30), icon_list[1])
        else:
            text = '0'

        bar_draw.text((370, 67), text, (214, 255, 192), gs_font_20, 'mm')

        img.paste(bar, (0, 475 + index * 95), bar)

    img_draw.text(
        (475, img.size[1] - 35),
        'Power by Wuyi无疑 & '
        'Data by AKS & CV '
        'Created by GsCore & GenshinUID',
        (200, 200, 200),
        gs_font_18,
        anchor='mm',
    )
    await cv_api.close()
    return await convert_img(img)
