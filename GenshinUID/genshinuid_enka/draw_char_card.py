import json
import math
import asyncio
from io import BytesIO
from pathlib import Path
from typing import Tuple, Union, Optional

from httpx import get
from PIL import Image, ImageDraw, ImageChops

from .propCalc.prop_calc import get_card_prop
from ..utils.db_operation.db_operation import config_check
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from .dmgCalc.dmg_calc import (
    DMG_PATH,
    calc_prop,
    draw_dmgCacl_img,
    get_char_percent,
    avatarName2SkillAdd,
)
from ..utils.download_resource.RESOURCE_PATH import (
    REL_PATH,
    ICON_PATH,
    PLAYER_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
)

R_PATH = Path(__file__).parent
TEXT_PATH = R_PATH / 'texture2D'
ETC_PATH = R_PATH / 'etc'


COLOR_MAP = {
    'Anemo': (43, 170, 163),
    'Cryo': (97, 168, 202),
    'Dendro': (84, 169, 62),
    'Electro': (150, 62, 169),
    'Geo': (169, 143, 62),
    'Hydro': (66, 98, 182),
    'Pyro': (169, 62, 67),
}

SCORE_MAP = {
    '暴击率': 2,
    '暴击伤害': 1,
    '元素精通': 0.25,
    '元素充能效率': 0.65,
    '百分比血量': 0.86,
    '百分比攻击力': 1,
    '百分比防御力': 0.7,
    '血量': 0.014,
    '攻击力': 0.12,
    '防御力': 0.18,
}

VALUE_MAP = {
    '攻击力': 4.975,
    '血量': 4.975,
    '防御力': 6.2,
    '元素精通': 19.75,
    '元素充能效率': 5.5,
    '暴击率': 3.3,
    '暴击伤害': 6.6,
}

# 引入ValueMap
with open(ETC_PATH / 'ValueAttrMap.json', 'r', encoding='UTF-8') as f:
    ATTR_MAP = json.load(f)

# 引入offset
with open(ETC_PATH / 'avatarOffsetMap.json', 'r', encoding='UTF-8') as f:
    avatarOffsetMap = json.load(f)

# 引入offset2
with open(ETC_PATH / 'avatarCardOffsetMap.json', 'r', encoding='UTF-8') as f:
    avatarCardOffsetMap = json.load(f)


def get_star_png(star: int) -> Image.Image:
    png = Image.open(TEXT_PATH / 's-{}.png'.format(str(star)))
    return png


def strLenth(r: str, size: int, limit: int = 540) -> str:
    result = ''
    temp = 0
    for i in r:
        if temp >= limit:
            result += '\n' + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == '/':
            temp += round(size / 10 * 2.2)
        elif i == '.':
            temp += round(size / 10 * 3)
        elif i == '%':
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result


async def get_artifacts_score(subName: str, subValue: int) -> int:
    score = subValue * SCORE_MAP[subName]
    return score


async def get_artifacts_value(
    subName: str,
    subValue: int,
    baseAtk: int,
    baseHp: int,
    baseDef: int,
    charName: str,
) -> float:
    if charName not in ATTR_MAP:
        ATTR_MAP[charName] = ['攻击力', '暴击率', '暴击伤害']
    if subName in ATTR_MAP[charName] and subName in ['血量', '防御力', '攻击力']:
        if subName == '血量':
            base = (subValue / baseHp) * 100
        elif subName == '防御力':
            base = (subValue / baseDef) * 100
        elif subName == '攻击力':
            base = (subValue / baseAtk) * 100
        else:
            base = 1.0
        value = float('{:.2f}'.format(base / VALUE_MAP[subName]))
    elif subName in ['百分比血量', '百分比防御力', '百分比攻击力']:
        subName = subName.replace('百分比', '')
        if subName in ATTR_MAP[charName]:
            value = float('{:.2f}'.format(subValue / VALUE_MAP[subName]))
        else:
            return 0
    else:
        if subName in ATTR_MAP[charName]:
            value = float('{:.2f}'.format(subValue / VALUE_MAP[subName]))
        else:
            value = 0

    if charName == '胡桃' and subName == '攻击力':
        value = value * 0.4
    return value


