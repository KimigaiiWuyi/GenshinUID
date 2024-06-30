import math
import random
from io import BytesIO
from typing import Dict, Optional

import aiofiles
from httpx import get
from PIL import Image, ImageDraw, ImageChops

from .mono.Character import Character
from ..genshinuid_config.gs_config import gsconfig
from .etc.MAP_PATH import COLOR_MAP, avatarName2SkillAdd
from .etc.etc import TEXT_PATH, strLenth, get_artifacts_value
from ..utils.image.image_tools import (
    CustomizeImage,
    get_star_png,
    get_weapon_affix_pic,
)
from ..utils.resource.RESOURCE_PATH import (
    REL_PATH,
    ICON_PATH,
    CU_CHBG_PATH,
    GACHA_IMG_PATH,
    CHAR_STAND_PATH,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_15,
    gs_font_18,
    gs_font_20,
    gs_font_22,
    gs_font_24,
    gs_font_25,
    gs_font_28,
    gs_font_32,
    gs_font_40,
    gs_font_50,
    gs_font_55,
)

ARTIFACTS_POS = {
    '生之花': (13, 1087),
    '死之羽': (323, 1087),
    '时之沙': (633, 1087),
    '空之杯': (13, 1447),
    '理之冠': (323, 1447),
}
PIC_API = gsconfig.get_config('random_pic_API').data


