import json
import asyncio
from typing import Tuple, Union, Literal

from PIL import Image, ImageDraw

from .mono.Character import Character
from .dmg_calc.dmg_calc import get_char_dmg_percent
from .etc.etc import TEXT_PATH, get_all_artifacts_value
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from ..utils.alias.avatarId_to_char_star import avatar_id_to_char_star
from ..utils.download_resource.RESOURCE_PATH import (
    CHAR_PATH,
    PLAYER_PATH,
    WEAPON_PATH,
)
from ..utils.draw_image_tools.draw_image_tool import (
    get_color_bg,
    get_qq_avatar,
    get_fetter_pic,
    get_talent_pic,
    draw_pic_with_ring,
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

gs_font_24 = genshin_font_origin(24)
gs_font_26 = genshin_font_origin(26)
gs_font_28 = genshin_font_origin(28)
gs_font_30 = genshin_font_origin(30)
gs_font_36 = genshin_font_origin(36)

char_rank_title = Image.open(TEXT_PATH / 'char_rank_title.png')
skill_mask = Image.open(TEXT_PATH / 'skill_mask.png')
percent_mask = Image.open(TEXT_PATH / 'percent_mask.png')
value_mask = Image.open(TEXT_PATH / 'value_mask.png')


async def draw_cahrcard_list(
    uid: str, qid: Union[str, int]
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

    char_done_list = []
    for char_name in char_list:
        temp = {}
        with open(uid_fold / f'{char_name}.json', 'r', encoding='UTF-8') as f:
            raw_data = json.load(f)

        skill_list = raw_data['avatarSkill']

        temp['char_name'] = char_name
        temp['fetter'] = raw_data['avatarFetter']
        temp['id'] = raw_data['avatarId']
        char = Character(raw_data)
        await char.new()
        await char.get_fight_prop()
        await get_char_dmg_percent(char)
        temp['percent'] = char.percent
        temp['percent'] = float(temp['percent'])
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
        # 武器
        temp['weapon_name'] = raw_data['weaponInfo']['weaponName']
        temp['weapon_level'] = raw_data['weaponInfo']['weaponLevel']
        temp['weapon_affix'] = raw_data['weaponInfo']['weaponAffix']
        temp['weapon_star'] = raw_data['weaponInfo']['weaponStar']
        char_done_list.append(temp)

    # 排序
    char_done_list.sort(key=lambda x: (-x['percent']))
    qid = str(qid)
    if qid.startswith('http'):
        char_pic = await get_qq_avatar(avatar_url=qid)
    else:
        char_pic = await get_qq_avatar(qid=qid)
    char_pic = await draw_pic_with_ring(char_pic, 320)

    img = await get_color_bg(950, 540 + 100 * len(char_done_list))
    img.paste(char_rank_title, (0, 0), char_rank_title)
    img.paste(char_pic, (318, 83), char_pic)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((475, 464), f'UID {uid}', black_color, gs_font_36, 'mm')

    tasks = []
    for index, char in enumerate(char_done_list):
        tasks.append(draw_single_rank(img, char, index))
    await asyncio.wait(tasks)

    res = await convert_img(img)
    return res


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


async def draw_single_rank(img: Image.Image, char: dict, index: int):
    char_id = char['id']
    char_rank = Image.open(TEXT_PATH / 'char_rank.png')
    char_pic = Image.open(CHAR_PATH / f'{char_id}.png')
    char_star = await avatar_id_to_char_star(char_id)
    weapon_star = str(char['weapon_star'])
    char_pic = await draw_pic_with_ring(
        char_pic, 82, star_color_map[char_star]
    )
    weapon_pic = Image.open(WEAPON_PATH / f'{char["weapon_name"]}.png')
    weapon_pic = await draw_pic_with_ring(
        weapon_pic, 82, star_color_map[weapon_star]
    )
    char_rank.paste(char_pic, (0, 0), char_pic)
    char_rank.paste(weapon_pic, (626, 0), weapon_pic)

    char_rank_draw = ImageDraw.Draw(char_rank)
    # 角色名称
    char_rank_draw.text(
        (85, 24), char['char_name'], black_color, gs_font_28, 'lm'
    )
    # AEQ等级
    for s_index, s in enumerate(['a', 'e', 'q']):
        s_offset = s_index * 38
        skill_color_img = Image.new(
            'RGBA',
            (35, 28),
            await get_color('skill', char[f'{s}_skill_level']),
        )
        char_rank.paste(skill_color_img, (86 + s_offset, 44), skill_mask)
        char_rank_draw.text(
            (103 + s_offset, 58),
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
    char_rank.paste(value_color_img, (233, 23), value_mask)
    char_rank_draw.text(
        (271, 40),
        f'{str(char["value"])[:4]}条',
        white_color,
        gs_font_24,
        'mm',
    )

    # 毕业度
    percent_color_img = Image.new(
        'RGBA',
        (99, 33),
        await get_color('percent', char['percent']),
    )
    char_rank.paste(percent_color_img, (329, 23), percent_mask)
    char_rank_draw.text(
        (379, 40),
        f'{char["percent"]}%',
        white_color,
        gs_font_24,
        'mm',
    )

    # 好感和天赋
    fetter_pic = await get_fetter_pic(char['fetter'])
    fetter_pic = fetter_pic.resize((77, 33))
    talent_pic = await get_talent_pic(char['talent_num'])
    talent_pic = talent_pic.resize((66, 33))

    char_rank.paste(fetter_pic, (444, 23), fetter_pic)
    char_rank.paste(talent_pic, (536, 23), talent_pic)

    # 武器
    weapon_affix_pic = await get_weapon_affix_pic(char['weapon_affix'])
    char_rank.paste(weapon_affix_pic, (714, 42), weapon_affix_pic)
    char_rank_draw.text(
        (788, 56), f'Lv.{char["weapon_level"]}', black_color, gs_font_26, 'lm'
    )
    char_rank_draw.text(
        (712, 22), str(char['weapon_name']), black_color, gs_font_26, 'lm'
    )

    img.paste(char_rank, (30, 540 + 100 * index), char_rank)
