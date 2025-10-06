import json
import asyncio
from pathlib import Path
from typing import Tuple, Union, Literal

import aiofiles
from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error

from ..utils.image.convert import convert_img
from ..utils.mys_api import mys_api, get_base_data
from ..genshinuid_enka.mono.Character import Character
from ..genshinuid_compute.utils import get_all_char_dict
from ..utils.map.GS_MAP_PATH import charList, weaponList
from ..utils.map.name_covert import avatar_id_to_char_star
from ..genshinuid_enka.etc.etc import get_all_artifacts_value
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, PLAYER_PATH, WEAPON_PATH
from ..genshinuid_poetry_abyss.draw_poetry_abyss import (
    TEXT_PATH as POETRY_ABYSS_PATH,
)
from ..genshinuid_hard_challenge.draw_hard_challenge import (
    TEXT_PATH as HARD_CHALLENGE_PATH,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_26,
    gs_font_28,
    gs_font_30,
    gs_font_38,
    gs_font_40,
)
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_fetter_pic,
    get_talent_pic,
    get_weapon_affix_pic,
)

black_color = (24, 24, 24)
white_color = (245, 245, 245)

level_color = {
    5: (230, 0, 0),
    4: (203, 131, 21),
    3: (97, 17, 156),
    2: (17, 105, 156),
    1: (94, 96, 95),
}

level_map = {
    'skill': {
        10: 5,
        7: 4,
        5: 3,
        3: 2,
        0: 1,
    },
    'equip': {33: 5, 27: 4, 21: 3, 15: 2, 0: 1},
    'percent': {99: 5, 90: 4, 85: 3, 70: 2, 0: 1},
}
star_color_map = {
    '1': (94, 96, 95),
    '2': (17, 105, 156),
    '3': (91, 141, 192),
    '4': (143, 123, 174),
    '5': (205, 135, 76),
}

TEXT_PATH = Path(__file__).parent / 'texture2d'

ring = Image.open(TEXT_PATH / 'ring.png')
ring_mask = Image.open(TEXT_PATH / 'ring_mask.png')
skill_mask = Image.open(TEXT_PATH / 'skill_mask.png')
value_mask = Image.open(TEXT_PATH / 'value_mask.png')
div = Image.open(TEXT_PATH / 'div.png')


async def get_color(
    type: Literal['skill', 'equip', 'percent'], value: int
) -> Tuple[int, int, int]:
    for v in level_map[type]:
        if value >= v:
            level = level_map[type][v]
            break
    else:
        level = 1
    return level_color[level]


def draw_ring(img: Image.Image, star: int):
    bg_temp = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
    if star <= 4:
        bg = Image.open(TEXT_PATH / 'star_4.png')
    else:
        bg = Image.open(TEXT_PATH / 'star_5.png')

    img = img.resize((90, 90))
    bg_temp.paste(img, (0, 0), ring_mask)
    bg.paste(bg_temp, (0, 0), bg_temp)
    bg.paste(ring, (0, 0), ring)
    return bg