async def get_char_card_base(char: Character) -> Image.Image:
    card_prop = char.card_prop
    char_info_1 = Image.open(TEXT_PATH / 'char_info_1.png')
    # 命座处理
    lock_img = Image.open(TEXT_PATH / 'icon_lock.png')
    # holo_img = Image.open(TEXT_PATH / 'holo.png')
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
                (50, 50), Image.Resampling.LANCZOS
            ).convert("RGBA")
            for _ in range(2):
                char_info_1.paste(
                    talent_img_new,
                    (850, 375 + talent_num * 81),
                    talent_img_new,
                )
        else:
            char_info_1.paste(lock_img, (850, 375 + talent_num * 81), lock_img)

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

    for skill_num, skill in enumerate(skillList[0:2] + [skillList[-1]]):
        skill_img = Image.open(ICON_PATH / '{}.png'.format(skill['skillIcon']))
        skill_img_new = skill_img.resize(
            (50, 50), Image.Resampling.LANCZOS
        ).convert("RGBA")
        char_info_1.paste(
            skill_img_new, (78, 756 + 101 * skill_num), skill_img_new
        )

    # 武器部分
    char_info_text = ImageDraw.Draw(char_info_1)
    weapon_star_img = get_star_png(card_prop['weaponInfo']['weaponStar'])
    weaponName = card_prop['weaponInfo']['weaponName']

    weaponAtk = card_prop['weaponInfo']['weaponStats'][0]['statValue']
    weaponLevel = card_prop['weaponInfo']['weaponLevel']
    weaponAffix = card_prop['weaponInfo']['weaponAffix']
    weaponEffect = card_prop['weaponInfo']['weaponEffect']
    weapon_type = card_prop['weaponInfo']['weaponType']

    char_info_1.paste(weapon_star_img, (402, 825), weapon_star_img)
    char_info_text.text(
        (412, 670),
        weaponName,
        (255, 255, 255),
        gs_font_50,
        anchor='lm',
    )
    char_info_text.text(
        (420, 710),
        weapon_type,
        (255, 255, 255),
        gs_font_20,
        anchor='lm',
    )
    char_info_text.text(
        (420, 750),
        '基础攻击力',
        (255, 255, 255),
        gs_font_32,
        anchor='lm',
    )
    char_info_text.text(
        (755, 750),
        str(weaponAtk),
        (255, 255, 255),
        gs_font_32,
        anchor='rm',
    )
    if len(card_prop['weaponInfo']['weaponStats']) == 2:
        weapon_sub_info = card_prop['weaponInfo']['weaponStats'][1]['statName']
        weapon_sub_value = card_prop['weaponInfo']['weaponStats'][1][
            'statValue'
        ]
        char_info_text.text(
            (420, 801),
            weapon_sub_info,
            (255, 255, 255),
            gs_font_32,
            anchor='lm',
        )
        char_info_text.text(
            (755, 801),
            str(weapon_sub_value),
            (255, 255, 255),
            gs_font_32,
            anchor='rm',
        )
    else:
        char_info_text.text(
            (420, 801),
            '该武器无副词条',
            (255, 255, 255),
            gs_font_32,
            anchor='lm',
        )
    char_info_text.text(
        (460, 893),
        f'Lv.{weaponLevel}',
        (255, 255, 255),
        gs_font_28,
        anchor='mm',
    )
    affix_pic = await get_weapon_affix_pic(weaponAffix)
    char_info_1.paste(affix_pic, (420 + len(weaponName) * 50, 660), affix_pic)
    '''
    char_info_text.text(
        (517, 895),
        f'精炼{str(weaponAffix)}阶',
        (255, 239, 173),
        gs_font_28,
        anchor='lm',
    )
    '''

    weaponEffect = strLenth(weaponEffect, 25, 455)
    weaponEffect = '\n'.join(weaponEffect.split('\n')[:5])
    char_info_text.text((412, 925), weaponEffect, (255, 255, 255), gs_font_25)

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

    hp_green = fight_prop['hp'] - fight_prop['baseHp']
    attack_green = fight_prop['atk'] - fight_prop['baseAtk']
    defense_green = fight_prop['def'] - fight_prop['baseDef']
    # 角色基本信息
    char_info_text.text(
        (411, 72),
        char.char_name,
        (255, 255, 255),
        gs_font_55,
        anchor='lm',
    )
    char_info_text.text(
        (411, 122),
        '等级{}'.format(char.char_level),
        (255, 255, 255),
        gs_font_40,
        anchor='lm',
    )
    char_info_text.text(
        (747, 126),
        str(char.char_fetter),
        (255, 255, 255),
        gs_font_28,
        anchor='lm',
    )
    char_info_text.text(
        (103, 820),
        f'{a_skill_level}',
        (255, 255, 255),
        gs_font_22,
        anchor='mm',
    )
    char_info_text.text(
        (103, 923),
        f'{e_skill_level}',
        (255, 255, 255),
        gs_font_22,
        anchor='mm',
    )

    char_info_text.text(
        (103, 1024),
        f'{q_skill_level}',
        (255, 255, 255),
        gs_font_22,
        anchor='mm',
    )

    # 属性
    char_info_text.text(
        (785, 174),
        str(round(hp)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 227),
        str(round(attack)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 280),
        str(round(defense)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 333),
        str(round(em)),
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 386),
        f'{str(round(critrate * 100, 2))}%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 439),
        f'{str(round(critdmg * 100, 2))}%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 492),
        f'{str(round(ce * 100, 1))}%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    char_info_text.text(
        (785, 545),
        f'{str(round(dmgBonus * 100, 1))}%',
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )

    char_info_text.text(
        (805, 174),
        f'(+{str(round(hp_green))})',
        (95, 251, 80),
        gs_font_28,
        anchor='lm',
    )
    char_info_text.text(
        (805, 227),
        f'(+{str(round(attack_green))})',
        (95, 251, 80),
        gs_font_28,
        anchor='lm',
    )
    char_info_text.text(
        (805, 280),
        f'(+{str(round(defense_green))})',
        (95, 251, 80),
        gs_font_28,
        anchor='lm',
    )

    uid = card_prop['playerUid']
    data_time = card_prop['dataTime']
    # uid
    char_info_text.text(
        (350, 1035),
        f'UID{uid}',
        (255, 255, 255),
        gs_font_24,
        anchor='rm',
    )
    # 数据最后更新时间
    char_info_text.text(
        (780, 600),
        f'数据最后更新于{data_time}',
        (255, 255, 255),
        gs_font_22,
        anchor='rm',
    )
    return char_info_1


async def get_bg_card(
    char_element: str, ex_len: int, char_img: Image.Image
) -> Image.Image:
    img_w, img_h = 950, 1085 + ex_len
    overlay = Image.open(TEXT_PATH / 'overlay.png')
    overlay_w, overlay_h = overlay.size
    if overlay_h < img_h:
        new_overlay_h = img_h
        new_overlay_w = math.ceil(new_overlay_h * overlay_w / overlay_h)
        overlay = overlay.resize(
            (new_overlay_w, new_overlay_h), Image.Resampling.LANCZOS
        )
        overlay = overlay.crop((0, 0, img_w, img_h))
    elif overlay_h > img_h:
        new_overlay_w = img_w
        new_overlay_h = math.ceil(overlay_w / new_overlay_w * overlay_h)
        overlay = overlay.resize(
            (new_overlay_w, new_overlay_h), Image.Resampling.LANCZOS
        )
        overlay = overlay.crop((0, 0, img_w, img_h))
    if (
        gsconfig.get_config('ColorBG').data
        and gsconfig.get_config('RandomPic').data
    ):
        bg_color = CustomizeImage.get_bg_color(char_img)
    else:
        bg_color = COLOR_MAP[char_element]
    color_img = Image.new('RGBA', overlay.size, bg_color)
    return ImageChops.overlay(color_img, overlay)


