import json
from typing import Dict, Union

import aiofiles
from PIL import Image, ImageDraw, ImageChops

from .mono.Character import Character
from ..utils.image.convert import convert_img
from .draw_normal import get_artifact_score_data
from .dmg_calc.dmg_calc import get_char_dmg_percent
from .etc.etc import TEXT_PATH, get_all_artifacts_value
from .etc.MAP_PATH import COLOR_MAP, avatarName2SkillAdd
from ..utils.image.image_tools import get_v4_bg, get_star_png
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_20,
    gs_font_22,
    gs_font_24,
    gs_font_28,
    gs_font_30,
    gs_font_36,
    gs_font_44,
)
from ..utils.resource.RESOURCE_PATH import (
    REL_PATH,
    ICON_PATH,
    PLAYER_PATH,
    WEAPON_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
    CHAR_NAMECARDPIC_PATH,
)

DMAP = {
    'Anemo': 0,
    'Cryo': 16,
    'Dendro': 335,
    'Electro': 106,
    'Geo': 219,
    'Hydro': 31,
    'Pyro': 161,
}


async def _get_single_artifact_info(aritifact: Dict) -> Image.Image:
    '''
    注意这里的aritifact不是原始的数据, 是带了评分的数据
    '''
    bg = Image.new('RGBA', (480, 136))
    fg = Image.open(TEXT_PATH / 'info_arti_fg.png')
    artifacts_img = (
        Image.open(REL_PATH / '{}.png'.format(aritifact['aritifactName']))
        .resize((128, 128))
        .convert('RGBA')
    )
    bg.paste(artifacts_img, (78, 4), artifacts_img)

    aritifactStar_img = get_star_png(aritifact['aritifactStar'])
    aritifactStar_img = aritifactStar_img.resize((96, 24))

    # 圣遗物星星和名称&位置
    bg.paste(aritifactStar_img, (94, 100), aritifactStar_img)
    bg.paste(fg, (0, 0), fg)
    bg_draw = ImageDraw.Draw(bg)

    mainValue: float = aritifact['reliquaryMainstat']['statValue']
    mainName: str = aritifact['reliquaryMainstat']['statName']
    mainLevel: int = aritifact['aritifactLevel']
    mainIcon = Image.open(TEXT_PATH / 'icon' / f'{mainName}.png')

    if mainName in ['攻击力', '血量', '防御力', '元素精通']:
        mainValueStr = str(mainValue)
    else:
        mainValueStr = str(mainValue) + '%'
    bg.paste(mainIcon, (202, 9), mainIcon)

    bg_draw.text(
        (168, 90),
        f'+{mainLevel}',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )

    bg_draw.text(
        (142, 24),
        mainValueStr,
        (255, 255, 255),
        gs_font_22,
        anchor='mm',
    )

    for index, i in enumerate(aritifact['reliquarySubstats']):
        subName: str = i['statName']
        subValue: float = i['statValue']
        subIcon = Image.open(TEXT_PATH / 'icon' / f'{subName}.png')

        if subName in ['攻击力', '血量', '防御力', '元素精通']:
            subValueStr = str(subValue)
        else:
            subValueStr = str(subValue) + '%'

        value_temp = i['value_score']

        # 副词条文字颜色
        if value_temp == 0:
            artifacts_color = (120, 120, 120)
        else:
            artifacts_color = (255, 255, 255)

        ox = (index % 2) * 113
        oy = (index // 2) * 33

        # 副词条底色
        if value_temp >= 3.4:
            artifacts_bg = (205, 135, 76)
            if value_temp >= 4.5:
                artifacts_bg = (158, 39, 39)
        else:
            artifacts_bg = (0, 0, 0, 100)

        bg_draw.rounded_rectangle(
            (207 + ox, 55 + oy, 307 + ox, 80 + oy),
            fill=artifacts_bg,
            radius=4,
        )

        subIcon = subIcon.resize((30, 30))
        bg.paste(subIcon, (208 + ox, 51 + oy), subIcon)

        bg_draw.text(
            (305 + ox, 68 + oy),
            '+{}'.format(subValueStr),
            artifacts_color,
            gs_font_20,
            anchor='rm',
        )

    artifactsScore = aritifact['value_score']
    cv_score = aritifact['cv_score']

    if artifactsScore >= 8.4:
        artifactsScore_color = (158, 39, 39)
    elif artifactsScore >= 6.5:
        artifactsScore_color = (205, 135, 76)
    elif artifactsScore >= 5.2:
        artifactsScore_color = (143, 123, 174)
    else:
        artifactsScore_color = (94, 96, 95)

    if cv_score >= 50:
        cv_color = (158, 39, 39)
    elif cv_score >= 45:
        cv_color = (205, 135, 76)
    elif cv_score >= 39:
        cv_color = (143, 123, 174)
    else:
        cv_color = (94, 96, 95)

    bg_draw.rounded_rectangle(
        (269, 22, 340, 42), fill=artifactsScore_color, radius=8
    )
    bg_draw.rounded_rectangle((349, 22, 420, 42), fill=cv_color, radius=8)

    bg_draw.text(
        (304, 32),
        '{:.2f}'.format(artifactsScore) + '条',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )

    bg_draw.text(
        (384, 32),
        '{:.1f}'.format(cv_score) + '分',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )

    return bg


async def get_single_artifact_info(aritifact: Dict, char: Character):
    new_aritifact = await get_artifact_score_data(aritifact, char)
    img = await _get_single_artifact_info(new_aritifact)
    for i in aritifact['reliquarySubstats']:
        char.artifacts_all_score += i['value_score']
    return img


ARTIFACTS_POS = {
    '生之花': (490, 537),
    '死之羽': (490, 673),
    '时之沙': (490, 809),
    '空之杯': (490, 945),
    '理之冠': (490, 1081),
}


async def get_attr_img(card_prop: Dict):
    fight_prop = card_prop['avatarFightProp']
    hp = fight_prop['hp']
    attack = fight_prop['atk']
    defense = fight_prop['def']
    em = fight_prop['elementalMastery']
    critrate = fight_prop['critRate']
    critdmg = fight_prop['critDmg']
    ce = fight_prop['energyRecharge']
    dmgBonus = (
        fight_prop['dmgBonus']
        if fight_prop['physicalDmgBonus'] <= fight_prop['dmgBonus']
        else fight_prop['physicalDmgBonus']
    )
    attr = Image.open(TEXT_PATH / 'info_attr_fg.png')
    attr_draw = ImageDraw.Draw(attr)
    attr_draw.text(
        (347, 105),
        str(round(hp)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 160),
        str(round(attack)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 215),
        str(round(defense)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 270),
        str(round(em)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 325),
        str(round(critrate * 100, 2)) + '%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 380),
        str(round(critdmg * 100, 2)) + '%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 435),
        str(round(ce * 100, 1)) + '%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    attr_draw.text(
        (347, 490),
        str(round(dmgBonus * 100, 1)) + '%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    return attr


async def get_weapon_img(char: Character) -> Image.Image:
    char_id = char.char_id
    card_prop = char.card_prop

    weapon_star_img = get_star_png(card_prop['weaponInfo']['weaponStar'])

    weaponAtk = card_prop['weaponInfo']['weaponStats'][0]['statValue']
    weaponName = card_prop['weaponInfo']['weaponName']
    weaponLevel = card_prop['weaponInfo']['weaponLevel']
    weaponAffix = card_prop['weaponInfo']['weaponAffix']

    weapon_img = Image.new('RGBA', (950, 1280))
    weapon_mask = Image.open(TEXT_PATH / 'info_weapon_bg.png')
    weapon_fg = Image.open(TEXT_PATH / 'info_weapon_fg.png')
    weapon = Image.open(WEAPON_PATH / f'{weaponName}.png').convert('RGBA')
    weapon = weapon.resize((174, 174))

    char_card_path = CHAR_NAMECARDPIC_PATH / f'{char_id}.png'
    if char_card_path.exists():
        char_card = (
            Image.open(CHAR_NAMECARDPIC_PATH / f'{char_id}.png')
            .convert('RGBA')
            .resize((560, 268))
        )
    else:
        char_card = Image.new('RGBA', (560, 268))

    weapon_img.paste(char_card, (70, 16), weapon_mask)
    weapon_img.paste(weapon, (124, 35), weapon)
    weapon_img.paste(weapon_fg, (0, 0), weapon_fg)
    weapon_img.paste(weapon_star_img, (147, 54), weapon_star_img)
    weapon_draw = ImageDraw.Draw(weapon_img)

    weapon_draw.text(
        (212, 222),
        weaponName,
        (255, 255, 255),
        gs_font_20,
        anchor='mm',
    )

    weapon_draw.text(
        (394, 71),
        f"Lv.{weaponLevel} / 90",
        (255, 255, 255),
        gs_font_20,
        anchor='mm',
    )

    weapon_draw.text(
        (530, 71),
        f"精{weaponAffix}",
        (255, 235, 0),
        gs_font_24,
        anchor='mm',
    )

    weapon_draw.text(
        (386, 117),
        f"{weaponAtk}",
        (255, 235, 0),
        gs_font_24,
        anchor='mm',
    )

    if len(card_prop['weaponInfo']['weaponStats']) == 2:
        weapon_sub_info = card_prop['weaponInfo']['weaponStats'][1]['statName']
        weapon_sub_value = card_prop['weaponInfo']['weaponStats'][1][
            'statValue'
        ]
        weapon_sub_icon = Image.open(
            TEXT_PATH / 'icon' / f'{weapon_sub_info}.png'
        )

        if '百分比' in weapon_sub_info:
            weapon_sub_value = str(weapon_sub_value) + '%'
        else:
            weapon_sub_value = str(weapon_sub_value)

        weapon_img.paste(weapon_sub_icon, (443, 97), weapon_sub_icon)
        weapon_draw.text(
            (562, 117),
            weapon_sub_value,
            (255, 255, 255),
            gs_font_24,
            anchor='rm',
        )
    else:
        weapon_draw.text(
            (504, 117),
            '无副词条',
            (255, 255, 255),
            gs_font_24,
            anchor='mm',
        )

    return weapon_img


async def get_char_img(char: Character):
    char_name = char.char_name
    card_prop = char.card_prop
    char_fg = Image.open(TEXT_PATH / 'info_char_fg.png')
    char_bg = Image.open(TEXT_PATH / 'info_char_bg.png')

    if char_name == '旅行者':
        char_img = (
            Image.open(CHAR_STAND_PATH / '10000007.png')
            .convert('RGBA')
            .resize((1776, 1000))
        )
    else:
        char_img = (
            Image.open(GACHA_IMG_PATH / f'{char_name}.png')
            .resize((1776, 1000))
            .convert('RGBA')
        )

    char_mask = Image.new('RGBA', (700, 1000))
    char_pic = Image.new('RGBA', (700, 1000))
    char_mask.paste(char_img, (-538, 0), char_img)
    char_pic.paste(char_mask, (0, 0), char_bg)
    char_pic.paste(char_fg, (0, 0), char_fg)
    char_draw = ImageDraw.Draw(char_pic)

    # 命座处理
    lock_img = Image.open(TEXT_PATH / 'icon_lock.png').resize((40, 40))
    for talent_num in range(0, 6):
        if talent_num + 1 <= len(card_prop['talentList']):
            talent = card_prop['talentList'][talent_num]
            try:
                talent_img = Image.open(
                    ICON_PATH / '{}.png'.format(talent['talentIcon'])
                )
            except Exception:
                talent_img = Image.open(
                    ICON_PATH / 'UI_Talent_S_Kazuha_02.png'
                )
            talent_img_new = talent_img.resize(
                (40, 40), Image.Resampling.LANCZOS
            ).convert("RGBA")
            for _ in range(2):
                char_pic.paste(
                    talent_img_new,
                    (134, 297 + talent_num * 69),
                    talent_img_new,
                )
        else:
            char_pic.paste(lock_img, (134, 297 + talent_num * 69), lock_img)

    # 天赋处理
    skillList = card_prop['avatarSkill']
    a_skill_level = skillList[0]['skillLevel']
    e_skill_level = skillList[1]['skillLevel']
    q_skill_level = skillList[-1]['skillLevel']

    if char.char_name in avatarName2SkillAdd:
        skill_add = avatarName2SkillAdd[char.char_name]
    else:
        skill_add = ['E', 'Q']
    for skillAdd_index in range(0, 2):
        if len(card_prop['talentList']) >= 3 + skillAdd_index * 2:
            if skill_add[skillAdd_index] == 'E':
                e_skill_level += 3
            elif skill_add[skillAdd_index] == 'Q':
                q_skill_level += 3
            elif skill_add[skillAdd_index] == 'A':
                a_skill_level += 3

    skill_level_list = [a_skill_level, e_skill_level, q_skill_level]

    for skill_num, skill in enumerate(skillList[0:2] + [skillList[-1]]):
        skill_img = Image.open(ICON_PATH / '{}.png'.format(skill['skillIcon']))
        skill_img_new = skill_img.resize(
            (50, 50), Image.Resampling.LANCZOS
        ).convert("RGBA")
        for _ in range(2):
            char_pic.paste(
                skill_img_new,
                (505, 488 + 100 * skill_num),
                skill_img_new,
            )
        level = skill_level_list[skill_num]
        if level >= 9:
            level_color = (255, 223, 0)
        else:
            level_color = (255, 255, 255)
        char_draw.text(
            (530, 558 + 100 * skill_num),
            f'{level}',
            level_color,
            gs_font_22,
            anchor='mm',
        )

    char_draw.text(
        (350, 885),
        f'{char.char_name}',
        (255, 233, 0),
        gs_font_44,
        anchor='mm',
    )

    char_draw.text(
        (350, 929),
        f'Lv: {char.char_level} / 90',
        (255, 255, 255),
        gs_font_30,
        anchor='mm',
    )

    return char_pic


async def draw_char_info(char: Character) -> Image.Image:
    overlay = Image.open(TEXT_PATH / 'info_bg_a.png')
    bg_color = COLOR_MAP[char.char_element]
    color_temp = Image.new('RGBA', overlay.size)
    color_img = Image.new('RGBA', overlay.size, bg_color)
    color_temp.paste(color_img, (0, 0), overlay)
    img = ImageChops.overlay(color_temp, overlay)

    card_prop = char.card_prop

    # 圣遗物部分
    for aritifact in card_prop['equipList']:
        artifactsPos = aritifact['aritifactPieceName']
        artifacts_img = await get_single_artifact_info(aritifact, char)
        img.paste(artifacts_img, ARTIFACTS_POS[artifactsPos], artifacts_img)

    # 属性部分
    attr_img = await get_attr_img(card_prop)
    img.paste(attr_img, (427, 13), attr_img)

    # 武器部分
    weapon_img = await get_weapon_img(char)
    img.paste(weapon_img, (-20, 52), weapon_img)

    # 角色部分
    char_img = await get_char_img(char)
    img.paste(char_img, (-20, 260), char_img)

    img_draw = ImageDraw.Draw(img)
    img_draw.rectangle((324, 256, 423, 293), (0, 105, 255))
    img_draw.rectangle((432, 256, 571, 293), (255, 0, 0))

    artifacts_all_score = await get_all_artifacts_value(
        char.card_prop, char.baseHp, char.baseAtk, char.baseDef, char.char_name
    )
    if char.percent == '0.00':
        percent_str = '暂无匹配'
    else:
        percent_str = f'{char.percent}%'

    img_draw.text(
        (374, 276),
        f'{artifacts_all_score:.2f}',
        (255, 255, 255),
        gs_font_36,
        anchor='mm',
    )

    img_draw.text(
        (504, 276),
        f'{percent_str}',
        (255, 255, 255),
        gs_font_36,
        anchor='mm',
    )

    return img


async def draw_all_char_list(uid: str) -> Union[str, bytes]:
    uid_fold = PLAYER_PATH / str(uid)
    char_file_list = uid_fold.glob('*')
    char_list = []
    for i in char_file_list:
        file_name = i.name
        if '\u4e00' <= file_name[0] <= '\u9fff':
            char_list.append(file_name.split('.')[0])
    if not char_list:
        return '你还没有已缓存的角色！\n请先使用【强制刷新】进行刷新！'

    char_done_list = {}
    player_name = '旅行者'
    for char_name in char_list:
        async with aiofiles.open(
            uid_fold / f'{char_name}.json', 'r', encoding='UTF-8'
        ) as f:
            raw_data = json.loads(await f.read())

        player_name = raw_data['playerName']
        char = Character(raw_data)
        await char.new()
        await char.get_fight_prop()
        await get_char_dmg_percent(char)

        char_done_list[float(char.percent)] = char

    sorted_items = sorted(
        char_done_list.items(),
        key=lambda item: item[0],
        reverse=True,
    )

    sorted_dict = {k: v for k, v in sorted_items}

    char_result = []
    for _, char in sorted_dict.items():
        char_result.append(await draw_char_info(char))
        if len(char_result) >= 8:
            break

    w, h = 4 * 950 + 50, ((len(char_result) - 1) // 4 + 1) * 1280 + 50
    bg = get_v4_bg(w, h)

    for index, cimg in enumerate(char_result):
        bg.paste(
            cimg, (25 + (index % 4) * 950, 25 + (index // 4) * 1280), cimg
        )

    bg_draw = ImageDraw.Draw(bg)
    bg_draw.text(
        (40, h - 30),
        f'{player_name} | UID: {uid}',
        (255, 255, 255),
        gs_font_28,
        anchor='lm',
    )

    res = await convert_img(bg)
    return res