async def draw_char_count_list(
    uid: str,
    ev: Event,
) -> Union[str, bytes]:
    uid_fold = PLAYER_PATH / str(uid)
    char_file_list = uid_fold.glob('*')
    char_list = []
    for i in char_file_list:
        file_name = i.name
        if '\u4e00' <= file_name[0] <= '\u9fff':
            char_list.append(file_name.split('.')[0])
    if not char_list:
        return '你还没有已缓存的角色！\n请先使用【强制刷新】进行刷新！'

    datas = await get_base_data(uid)
    if isinstance(datas, (str, bytes)):
        return datas

    raw = await get_all_char_dict()
    pack_data = await mys_api.get_batch_compute_info(uid, raw)
    if isinstance(pack_data, int):
        return get_error(pack_data)

    for item in pack_data['overall_consume']:
        if item['id'] != 104319:
            continue
        crown_get = item['num'] - item['lack_num']

    crown_cost = 0
    """皇冠消耗"""

    fetter_full = 0
    """满好感角色"""

    full_star4_char = 0
    """满命4星角色"""

    full_star5_char = 0
    """满命5星角色"""

    star4_char = 0
    """4星角色"""

    star5_char = 0
    """5星角色"""

    full_star4_weapon = 0
    """满命4星武器"""

    full_star5_weapon = 0
    """满命5星武器"""

    star4_weapon = 0
    """4星武器"""

    star5_weapon = 0
    """5星武器"""

    high_score_equip_num = 0
    """高分圣遗物套装数量"""

    useful_char = 0
    """有用角色"""

    ALL_STAR_5_CHAR = len(
        [i for i in charList if charList[i]['rank'] == 'QUALITY_ORANGE']
    )
    ALL_STAR_4_CHAR = len(
        [i for i in charList if charList[i]['rank'] == 'QUALITY_PURPLE']
    )

    '''
    ALL_STAR_4_WEAPON = len(
        [i for i in weaponList if weaponList[i]['rank'] == 4]
    )
    '''

    ALL_STAR_5_WEAPON = len(
        [i for i in weaponList if weaponList[i]['rank'] == 5]
    )

    char_done_list = []
    for char_name in char_list:
        temp = {}
        async with aiofiles.open(
            uid_fold / f'{char_name}.json', 'r', encoding='UTF-8'
        ) as f:
            raw_data = json.loads(await f.read())

        skill_list = raw_data['avatarSkill']

        temp['char_name'] = char_name
        temp['fetter'] = raw_data['avatarFetter']
        if char_name == '旅行者':
            temp['fetter'] = 10

        temp['id'] = raw_data['avatarId']

        char = Character(raw_data)
        await char.new()
        await char.get_fight_prop()

        temp['value'] = await get_all_artifacts_value(
            raw_data,
            char.baseHp,
            char.baseAtk,
            char.baseDef,
            char_name,
        )
        temp['value'] = float('{:.2f}'.format(temp['value']))
        temp['avatarElement'] = raw_data['avatarElement']
        temp['a_skill_level'] = skill_list[0]['skillLevel']
        temp['e_skill_level'] = skill_list[1]['skillLevel']
        temp['q_skill_level'] = skill_list[-1]['skillLevel']
        temp['talent_num'] = len(raw_data['talentList'])

        if temp['a_skill_level'] >= 10:
            crown_cost += 1
        if temp['e_skill_level'] >= 10:
            crown_cost += 1
        if temp['q_skill_level'] >= 10:
            crown_cost += 1

        # 武器
        temp['weapon_name'] = raw_data['weaponInfo']['weaponName']
        temp['weapon_level'] = raw_data['weaponInfo']['weaponLevel']
        temp['weapon_affix'] = raw_data['weaponInfo']['weaponAffix']
        temp['weapon_star'] = raw_data['weaponInfo']['weaponStar']

        char_star = int(await avatar_id_to_char_star(temp['id']))
        temp['char_star'] = char_star

        temp['score_value'] = (
            temp['a_skill_level']
            + temp['e_skill_level']
            + temp['q_skill_level']
            + temp['talent_num'] * (char_star - 3)
            + temp['weapon_affix'] * (temp['weapon_star'] - 3)
            + temp['value']
        )
        char_done_list.append(temp)

        # 角色变量
        if temp['fetter'] >= 10:
            fetter_full += 1

        if char_star == 5:
            star5_char += 1
            if temp['talent_num'] >= 6:
                full_star5_char += 1
        elif char_star == 4:
            star4_char += 1
            if temp['talent_num'] >= 6:
                full_star4_char += 1

        # 武器变量
        if temp['weapon_star'] == 5:
            star5_weapon += 1
            if temp['weapon_affix'] >= 5:
                full_star5_weapon += 1
        elif temp['weapon_star'] == 4:
            star4_weapon += 1
            if temp['weapon_affix'] >= 5:
                full_star4_weapon += 1

        if temp['value'] >= 27:
            high_score_equip_num += 1

        if temp['value'] >= 24 and (
            temp['a_skill_level'] >= 8
            or temp['e_skill_level'] >= 8
            or temp['q_skill_level'] >= 8
        ):
            useful_char += 1

    if len(char_done_list) > 86:
        _mode = 3
    else:
        _mode = 2

    char_done_list.sort(key=lambda x: (-x['score_value']))

    title = Image.open(TEXT_PATH / f'title_{_mode}.png')
    title_fg = Image.open(TEXT_PATH / f'title_fg_{_mode}.png')

    char_pic = await get_avatar(ev, 180)
    title.paste(char_pic, (117, 328) if _mode == 3 else (88, 328), char_pic)
    title.paste(title_fg, (0, 0), title_fg)
    title_draw = ImageDraw.Draw(title)

    title_draw.text(
        (360, 428) if _mode == 3 else (331, 428),
        f'{ev.sender["nickname"] if "nickname" in ev.sender else "旅行者"}',
        'white',
        gs_font_40,
        'lm',
    )
    title_draw.text(
        (456, 478) if _mode == 3 else (427, 478),
        f'UID {uid}',
        (207, 207, 207),
        gs_font_30,
        'mm',
    )

    spiral_abyss = datas['stats']['spiral_abyss']
    role_combat = datas['stats']['role_combat']
    max_round_id = role_combat['max_round_id']
    hard_challenge = datas['stats']['hard_challenge']
    hard_level = (
        hard_challenge['difficulty']
        if hard_challenge['difficulty'] >= 3
        else 3
    )

    if role_combat['difficulty_id'] == 3:
        if role_combat['max_round_id'] == 8:
            icon_name = 'gold_yes.png'
        else:
            icon_name = 'gold_no.png'
    elif role_combat['difficulty_id'] == 4:
        if role_combat['max_round_id'] == 10:
            icon_name = 'super_yes.png'
        else:
            icon_name = 'super_no.png'
    elif role_combat['difficulty_id'] == 5:
        if (
            role_combat['max_round_id'] == 10
            and role_combat['tarot_finished_cnt'] == 2
        ):
            icon_name = 'moon_yes.png'
        else:
            icon_name = 'moon_no.png'
    else:
        icon_name = 'gold_no.png'

    icon = Image.open(POETRY_ABYSS_PATH / icon_name).convert('RGBA')
    title.paste(icon, (1882, 438) if _mode == 3 else (1151, 438), icon)

    hard_icon = (
        Image.open(HARD_CHALLENGE_PATH / f'medal_{hard_level}.png')
        .convert('RGBA')
        .resize((52, 52))
    )
    title.paste(
        hard_icon, (2057, 358) if _mode == 3 else (1326, 358), hard_icon
    )

    title_draw.text(
        (2208, 462) if _mode == 3 else (1476, 462),
        f'深渊{spiral_abyss}',
        'white',
        gs_font_28,
        'mm',
    )
    title_draw.text(
        (2208, 383) if _mode == 3 else (1476, 383),
        f'{hard_challenge["name"]}',
        'white',
        gs_font_28,
        'mm',
    )
    title_draw.text(
        (2033, 462) if _mode == 3 else (1301, 462),
        f'第{max_round_id}幕',
        'white',
        gs_font_28,
        'mm',
    )

    rows = (len(char_done_list) + _mode - 1) // _mode
    h = 750 + 80 + 90 * rows
    img = get_v4_bg(2370 if _mode == 3 else 1600, h)
    img.paste(title, (0, 0), title)

    # title_bar部分
    title_bar = Image.open(TEXT_PATH / f'title_bar_{_mode}.png')
    title_bar_draw = ImageDraw.Draw(title_bar)
    if _mode == 3:
        title_list = [
            f'{crown_cost}/{crown_get + crown_cost}',
            f'{fetter_full}/{len(char_list)}',
            f'{full_star5_char}/{star5_char}',
            f'{full_star4_char}/{star4_char}',
            f'{star5_char}/{ALL_STAR_5_CHAR}',
            f'{star4_char}/{ALL_STAR_4_CHAR}',
            f'{star5_weapon}/{ALL_STAR_5_WEAPON}',
            f'{full_star4_weapon}/{star4_weapon}',
            f'{full_star5_weapon}/{star5_weapon}',
            high_score_equip_num,
            useful_char,
        ]
        start_pos = (181, 52)
        offset = 201.8
    else:
        title_list = [
            f'{crown_cost}/{crown_get + crown_cost}',
            f'{fetter_full}/{len(char_list)}',
            f'{full_star5_char}/{star5_char}',
            f'{full_star4_char}/{star4_char}',
            f'{star5_char}/{ALL_STAR_5_CHAR}',
            f'{star4_char}/{ALL_STAR_4_CHAR}',
            f'{star5_weapon}/{ALL_STAR_5_WEAPON}',
            high_score_equip_num,
            useful_char,
        ]
        start_pos = (142, 52)
        offset = 187.4

    for index, title in enumerate(title_list):
        title_bar_draw.text(
            (int(start_pos[0] + index * offset), int(start_pos[1])),
            str(title),
            'white',
            gs_font_38,
            'mm',
        )

    img.paste(title_bar, (0, 570), title_bar)

    tasks = []
    for index, char in enumerate(char_done_list):
        tasks.append(draw_single_rank(img, char, index, _mode))
    await asyncio.gather(*tasks)

    img = add_footer(img, 900 if _mode == 3 else 700)
    img.paste(div, (0, h - 61), div)
    res = await convert_img(img)
    return res