async def get_all_artifacts_value(
    raw_data: dict, baseHp: int, baseAtk: int, baseDef: int, char_name: str
) -> int:
    artifactsValue = 0
    for aritifact in raw_data:
        for i in aritifact['reliquarySubstats']:
            subName = i['statName']
            subValue = i['statValue']
            value_temp = await get_artifacts_value(
                subName, subValue, baseAtk, baseHp, baseDef, char_name
            )
            artifactsValue += value_temp
    return artifactsValue


async def draw_char_img(
    raw_data: dict, weapon: Optional[str] = None, charUrl: Optional[str] = None
) -> Union[bytes, str]:
    if not await config_check('OldPanle'):
        raw_data = await get_card_prop(raw_data, weapon)
        if raw_data == {}:
            return '要替换的武器不正确或发生了未知错误~'
    char_name = raw_data['avatarName']
    char_level = raw_data['avatarLevel']
    char_fetter = raw_data['avatarFetter']

    char_bytes = None
    if await config_check('RandomPic') and charUrl is None:
        if char_name == '旅行者':
            char_name_url = '荧'
        else:
            char_name_url = char_name
        charUrl = f'http://img.genshin.cherishmoon.fun/{char_name_url}'
        char_data = get(charUrl, follow_redirects=True)
        if char_data.headers['Content-Type'] == 'application/json':
            charUrl = None
        else:
            char_bytes = char_data.content

    based_w, based_h = 600, 1200
    if charUrl:
        offset_x, offset_y = 200, 0
        if char_bytes is None:
            char_bytes = get(charUrl).content
        char_img = Image.open(BytesIO(char_bytes)).convert('RGBA')
    else:
        if char_name in avatarOffsetMap:
            offset_x, offset_y = (
                avatarOffsetMap[char_name][0],
                avatarOffsetMap[char_name][1],
            )
        else:
            offset_x, offset_y = 200, 0
        if char_name == '旅行者':
            char_img = (
                Image.open(CHAR_STAND_PATH / f'{raw_data["avatarId"]}.png')
                .convert('RGBA')
                .resize((1421, 800))
            )
        else:
            char_img = Image.open(GACHA_IMG_PATH / f'{char_name}.png')  # 角色图像

    # 确定图片的长宽
    w, h = char_img.size
    if (w, h) != (based_w, based_h):
        # offset_all = offset_x if offset_x >= offset_y else offset_y
        based_new_w, based_new_h = based_w + offset_x, based_h + offset_y
        based_scale = '%.3f' % (based_new_w / based_new_h)
        scale_f = '%.3f' % (w / h)
        new_w = math.ceil(based_new_h * float(scale_f))
        new_h = math.ceil(based_new_w / float(scale_f))
        if scale_f > based_scale:
            bg_img2 = char_img.resize(
                (new_w, based_new_h), Image.Resampling.LANCZOS  # type: ignore
            )
            x1 = new_w / 2 - based_new_w / 2 + offset_x
            y1 = 0 + offset_y / 2
            x2 = new_w / 2 + based_new_w / 2
            y2 = based_new_h - offset_y / 2
        else:
            bg_img2 = char_img.resize(
                (based_new_w, new_h), Image.Resampling.LANCZOS  # type: ignore
            )
            x1 = 0 + offset_x
            y1 = new_h / 2 - based_new_h / 2 + offset_y / 2
            x2 = based_new_w
            y2 = new_h / 2 + based_new_h / 2 - offset_y / 2
        char_img = bg_img2.crop((x1, y1, x2, y2))  # type: ignore

    with open(DMG_PATH / 'char_action.json', "r", encoding='UTF-8') as f:
        char_action = json.load(f)
    # 拿到倍率表
    if char_name not in char_action:
        power_list = char_action[char_name]
        new_prop = await calc_prop(raw_data, {})
        dmg_img, dmg_len = Image.new('RGBA', (950, 1)), 0
    else:
        power_list = char_action[char_name]
        # 额外增加钟离倍率
        if char_name == '钟离':
            power_list['E总护盾量'] = {
                'name': 'E总护盾量',
                'type': '生命值',
                'plus': 1,
                'value': [
                    f'{power_list["E护盾附加吸收量"]["value"][index]}+{i}'
                    for index, i in enumerate(power_list['E护盾基础吸收量']['value'])
                ],
            }
        new_prop = await calc_prop(raw_data, power_list)
        dmg_img, dmg_len = await draw_dmgCacl_img(
            raw_data, power_list, new_prop
        )
    img_w, img_h = 950, 1850 + dmg_len * 40
    overlay = Image.open(TEXT_PATH / 'overlay.png')
    overlay_w, overlay_h = overlay.size
    if overlay_h < img_h:
        new_overlay_h = img_h
        new_overlay_w = math.ceil(new_overlay_h * overlay_w / overlay_h)
        overlay = overlay.resize(
            (new_overlay_w, new_overlay_h), Image.Resampling.LANCZOS
        )
        overlay = overlay.crop((0, 0, img_w, img_h))
    color_img = Image.new(
        'RGBA', overlay.size, COLOR_MAP[raw_data['avatarElement']]
    )
    img = ImageChops.overlay(color_img, overlay)
    char_info_1 = Image.open(TEXT_PATH / 'char_info_1.png')
    char_info_mask = Image.open(TEXT_PATH / 'char_info_mask.png')

    img_temp = Image.new('RGBA', (based_w, based_h), (0, 0, 0, 0))
    img_temp.paste(char_img, (0, 0), char_info_mask)
    img.paste(img_temp, (0, 0), img_temp)
    img.paste(char_info_1, (0, 0), char_info_1)
    img.paste(dmg_img, (0, 1850), dmg_img)

    lock_img = Image.open(TEXT_PATH / 'icon_lock.png')

    # 命座处理
    holo_img = Image.open(TEXT_PATH / 'holo.png')
    holo_color = Image.new(
        'RGBA', holo_img.size, COLOR_MAP[raw_data['avatarElement']]
    )
    for talent_num in range(0, 6):
        if talent_num + 1 <= len(raw_data['talentList']):
            talent = raw_data['talentList'][talent_num]
            talent_img = Image.open(
                ICON_PATH / '{}.png'.format(talent['talentIcon'])
            )
            talent_img_new = talent_img.resize(
                (50, 50), Image.Resampling.LANCZOS  # type: ignore
            ).convert("RGBA")
            img.paste(holo_color, (775, 300 + talent_num * 81), holo_img)
            img.paste(
                talent_img_new, (850, 375 + talent_num * 81), talent_img_new
            )
        else:
            img.paste(lock_img, (850, 375 + talent_num * 81), lock_img)

    # 天赋处理
    skillList = raw_data['avatarSkill']
    # a_skill_name = skillList[0]['skillName'].replace('普通攻击·', '')
    a_skill_level = skillList[0]['skillLevel']
    # e_skill_name = skillList[1]['skillName']
    e_skill_level = skillList[1]['skillLevel']
    # q_skill_name = skillList[-1]['skillName']
    q_skill_level = skillList[-1]['skillLevel']

    skill_add = avatarName2SkillAdd[char_name]
    for skillAdd_index in range(0, 2):
        if len(raw_data['talentList']) >= 3 + skillAdd_index * 2:
            if skill_add[skillAdd_index] == 'E':
                e_skill_level += 3
            elif skill_add[skillAdd_index] == 'Q':
                q_skill_level += 3

    for skill_num, skill in enumerate(skillList[0:2] + [skillList[-1]]):
        skill_img = Image.open(ICON_PATH / '{}.png'.format(skill['skillIcon']))
        skill_img_new = skill_img.resize(
            (50, 50), Image.Resampling.LANCZOS  # type: ignore
        ).convert("RGBA")
        img.paste(skill_img_new, (78, 756 + 101 * skill_num), skill_img_new)

    # 武器部分
    weapon_img = Image.open(TEXT_PATH / 'char_info_weapon.png')
    weapon_star_img = get_star_png(raw_data['weaponInfo']['weaponStar'])
    weaponName = raw_data['weaponInfo']['weaponName']

    weaponAtk = raw_data['weaponInfo']['weaponStats'][0]['statValue']
    weaponLevel = raw_data['weaponInfo']['weaponLevel']
    weaponAffix = raw_data['weaponInfo']['weaponAffix']
    weaponEffect = raw_data['weaponInfo']['weaponEffect']
    weapon_type = raw_data['weaponInfo']['weaponType']

    weapon_img.paste(weapon_star_img, (25, 235), weapon_star_img)
    weapon_text = ImageDraw.Draw(weapon_img)
    weapon_text.text(
        (35, 80),
        weaponName,
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='lm',
    )
    weapon_text.text(
        (35, 120),
        weapon_type,
        (255, 255, 255),
        genshin_font_origin(20),
        anchor='lm',
    )
    weapon_text.text(
        (35, 160),
        '基础攻击力',
        (255, 255, 255),
        genshin_font_origin(32),
        anchor='lm',
    )
    weapon_text.text(
        (368, 160),
        str(weaponAtk),
        (255, 255, 255),
        genshin_font_origin(32),
        anchor='rm',
    )
    if len(raw_data['weaponInfo']['weaponStats']) == 2:
        weapon_sub_info = raw_data['weaponInfo']['weaponStats'][1]['statName']
        weapon_sub_value = raw_data['weaponInfo']['weaponStats'][1][
            'statValue'
        ]
        weapon_text.text(
            (35, 211),
            weapon_sub_info,
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='lm',
        )
        weapon_text.text(
            (368, 211),
            str(weapon_sub_value),
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='rm',
        )
    else:
        weapon_text.text(
            (35, 211),
            '该武器无副词条',
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='lm',
        )
    weapon_text.text(
        (73, 303),
        f'Lv.{weaponLevel}',
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='mm',
    )
    weapon_text.text(
        (130, 305),
        f'精炼{str(weaponAffix)}阶',
        (255, 239, 173),
        genshin_font_origin(28),
        anchor='lm',
    )

    weaponEffect = strLenth(weaponEffect, 25, 455)
    weapon_text.text(
        (25, 335), weaponEffect, (255, 255, 255), genshin_font_origin(25)
    )
    img.paste(weapon_img, (387, 590), weapon_img)

    fight_prop = raw_data['avatarFightProp']
    hp = fight_prop['hp']
    baseHp = fight_prop['baseHp']
    attack = fight_prop['atk']
    baseAtk = fight_prop['baseAtk']
    defense = fight_prop['def']
    baseDef = fight_prop['baseDef']
    em = fight_prop['elementalMastery']
    critrate = fight_prop['critRate']
    critdmg = fight_prop['critDmg']
    ce = fight_prop['energyRecharge']
    dmgBonus = (
        fight_prop['dmgBonus']
        if fight_prop['physicalDmgBonus'] <= fight_prop['dmgBonus']
        else fight_prop['physicalDmgBonus']
    )

    hp_green = fight_prop['addHp']
    attack_green = fight_prop['addAtk']
    defense_green = fight_prop['addDef']

    # 圣遗物部分
    artifactsAllScore = 0
    for aritifact in raw_data['equipList']:
        artifacts_img = Image.open(TEXT_PATH / 'char_info_artifacts.png')
        artifacts_piece_img = Image.open(
            REL_PATH / '{}.png'.format(aritifact['aritifactName'])
        )
        artifacts_piece_new_img = artifacts_piece_img.resize(
            (75, 75), Image.Resampling.LANCZOS  # type: ignore
        ).convert("RGBA")
        # artifacts_piece_new_img.putalpha(
        # artifacts_piece_new_img.getchannel('A').point(
        #     lambda x: round(x * 0.5) if x > 0 else 0
        # )

        artifacts_img.paste(
            artifacts_piece_new_img, (195, 35), artifacts_piece_new_img
        )
        aritifactStar_img = get_star_png(aritifact['aritifactStar'])
        artifactsPos = aritifact['aritifactPieceName']

        artifacts_img.paste(aritifactStar_img, (20, 165), aritifactStar_img)
        artifacts_text = ImageDraw.Draw(artifacts_img)
        artifacts_text.text(
            (30, 66),
            aritifact['aritifactName'][:4],
            (255, 255, 255),
            genshin_font_origin(34),
            anchor='lm',
        )
        artifacts_text.text(
            (30, 102),
            artifactsPos,
            (255, 255, 255),
            genshin_font_origin(20),
            anchor='lm',
        )

        mainValue = aritifact['reliquaryMainstat']['statValue']
        mainName = aritifact['reliquaryMainstat']['statName']
        mainLevel = aritifact['aritifactLevel']

        if mainName in ['攻击力', '血量', '防御力', '元素精通']:
            mainValueStr = str(mainValue)
        else:
            mainValueStr = str(mainValue) + '%'

        mainNameNew = (
            mainName.replace('百分比', '')
            .replace('伤害加成', '伤加成')
            .replace('元素', '')
            .replace('理', '')
        )

        artifacts_text.text(
            (30, 141),
            mainNameNew,
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='lm',
        )
        artifacts_text.text(
            (263, 141),
            mainValueStr,
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        artifacts_text.text(
            (55, 219),
            '+{}'.format(str(mainLevel)),
            (255, 255, 255),
            genshin_font_origin(24),
            anchor='mm',
        )

        artifactsScore = 0
        for index, i in enumerate(aritifact['reliquarySubstats']):
            subName = i['statName']
            subValue = i['statValue']
            if subName in ['攻击力', '血量', '防御力', '元素精通']:
                subValueStr = str(subValue)
            else:
                subValueStr = str(subValue) + '%'
            # artifactsScore += await get_artifacts_score(subName, subValue)
            value_temp = await get_artifacts_value(
                subName, subValue, baseAtk, baseHp, baseDef, char_name
            )
            artifactsScore += value_temp
            subNameStr = subName.replace('百分比', '').replace('元素', '')
            if value_temp == 0:
                artifacts_color = (160, 160, 160)
            elif value_temp >= 4.5:
                artifacts_color = (247, 50, 50)
            else:
                artifacts_color = (255, 255, 100)
            artifacts_text.text(
                (20, 256 + index * 33),
                '·{}'.format(subNameStr),
                artifacts_color,
                genshin_font_origin(25),
                anchor='lm',
            )
            artifacts_text.text(
                (268, 256 + index * 33),
                '{}'.format(subValueStr),
                artifacts_color,
                genshin_font_origin(25),
                anchor='rm',
            )
        if artifactsScore >= 6:
            artifactsScore_color = (247, 26, 26)
        else:
            artifactsScore_color = (255, 255, 255)
        artifactsAllScore += artifactsScore
        artifacts_text.text(
            (268, 190),
            '{:.2f}'.format(artifactsScore) + '条',
            artifactsScore_color,
            genshin_font_origin(23),
            anchor='rm',
        )

        if artifactsPos == '生之花':
            img.paste(artifacts_img, (18, 1075), artifacts_img)
        elif artifactsPos == '死之羽':
            img.paste(artifacts_img, (318, 1075), artifacts_img)
        elif artifactsPos == '时之沙':
            img.paste(artifacts_img, (618, 1075), artifacts_img)
        elif artifactsPos == '空之杯':
            img.paste(artifacts_img, (18, 1447), artifacts_img)
        elif artifactsPos == '理之冠':
            img.paste(artifacts_img, (318, 1447), artifacts_img)

    # 角色基本信息
    img_text = ImageDraw.Draw(img)
    img_text.text(
        (411, 72),
        char_name,
        (255, 255, 255),
        genshin_font_origin(55),
        anchor='lm',
    )
    img_text.text(
        (411, 122),
        '等级{}'.format(char_level),
        (255, 255, 255),
        genshin_font_origin(40),
        anchor='lm',
    )
    img_text.text(
        (747, 126),
        str(char_fetter),
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='lm',
    )

    # aeq
    # img_text.text(
    #     (110, 771),
    #     a_skill_name,
    #     (255, 255, 255),
    #     genshin_font_origin(26),
    #     anchor='lm',
    # )
    img_text.text(
        (103, 812),
        f'{str(a_skill_level)}',
        (255, 255, 255),
        genshin_font_origin(30),
        anchor='mm',
    )

    # img_text.text(
    #     (110, 872),
    #     e_skill_name,
    #     (255, 255, 255),
    #     genshin_font_origin(26),
    #     anchor='lm',
    # )
    img_text.text(
        (103, 915),
        f'{str(e_skill_level)}',
        (255, 255, 255),
        genshin_font_origin(30),
        anchor='mm',
    )

    # img_text.text(
    #     (110, 973),
    #     q_skill_name,
    #     (255, 255, 255),
    #     genshin_font_origin(26),
    #     anchor='lm',
    # )
    img_text.text(
        (103, 1016),
        f'{str(q_skill_level)}',
        (255, 255, 255),
        genshin_font_origin(30),
        anchor='mm',
    )

    # 属性
    img_text.text(
        (785, 174),
        str(round(hp)),
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 227),
        str(round(attack)),
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 280),
        str(round(defense)),
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 333),
        str(round(em)),
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 386),
        f'{str(round(critrate * 100, 2))}%',
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 439),
        f'{str(round(critdmg * 100, 2))}%',
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 492),
        f'{str(round(ce * 100, 1))}%',
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )
    img_text.text(
        (785, 545),
        f'{str(round(dmgBonus * 100, 1))}%',
        (255, 255, 255),
        genshin_font_origin(28),
        anchor='rm',
    )

    img_text.text(
        (805, 174),
        f'(+{str(round(hp_green))})',
        (95, 251, 80),
        genshin_font_origin(28),
        anchor='lm',
    )
    img_text.text(
        (805, 227),
        f'(+{str(round(attack_green))})',
        (95, 251, 80),
        genshin_font_origin(28),
        anchor='lm',
    )
    img_text.text(
        (805, 280),
        f'(+{str(round(defense_green))})',
        (95, 251, 80),
        genshin_font_origin(28),
        anchor='lm',
    )

    uid = raw_data['playerUid']
    data_time = raw_data['dataTime']
    # uid
    img_text.text(
        (350, 1035),
        f'UID{uid}',
        (255, 255, 255),
        genshin_font_origin(24),
        anchor='rm',
    )

    # 数据最后更新时间
    img_text.text(
        (780, 600),
        f'数据最后更新于{data_time}',
        (255, 255, 255),
        genshin_font_origin(22),
        anchor='rm',
    )

    # 角色评分
    img_text.text(
        (768, 1557),
        f'{round(artifactsAllScore, 1)}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )
    percent = await get_char_percent(raw_data, new_prop, char_name)
    img_text.text(
        (768, 1690),
        f'{str(percent)+"%"}',
        (255, 255, 255),
        genshin_font_origin(50),
        anchor='mm',
    )

    img = img.convert('RGB')
    result_buffer = BytesIO()
    img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    res = result_buffer.getvalue()
    return res


async def draw_single_card(
    img: Image.Image,
    char: dict,
    index: int,
    color: Tuple[int, int, int],
    x_limit: int,
    char_card_mask: Image.Image,
    char_card_1: Image.Image,
    img_card: Image.Image,
):

    size_36 = genshin_font_origin(36)
    size_46 = genshin_font_origin(46)

    overlay = Image.open(TEXT_PATH / 'overlay.png')
    color_img = Image.new(
        'RGBA', overlay.size, COLOR_MAP[char['avatarElement']]
    )
    img_base = ImageChops.overlay(color_img, overlay)
    char_img_raw = Image.open(CHAR_STAND_PATH / f'{char["id"]}.png')
    char_img = char_img_raw.resize(
        (round(char_img_raw.size[0] * 0.5), round(char_img_raw.size[1] * 0.5))
    ).convert('RGBA')

    offset_x, offset_y = 0, 0
    if char['char_name'] == '八重神子':
        offset_x = -100
    elif char['char_name'] == '早柚':
        offset_x = 50

    img_base.paste(char_img, (-380 + offset_x, 200 + offset_y), char_img)
    img_card.paste(img_base, (-25, -260), char_card_mask)
    img_card = Image.alpha_composite(img_card, char_card_1)
    # img_card.paste(img_card, (0, 0), img_card)

    char_card_text = ImageDraw.Draw(img_card)

    char_card_text.text(
        (448, 59.2),
        f'{str(round(char["critrate"] * 100, 2))}%',
        color,
        size_36,
        anchor='lm',
    )
    char_card_text.text(
        (448, 122.2),
        f'{str(round(char["critdmg"] * 100, 2))}%',
        color,
        size_36,
        anchor='lm',
    )

    char_card_text.text(
        (410.9, 252.6), str(char['a_skill_level']), color, size_36, anchor='mm'
    )
    char_card_text.text(
        (485, 252.6), str(char['e_skill_level']), color, size_36, anchor='mm'
    )
    char_card_text.text(
        (558, 252.6), str(char['q_skill_level']), color, size_36, anchor='mm'
    )

    if float(char['percent']) >= 100:
        percent_color = (204, 57, 78)
    else:
        percent_color = color

    if char['value'] >= 28.5:
        value_color = (204, 57, 78)
    else:
        value_color = color

    char_card_text.text(
        (742, 253.1),
        str(char['percent']) + '%',
        percent_color,
        size_46,
        anchor='mm',
    )
    char_card_text.text(
        (742, 113.1),
        str(char['value']) + '条',
        value_color,
        size_46,
        anchor='mm',
    )

    char_card_text.text(
        (21.2, 70.5),
        f'{str(char["talent_num"])}命',
        color,
        size_36,
        anchor='lm',
    )
    char_card_text.text(
        (21.2, 129.8),
        f'{str(char["weapon_affix"])}精',
        color,
        size_36,
        anchor='lm',
    )

    img.paste(
        img_card, ((index % x_limit) * 900, (index // x_limit) * 300), img_card
    )


async def draw_cahrcard_list(uid: str, limit: int = 24) -> Union[str, bytes]:
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
    with open(DMG_PATH / 'char_action.json', "r", encoding='UTF-8') as f:
        char_action = json.load(f)
    for char_name in char_list:
        temp = {}
        with open(uid_fold / f'{char_name}.json', 'r', encoding='UTF-8') as f:
            raw_data = json.load(f)

        fight_prop = raw_data['avatarFightProp']
        skillList = raw_data['avatarSkill']

        temp['char_name'] = char_name
        temp['id'] = raw_data['avatarId']
        temp['avatarEnName'] = raw_data['avatarEnName']
        temp['avatarElement'] = raw_data['avatarElement']
        # 拿到倍率表
        power_list = char_action[char_name]
        new_prop = await calc_prop(raw_data, power_list)
        temp['percent'] = await get_char_percent(raw_data, new_prop, char_name)
        temp['critrate'] = fight_prop['critRate']
        temp['critdmg'] = fight_prop['critDmg']
        baseHp = fight_prop['baseHp']
        baseAtk = fight_prop['baseAtk']
        baseDef = fight_prop['baseDef']
        temp['value'] = await get_all_artifacts_value(
            raw_data['equipList'], baseHp, baseAtk, baseDef, char_name
        )
        temp['value'] = float('{:.2f}'.format(temp['value']))
        temp['avatarElement'] = raw_data['avatarElement']
        temp['a_skill_level'] = skillList[0]['skillLevel']
        temp['e_skill_level'] = skillList[1]['skillLevel']
        temp['q_skill_level'] = skillList[-1]['skillLevel']
        temp['talent_num'] = len(raw_data['talentList'])
        temp['weapon_affix'] = raw_data['weaponInfo']['weaponAffix']
        char_done_list.append(temp)

    # 排序
    char_done_list.sort(key=lambda x: (-float(x['percent'])))
    char_done_list = char_done_list[:limit]

    char_card_1 = Image.open(TEXT_PATH / 'charcard_1.png')
    char_card_mask = Image.open(TEXT_PATH / 'charcard_mask.png')

    x_limit = 2
    color = (255, 255, 255)
    x_tile = (len(char_done_list) + x_limit - 1) // x_limit
    y_tile = math.ceil(len(char_done_list) / x_tile)
    x_tile, y_tile = (
        x_tile if x_tile <= y_tile else y_tile,
        y_tile if y_tile >= x_tile else x_tile,
    )

    img = Image.new('RGBA', (900 * x_tile, 300 * y_tile), (0, 0, 0))
    img_card = Image.new('RGBA', (900, 300))

    tasks = []
    for index, char in enumerate(char_done_list):
        tasks.append(
            draw_single_card(
                img,
                char,
                index,
                color,
                x_limit,
                char_card_mask,
                char_card_1,
                img_card,
            )
        )
    await asyncio.wait(tasks)

    res = await convert_img(img)
    return res