async def get_char_img(
    char: Character, char_url: Optional[str] = None
) -> Image.Image:
    char_name = char.char_name
    if gsconfig.get_config('RandomPic').data and char_url is None:
        if char_name == '旅行者':
            char_name_url = '荧'
        else:
            char_name_url = char_name
        chbg_path = CU_CHBG_PATH / char_name_url
        char_url = f'{PIC_API}{char_name_url}'
        if chbg_path.exists():
            cuch_img = random.choice(list(chbg_path.iterdir()))
            async with aiofiles.open(cuch_img, 'rb') as f:
                char.char_bytes = await f.read()
        else:
            char_data = get(char_url, follow_redirects=True)
            if 'application/json' in char_data.headers['Content-Type']:
                char_url = None
            else:
                char.char_bytes = char_data.content

    based_w, based_h = 600, 1200
    if char_url:
        offset_x, offset_y = 200, 0
        if char.char_bytes is None:
            char.char_bytes = get(char_url).content
        char_img = Image.open(BytesIO(char.char_bytes)).convert('RGBA')
    else:
        offset_x, offset_y = 200, 0
        if char_name == '旅行者':
            char_img = (
                Image.open(CHAR_STAND_PATH / '10000007.png')
                .convert('RGBA')
                .resize((1421, 800))
            )
        else:
            char_img = Image.open(
                GACHA_IMG_PATH / f'{char_name}.png'
            )  # 角色图像
    # 确定图片的长宽
    w, h = char_img.size
    if (w, h) != (based_w, based_h):
        based_new_w, based_new_h = based_w + offset_x, based_h + offset_y
        based_scale = '%.3f' % (based_new_w / based_new_h)
        scale_f = '%.3f' % (w / h)
        new_w = math.ceil(based_new_h * float(scale_f))
        new_h = math.ceil(based_new_w / float(scale_f))
        if scale_f > based_scale:
            bg_img2 = char_img.resize(
                (new_w, based_new_h), Image.Resampling.LANCZOS
            )
            x1 = new_w / 2 - based_new_w / 2 + offset_x
            y1 = 0 + offset_y / 2
            x2 = new_w / 2 + based_new_w / 2
            y2 = based_new_h - offset_y / 2
        else:
            bg_img2 = char_img.resize(
                (based_new_w, new_h), Image.Resampling.LANCZOS
            )
            x1 = 0 + offset_x
            y1 = new_h / 2 - based_new_h / 2 + offset_y / 2
            x2 = based_new_w
            y2 = new_h / 2 + based_new_h / 2 - offset_y / 2
        char_img = bg_img2.crop((x1, y1, x2, y2))  # type: ignore

    char_info_mask = Image.open(TEXT_PATH / 'char_info_mask.png')
    char_result = Image.new('RGBA', (based_w, based_h), (0, 0, 0, 0))
    char_result.paste(char_img, (0, 0), char_info_mask)
    return char_result