async def draw_single_rank(
    img: Image.Image, char: dict, index: int, _mode: int
):
    char_id = char['id']
    char_rank = Image.open(TEXT_PATH / 'char_rank.png')
    char_pic = Image.open(CHAR_PATH / f'{char_id}.png')
    weapon_star = int(char['weapon_star'])
    char_pic = draw_ring(char_pic, char['char_star'])
    weapon_pic = Image.open(WEAPON_PATH / f'{char["weapon_name"]}.png')
    weapon_pic = draw_ring(weapon_pic, weapon_star)

    char_rank.paste(char_pic, (8, 0), char_pic)
    char_rank.paste(weapon_pic, (472, 0), weapon_pic)

    char_rank_draw = ImageDraw.Draw(char_rank)
    # 角色名称
    char_rank_draw.text(
        (98, 31),
        char['char_name'][:4],
        'white',
        gs_font_28,
        'lm',
    )

    # AEQ等级
    for s_index, s in enumerate(['a', 'e', 'q']):
        s_offset = s_index * 38
        skill_color_img = Image.new(
            'RGBA',
            (35, 28),
            await get_color('skill', char[f'{s}_skill_level']),
        )
        char_rank.paste(skill_color_img, (99 + s_offset, 48), skill_mask)
        char_rank_draw.text(
            (116 + s_offset, 62),
            str(char[f'{s}_skill_level']),
            white_color,
            gs_font_26,
            'mm',
        )

    # 圣遗物词条数
    value_color_img = Image.new(
        'RGBA',
        (77, 33),
        await get_color('equip', char['value']),
    )
    char_rank.paste(value_color_img, (225, 28), value_mask)
    char_rank_draw.text(
        (263, 45),
        f'{str(char["value"])[:4]}条',
        white_color,
        gs_font_24,
        'mm',
    )

    # 好感和天赋
    fetter_pic = await get_fetter_pic(char['fetter'])
    fetter_pic = fetter_pic.resize((77, 33))
    talent_pic = await get_talent_pic(char['talent_num'])
    talent_pic = talent_pic.resize((66, 33))

    char_rank.paste(fetter_pic, (308, 28), fetter_pic)
    char_rank.paste(talent_pic, (391, 28), talent_pic)

    # 武器
    weapon_affix_pic = await get_weapon_affix_pic(char['weapon_affix'])
    char_rank.paste(weapon_affix_pic, (561, 47), weapon_affix_pic)
    char_rank_draw.text(
        (635, 61),
        f'Lv.{char["weapon_level"]}',
        'white',
        gs_font_26,
        'lm',
    )
    char_rank_draw.text(
        (559, 27),
        str(char['weapon_name'][:7]),
        'white',
        gs_font_26,
        'lm',
    )

    img.paste(
        char_rank,
        (50 + (index % _mode) * 750, 750 + 90 * (index // _mode)),
        char_rank,
    )
