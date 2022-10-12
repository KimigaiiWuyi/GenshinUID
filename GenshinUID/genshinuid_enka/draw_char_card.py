import json
import math
from io import BytesIO
from pathlib import Path
from typing import Tuple, Union, Optional

from httpx import get
from PIL import Image, ImageDraw, ImageChops

from .propCalc.prop_calc import get_card_prop
from .curveCalc.curve_calc import draw_char_curve_data
from ..utils.db_operation.db_operation import config_check
from ..utils.draw_image_tools.draw_image_tool import CustomizeImage
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

ARTIFACTS_POS = {
    '生之花': (18, 1075),
    '死之羽': (318, 1075),
    '时之沙': (618, 1075),
    '空之杯': (18, 1447),
    '理之冠': (318, 1447),
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


class CharCard:
    def __init__(
        self,
        raw_data: dict,
        char_url: Optional[str] = None,
    ):
        self.raw_data = raw_data
        self.new_prop = {}
        self.char_name = self.raw_data['avatarName']
        self.char_level = self.raw_data['avatarLevel']
        self.char_fetter = self.raw_data['avatarFetter']
        self.baseHp: int = 0
        self.baseAtk: int = 0
        self.baseDef: int = 0
        self.char_bytes = None
        self.char_url = char_url
        self.artifacts_all_score = 0
        self.percent = ''
        self.seq_str = ''
        self.power_list = {}

    async def new(
        self,
        weapon: Optional[str] = None,
        weapon_affix: Optional[int] = None,
        talent_num: Optional[int] = None,
    ):
        if not await config_check('OldPanle'):
            self.raw_data = await get_card_prop(
                self.raw_data, weapon, weapon_affix, talent_num
            )
        if self.raw_data == {}:
            return '要替换的武器不正确或发生了未知错误~'
        self.baseHp = self.raw_data['avatarFightProp']['baseHp']
        self.baseAtk = self.raw_data['avatarFightProp']['baseAtk']
        self.baseDef = self.raw_data['avatarFightProp']['baseDef']
        self.char_name = self.raw_data['avatarName']

    async def get_char_img(self) -> Image.Image:
        if await config_check('RandomPic') and self.char_url is None:
            if self.char_name == '旅行者':
                char_name_url = '荧'
            else:
                char_name_url = self.char_name
            self.char_url = (
                f'http://img.genshin.cherishmoon.fun/{char_name_url}'
            )
            char_data = get(self.char_url, follow_redirects=True)
            if char_data.headers['Content-Type'] == 'application/json':
                self.char_url = None
            else:
                self.char_bytes = char_data.content

        based_w, based_h = 600, 1200
        if self.char_url:
            offset_x, offset_y = 200, 0
            if self.char_bytes is None:
                self.char_bytes = get(self.char_url).content
            char_img = Image.open(BytesIO(self.char_bytes)).convert('RGBA')
        else:
            if self.char_name in avatarOffsetMap:
                offset_x, offset_y = (
                    avatarOffsetMap[self.char_name][0],
                    avatarOffsetMap[self.char_name][1],
                )
            else:
                offset_x, offset_y = 200, 0
            if self.char_name == '旅行者':
                char_img = (
                    Image.open(
                        CHAR_STAND_PATH / f'{self.raw_data["avatarId"]}.png'
                    )
                    .convert('RGBA')
                    .resize((1421, 800))
                )
            else:
                char_img = Image.open(
                    GACHA_IMG_PATH / f'{self.char_name}.png'
                )  # 角色图像
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

        char_info_mask = Image.open(TEXT_PATH / 'char_info_mask.png')
        img_temp = Image.new('RGBA', (based_w, based_h), (0, 0, 0, 0))
        img_temp.paste(char_img, (0, 0), char_info_mask)
        char_img = img_temp
        return char_img

    async def get_bg_card(
        self, ex_len: int, char_img: Image.Image
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
        if await config_check('ColorBG'):
            bg_color = CustomizeImage.get_bg_color(char_img)
        else:
            bg_color = COLOR_MAP[self.raw_data['avatarElement']]
        color_img = Image.new('RGBA', overlay.size, bg_color)
        return ImageChops.overlay(color_img, overlay)

    async def get_new_prop(self):
        with open(DMG_PATH / 'char_action.json', "r", encoding='UTF-8') as f:
            char_action = json.load(f)
        # 拿到倍率表
        if self.char_name not in char_action:
            self.power_list = {}
        else:
            self.power_list = char_action[self.char_name]
            # 额外增加钟离倍率
            if self.char_name == '钟离':
                self.power_list['E总护盾量'] = {
                    'name': 'E总护盾量',
                    'type': '生命值',
                    'plus': 1,
                    'value': [
                        f'{self.power_list["E护盾附加吸收量"]["value"][index]}+{i}'
                        for index, i in enumerate(
                            self.power_list['E护盾基础吸收量']['value']
                        )
                    ],
                }
            elif self.char_name == '赛诺':
                for power_name in ['E渡荒之雷', 'E渡荒之雷(超激化)']:
                    self.power_list[power_name] = {
                        'name': power_name,
                        'type': '攻击力',
                        'plus': 1,
                        'value': ['100%'] * 15,
                    }
        self.new_prop = await calc_prop(self.raw_data, self.power_list)

    async def get_dmg_card(self) -> Tuple[Image.Image, int]:
        await self.get_new_prop()
        # 拿到倍率表
        if self.power_list == {}:
            dmg_img, dmg_len = Image.new('RGBA', (950, 1)), 0
        else:
            dmg_img, dmg_len = await draw_dmgCacl_img(
                self.raw_data, self.power_list, self.new_prop
            )
        return dmg_img, dmg_len

    async def get_artifacts_card(self, img: Image.Image):
        # 圣遗物部分
        for aritifact in self.raw_data['equipList']:
            artifacts_img = Image.open(TEXT_PATH / 'char_info_artifacts.png')
            artifacts_piece_img = Image.open(
                REL_PATH / '{}.png'.format(aritifact['aritifactName'])
            )
            artifacts_piece_new_img = artifacts_piece_img.resize(
                (75, 75), Image.Resampling.LANCZOS
            ).convert("RGBA")

            artifacts_img.paste(
                artifacts_piece_new_img, (195, 35), artifacts_piece_new_img
            )
            aritifactStar_img = get_star_png(aritifact['aritifactStar'])
            artifactsPos = aritifact['aritifactPieceName']

            artifacts_img.paste(
                aritifactStar_img, (20, 165), aritifactStar_img
            )
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
                value_temp = await get_artifacts_value(
                    subName,
                    subValue,
                    self.baseAtk,
                    self.baseHp,
                    self.baseDef,
                    self.char_name,
                )
                artifactsScore += value_temp
                subNameStr = subName.replace('百分比', '').replace('元素', '')
                if value_temp == 0:
                    artifacts_color = (160, 160, 160)
                elif value_temp >= 5.1:
                    artifacts_color = (247, 50, 50)
                elif value_temp >= 3.7:
                    artifacts_color = (255, 255, 100)
                else:
                    artifacts_color = (250, 250, 250)
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
            self.artifacts_all_score += artifactsScore
            artifacts_text.text(
                (268, 190),
                '{:.2f}'.format(artifactsScore) + '条',
                artifactsScore_color,
                genshin_font_origin(23),
                anchor='rm',
            )
            img.paste(
                artifacts_img, ARTIFACTS_POS[artifactsPos], artifacts_img
            )

    async def get_char_card_1(self) -> Image.Image:
        char_info_1 = Image.open(TEXT_PATH / 'char_info_1.png')
        holo_temp = Image.new('RGBA', char_info_1.size, (0, 0, 0, 0))
        # 命座处理
        lock_img = Image.open(TEXT_PATH / 'icon_lock.png')
        holo_img = Image.open(TEXT_PATH / 'holo.png')
        # holo_color = Image.new(
        #    'RGBA', holo_img.size, COLOR_MAP[self.raw_data['avatarElement']]
        # )
        for talent_num in range(0, 6):
            if talent_num + 1 <= len(self.raw_data['talentList']):
                talent = self.raw_data['talentList'][talent_num]
                talent_img = Image.open(
                    ICON_PATH / '{}.png'.format(talent['talentIcon'])
                )
                talent_img_new = talent_img.resize(
                    (50, 50), Image.Resampling.LANCZOS  # type: ignore
                ).convert("RGBA")
                holo_temp.paste(
                    holo_img, (775, 300 + talent_num * 81), holo_img
                )
                holo_temp.paste(
                    talent_img_new,
                    (850, 375 + talent_num * 81),
                    talent_img_new,
                )
            else:
                holo_temp.paste(
                    lock_img, (850, 375 + talent_num * 81), lock_img
                )
        char_info_1 = Image.alpha_composite(char_info_1, holo_temp)

        # 天赋处理
        skillList = self.raw_data['avatarSkill']
        # a_skill_name = skillList[0]['skillName'].replace('普通攻击·', '')
        a_skill_level = skillList[0]['skillLevel']
        # e_skill_name = skillList[1]['skillName']
        e_skill_level = skillList[1]['skillLevel']
        # q_skill_name = skillList[-1]['skillName']
        q_skill_level = skillList[-1]['skillLevel']

        skill_add = avatarName2SkillAdd[self.char_name]
        for skillAdd_index in range(0, 2):
            if len(self.raw_data['talentList']) >= 3 + skillAdd_index * 2:
                if skill_add[skillAdd_index] == 'E':
                    e_skill_level += 3
                elif skill_add[skillAdd_index] == 'Q':
                    q_skill_level += 3

        for skill_num, skill in enumerate(skillList[0:2] + [skillList[-1]]):
            skill_img = Image.open(
                ICON_PATH / '{}.png'.format(skill['skillIcon'])
            )
            skill_img_new = skill_img.resize(
                (50, 50), Image.Resampling.LANCZOS  # type: ignore
            ).convert("RGBA")
            char_info_1.paste(
                skill_img_new, (78, 756 + 101 * skill_num), skill_img_new
            )

        # 武器部分
        char_info_text = ImageDraw.Draw(char_info_1)
        # weapon_img = Image.open(TEXT_PATH / 'char_info_weapon.png')
        # char_info_1.paste(weapon_img, (387, 590), weapon_img)
        weapon_star_img = get_star_png(
            self.raw_data['weaponInfo']['weaponStar']
        )
        weaponName = self.raw_data['weaponInfo']['weaponName']

        weaponAtk = self.raw_data['weaponInfo']['weaponStats'][0]['statValue']
        weaponLevel = self.raw_data['weaponInfo']['weaponLevel']
        weaponAffix = self.raw_data['weaponInfo']['weaponAffix']
        weaponEffect = self.raw_data['weaponInfo']['weaponEffect']
        weapon_type = self.raw_data['weaponInfo']['weaponType']

        char_info_1.paste(weapon_star_img, (402, 825), weapon_star_img)
        # char_info_text = ImageDraw.Draw(weapon_img)
        char_info_text.text(
            (412, 670),
            weaponName,
            (255, 255, 255),
            genshin_font_origin(50),
            anchor='lm',
        )
        char_info_text.text(
            (412, 710),
            weapon_type,
            (255, 255, 255),
            genshin_font_origin(20),
            anchor='lm',
        )
        char_info_text.text(
            (412, 750),
            '基础攻击力',
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='lm',
        )
        char_info_text.text(
            (755, 750),
            str(weaponAtk),
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='rm',
        )
        if len(self.raw_data['weaponInfo']['weaponStats']) == 2:
            weapon_sub_info = self.raw_data['weaponInfo']['weaponStats'][1][
                'statName'
            ]
            weapon_sub_value = self.raw_data['weaponInfo']['weaponStats'][1][
                'statValue'
            ]
            char_info_text.text(
                (412, 801),
                weapon_sub_info,
                (255, 255, 255),
                genshin_font_origin(32),
                anchor='lm',
            )
            char_info_text.text(
                (755, 801),
                str(weapon_sub_value),
                (255, 255, 255),
                genshin_font_origin(32),
                anchor='rm',
            )
        else:
            char_info_text.text(
                (412, 801),
                '该武器无副词条',
                (255, 255, 255),
                genshin_font_origin(32),
                anchor='lm',
            )
        char_info_text.text(
            (460, 893),
            f'Lv.{weaponLevel}',
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='mm',
        )
        char_info_text.text(
            (517, 895),
            f'精炼{str(weaponAffix)}阶',
            (255, 239, 173),
            genshin_font_origin(28),
            anchor='lm',
        )

        weaponEffect = strLenth(weaponEffect, 25, 455)
        weaponEffect = '\n'.join(weaponEffect.split('\n')[:5])
        char_info_text.text(
            (412, 925), weaponEffect, (255, 255, 255), genshin_font_origin(25)
        )

        fight_prop = self.raw_data['avatarFightProp']
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

        hp_green = fight_prop['addHp']
        attack_green = fight_prop['addAtk']
        defense_green = fight_prop['addDef']
        # 角色基本信息
        char_info_text.text(
            (411, 72),
            self.char_name,
            (255, 255, 255),
            genshin_font_origin(55),
            anchor='lm',
        )
        char_info_text.text(
            (411, 122),
            '等级{}'.format(self.char_level),
            (255, 255, 255),
            genshin_font_origin(40),
            anchor='lm',
        )
        char_info_text.text(
            (747, 126),
            str(self.char_fetter),
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='lm',
        )

        # aeq
        # char_info_text.text(
        #     (110, 771),
        #     a_skill_name,
        #     (255, 255, 255),
        #     genshin_font_origin(26),
        #     anchor='lm',
        # )
        char_info_text.text(
            (103, 812),
            f'{str(a_skill_level)}',
            (255, 255, 255),
            genshin_font_origin(30),
            anchor='mm',
        )

        # char_info_text.text(
        #     (110, 872),
        #     e_skill_name,
        #     (255, 255, 255),
        #     genshin_font_origin(26),
        #     anchor='lm',
        # )
        char_info_text.text(
            (103, 915),
            f'{str(e_skill_level)}',
            (255, 255, 255),
            genshin_font_origin(30),
            anchor='mm',
        )

        # char_info_text.text(
        #     (110, 973),
        #     q_skill_name,
        #     (255, 255, 255),
        #     genshin_font_origin(26),
        #     anchor='lm',
        # )
        char_info_text.text(
            (103, 1016),
            f'{str(q_skill_level)}',
            (255, 255, 255),
            genshin_font_origin(30),
            anchor='mm',
        )

        # 属性
        char_info_text.text(
            (785, 174),
            str(round(hp)),
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 227),
            str(round(attack)),
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 280),
            str(round(defense)),
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 333),
            str(round(em)),
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 386),
            f'{str(round(critrate * 100, 2))}%',
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 439),
            f'{str(round(critdmg * 100, 2))}%',
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 492),
            f'{str(round(ce * 100, 1))}%',
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )
        char_info_text.text(
            (785, 545),
            f'{str(round(dmgBonus * 100, 1))}%',
            (255, 255, 255),
            genshin_font_origin(28),
            anchor='rm',
        )

        char_info_text.text(
            (805, 174),
            f'(+{str(round(hp_green))})',
            (95, 251, 80),
            genshin_font_origin(28),
            anchor='lm',
        )
        char_info_text.text(
            (805, 227),
            f'(+{str(round(attack_green))})',
            (95, 251, 80),
            genshin_font_origin(28),
            anchor='lm',
        )
        char_info_text.text(
            (805, 280),
            f'(+{str(round(defense_green))})',
            (95, 251, 80),
            genshin_font_origin(28),
            anchor='lm',
        )

        uid = self.raw_data['playerUid']
        data_time = self.raw_data['dataTime']
        # uid
        char_info_text.text(
            (350, 1035),
            f'UID{uid}',
            (255, 255, 255),
            genshin_font_origin(24),
            anchor='rm',
        )
        # 数据最后更新时间
        char_info_text.text(
            (780, 600),
            f'数据最后更新于{data_time}',
            (255, 255, 255),
            genshin_font_origin(22),
            anchor='rm',
        )
        return char_info_1

    async def get_adv_card(self) -> Image.Image:
        adv_img = Image.open(TEXT_PATH / 'adv.png')
        return adv_img

    async def get_seq(self):
        self.percent, seq = await get_char_percent(
            self.raw_data, self.new_prop, self.char_name
        )
        self.seq_str = '·'.join([s[:2] for s in seq.split('|')]) + seq[-1:]
        if self.seq_str == '':
            self.seq_str = '无匹配'

    async def draw_char_curve_card(self) -> bytes:
        await self.get_new_prop()
        await self.get_seq()
        await self.get_artifacts_card(Image.new('RGB', (1, 1)))
        curve_img, curve_len = await draw_char_curve_data(
            self.char_name, self.raw_data
        )
        curve2_img, curve2_len = await draw_char_curve_data(
            self.char_name, self.new_prop
        )
        char_img = await self.get_char_img()
        adv_img = await self.get_adv_card()
        img = await self.get_bg_card(curve_len + curve2_len + 460, char_img)
        img.paste(char_img, (0, 0), char_img)
        char_info_1 = await self.get_char_card_1()
        img.paste(char_info_1, (0, 0), char_info_1)
        img.paste(curve_img, (0, 1085), curve_img)
        img.paste(curve2_img, (0, 1085 + curve_len), curve2_img)
        img.paste(adv_img, (0, 1085 + curve_len + curve2_len), adv_img)
        img_text = ImageDraw.Draw(img)
        # 顶栏
        img_text.text(
            (475, 2240),
            f'曲线(上)为正常面板,曲线(下)为触发各种战斗buff后面板',
            (255, 255, 255),
            genshin_font_origin(32),
            anchor='mm',
        )
        # 角色评分
        img_text.text(
            (785, 2380),
            f'{round(self.artifacts_all_score, 1)}',
            (255, 255, 255),
            genshin_font_origin(50),
            anchor='mm',
        )
        img_text.text(
            (785, 2542),
            f'{str(self.percent)+"%"}',
            (255, 255, 255),
            genshin_font_origin(50),
            anchor='mm',
        )
        img_text.text(
            (785, 2490),
            f'{self.seq_str}',
            (255, 255, 255),
            genshin_font_origin(18),
            anchor='mm',
        )

        img = img.convert('RGB')
        result_buffer = BytesIO()
        img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
        res = result_buffer.getvalue()
        return res

    async def draw_char_card(self) -> bytes:
        dmg_img, dmg_len = await self.get_dmg_card()
        char_img = await self.get_char_img()
        ex_len = dmg_len * 40 + 765
        img = await self.get_bg_card(ex_len, char_img)
        img.paste(char_img, (0, 0), char_img)
        char_info_1 = await self.get_char_card_1()
        char_info_2 = Image.open(TEXT_PATH / 'char_info_2.png')
        img.paste(char_info_1, (0, 0), char_info_1)
        img.paste(char_info_2, (0, 1085), char_info_2)
        img.paste(dmg_img, (0, 1850), dmg_img)
        await self.get_artifacts_card(img)
        img_text = ImageDraw.Draw(img)
        await self.get_seq()
        # 角色评分
        img_text.text(
            (768, 1564),
            f'{round(self.artifacts_all_score, 1)}',
            (255, 255, 255),
            genshin_font_origin(50),
            anchor='mm',
        )
        img_text.text(
            (768, 1726),
            f'{str(self.percent)+"%"}',
            (255, 255, 255),
            genshin_font_origin(50),
            anchor='mm',
        )
        img_text.text(
            (768, 1673),
            f'{self.seq_str}',
            (255, 255, 255),
            genshin_font_origin(18),
            anchor='mm',
        )

        img = img.convert('RGB')
        result_buffer = BytesIO()
        img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
        res = result_buffer.getvalue()
        return res


async def draw_char_img(
    raw_data: dict,
    weapon: Optional[str] = None,
    weapon_affix: Optional[int] = None,
    talent_num: Optional[int] = None,
    charUrl: Optional[str] = None,
    is_curve: bool = False,
) -> Union[bytes, str]:
    card = CharCard(raw_data=raw_data, char_url=charUrl)
    err = await card.new(
        weapon=weapon, weapon_affix=weapon_affix, talent_num=talent_num
    )
    if isinstance(err, str):
        return err
    if is_curve:
        res = await card.draw_char_curve_card()
    else:
        res = await card.draw_char_card()
    return res