async def _get_single_artifact_img(aritifact: Dict) -> Image.Image:
    '''
    注意这里的aritifact不是原始的数据, 是带了评分的数据
    '''
    artifactimg_bg = Image.open(TEXT_PATH / 'char_info_artifacts_bg.png')
    artifacts_img = Image.open(TEXT_PATH / 'char_info_artifacts.png')
    artifacts_piece_img = Image.open(
        REL_PATH / '{}.png'.format(aritifact['aritifactName'])
    )
    artifacts_piece_new_img = artifacts_piece_img.resize(
        (90, 90), Image.Resampling.LANCZOS
    ).convert('RGBA')

    artifacts_img.paste(
        artifacts_piece_new_img, (26, 32), artifacts_piece_new_img
    )
    aritifactStar_img = get_star_png(aritifact['aritifactStar'])
    aritifactStar_img = aritifactStar_img.resize((90, 23))

    # 圣遗物星星和名称&位置
    artifacts_img.paste(aritifactStar_img, (121, 63), aritifactStar_img)
    artifacts_text = ImageDraw.Draw(artifacts_img)
    if len(aritifact['aritifactName']) <= 8:
        main_name = aritifact['aritifactName']
    else:
        main_name = (
            aritifact['aritifactName'][:4] + aritifact['aritifactName'][4:]
        )
    artifacts_text.text(
        (124, 51),
        main_name,
        (255, 255, 255),
        gs_font_22,
        anchor='lm',
    )
    '''
    artifacts_text.text(
        (30, 102),
        artifactsPos,
        (255, 255, 255),
        gs_font_20,
        anchor='lm',
    )
    '''

    mainValue: float = aritifact['reliquaryMainstat']['statValue']
    mainName: str = aritifact['reliquaryMainstat']['statName']
    mainLevel: int = aritifact['aritifactLevel']

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
        (38, 150),
        mainNameNew,
        (255, 255, 255),
        gs_font_28,
        anchor='lm',
    )
    artifacts_text.text(
        (271, 150),
        mainValueStr,
        (255, 255, 255),
        gs_font_28,
        anchor='rm',
    )
    artifacts_text.text(
        (232, 75),
        f'+{mainLevel}',
        (255, 255, 255),
        gs_font_15,
        anchor='mm',
    )

    for index, i in enumerate(aritifact['reliquarySubstats']):
        subName: str = i['statName']
        subValue: float = i['statValue']
        if subName in ['攻击力', '血量', '防御力', '元素精通']:
            subValueStr = str(subValue)
        else:
            subValueStr = str(subValue) + '%'
        value_temp = i['value_score']
        subNameStr = subName.replace('百分比', '').replace('元素', '')
        # 副词条文字颜色
        if value_temp == 0:
            artifacts_color = (120, 120, 120)
        else:
            artifacts_color = (255, 255, 255)

        # 副词条底色
        if value_temp >= 3.4:
            artifacts_bg = (205, 135, 76)
            if value_temp >= 4.5:
                artifacts_bg = (158, 39, 39)
            artifacts_text.rounded_rectangle(
                (25, 184 + index * 35, 283, 213 + index * 35),
                fill=artifacts_bg,
                radius=8,
            )

        artifacts_text.text(
            (22, 200 + index * 35),
            '·{}'.format(subNameStr),
            artifacts_color,
            gs_font_25,
            anchor='lm',
        )
        artifacts_text.text(
            (266, 200 + index * 35),
            '{}'.format(subValueStr),
            artifacts_color,
            gs_font_25,
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

    artifacts_text.rounded_rectangle(
        (121, 99, 193, 119), fill=artifactsScore_color, radius=8
    )
    artifacts_text.rounded_rectangle(
        (200, 99, 272, 119), fill=cv_color, radius=8
    )

    artifacts_text.text(
        (156, 109),
        '{:.2f}'.format(artifactsScore) + '条',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )

    artifacts_text.text(
        (235, 109),
        '{:.1f}'.format(cv_score) + '分',
        (255, 255, 255),
        gs_font_18,
        anchor='mm',
    )

    artifactimg_bg.paste(artifacts_img, (0, 0), artifacts_img)
    return artifactimg_bg


async def get_artifact_score_data(
    aritifact: Dict,
    char: Optional[Character] = None,
    char_name: Optional[str] = None,
) -> Dict:
    all_value_score = 0
    all_cv_score = 0
    for i in aritifact['reliquarySubstats']:
        subName: str = i['statName']
        subValue: float = i['statValue']
        if char is not None and not hasattr(char, 'baseAtk'):
            await char.new()
        cv_score = 0

        if subName == '暴击率':
            cv_score += subValue * 2
        elif subName == '暴击伤害':
            cv_score += subValue

        if char is None:
            _atk = 750
            _hp = 12000
            _def = 700
            if char_name is None:
                return {}
            _char_name = char_name
        else:
            _atk = char.baseAtk
            _hp = char.baseHp
            _def = char.baseDef
            _char_name = char.char_name

        value_temp = await get_artifacts_value(
            subName,
            subValue,
            _atk,
            _hp,
            _def,
            _char_name,
        )

        i['value_score'] = value_temp
        i['cv_score'] = cv_score

        all_cv_score += cv_score
        all_value_score += value_temp

    aritifact['cv_score'] = all_cv_score
    aritifact['value_score'] = all_value_score

    return aritifact


async def get_single_artifact_img(
    aritifact: Dict, char: Character
) -> Image.Image:
    new_aritifact = await get_artifact_score_data(aritifact, char)
    img = await _get_single_artifact_img(new_aritifact)
    for i in aritifact['reliquarySubstats']:
        char.artifacts_all_score += i['value_score']
    return img


async def get_artifacts_card(char: Character, img: Image.Image):
    card_prop = char.card_prop
    # 圣遗物部分
    for aritifact in card_prop['equipList']:
        artifactsPos = aritifact['aritifactPieceName']
        artifacts_img = await get_single_artifact_img(aritifact, char)
        img.paste(artifacts_img, ARTIFACTS_POS[artifactsPos], artifacts_img)
