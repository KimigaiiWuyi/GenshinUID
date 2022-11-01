from typing import Tuple
from copy import deepcopy

from PIL import Image, ImageDraw

from ..etc.etc import TEXT_PATH
from .base_value import base_value_list
from ..etc.buff_calc import get_effect_prop
from ..etc.get_buff_list import get_buff_list
from ..etc.MAP_PATH import avatarName2SkillAdd
from ..etc.status_change import EXTRA_CHAR_LIST, STATUS_CHAR_LIST
from ...utils.genshin_fonts.genshin_fonts import genshin_font_origin

dmgBar_1 = Image.open(TEXT_PATH / 'dmgBar_1.png')
dmgBar_2 = Image.open(TEXT_PATH / 'dmgBar_2.png')


async def get_fight_prop(raw_data: dict) -> dict:
    # 获取值
    char_name = raw_data['avatarName']

    skillList = raw_data['avatarSkill']
    prop = deepcopy(raw_data['avatarFightProp'])
    prop['A_skill_level'] = skillList[0]['skillLevel']
    prop['E_skill_level'] = skillList[1]['skillLevel']
    prop['Q_skill_level'] = skillList[-1]['skillLevel']

    skill_add = avatarName2SkillAdd[char_name]
    for skillAdd_index in range(0, 2):
        if len(raw_data['talentList']) >= 3 + skillAdd_index * 2:
            if skill_add[skillAdd_index] == 'E':
                prop['E_skill_level'] += 3
            elif skill_add[skillAdd_index] == 'Q':
                prop['Q_skill_level'] += 3

    prop = await get_effect_prop(prop, [], char_name)
    all_effect = await get_buff_list(raw_data, 'fight')

    # 开启效果
    if char_name in STATUS_CHAR_LIST:
        for skill_effect in STATUS_CHAR_LIST[char_name]:
            skill_level = prop[f'{skill_effect["name"][0]}_skill_level'] - 1
            skill_value = skill_effect['value'][skill_level]
            skill: str = skill_effect['effect'].format(skill_value)
            if skill.endswith('%'):
                skill = skill[:-1]
            all_effect.append(skill)

    # 特殊效果,目前有雷神满愿力
    prop['extra_effect'] = {}
    if char_name in EXTRA_CHAR_LIST:
        if char_name == '雷电将军':
            skill_effect = EXTRA_CHAR_LIST[char_name]
            skill_level = prop[f'{skill_effect["name"][0]}_skill_level'] - 1
            value_1 = float(skill_effect['value'][skill_level].split('+')[0])
            value_1 *= 0.6
            value_2 = float(skill_effect['value'][skill_level].split('+')[1])
            all_effect.append(
                (
                    f'Q一段伤害:addAtk+{60*value_2};'
                    f'Q重击伤害:addAtk+{60*value_2};'
                    f'Q高空下落伤害:addAtk+{60*value_2}'
                )
            )
            prop['extra_effect'] = {'Q梦想一刀基础伤害(满愿力)': value_1}

    # 在计算buff前, 引入特殊效果
    if char_name == '雷电将军':
        all_effect.append('Q:dmgBonus+27')
    elif char_name == '钟离':
        all_effect.append('r+-20')
    elif char_name == '妮露':
        all_effect.append('addHp+25')
        all_effect.append('elementalMastery+80')

    # 计算全部的buff，添加入属性
    prop = await get_effect_prop(prop, all_effect, char_name)
    return prop


async def draw_dmg_img(
    raw_data: dict, power_list: dict, prop: dict
) -> Tuple[Image.Image, int]:
    # 获取值
    char_name = raw_data['avatarName']
    char_level = int(raw_data['avatarLevel'])
    enemy_level = char_level

    extra_effect = prop['extra_effect']
    sp = prop['sp']

    # 计算伤害计算部分图片长宽值
    w = 950
    h = 40 * (len(power_list) + 1)
    result_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # 反复贴上不同颜色的长条
    for i in range(0, len(power_list) + 1):
        if i % 2 == 0:
            result_img.paste(dmgBar_1, (0, i * 40))
        else:
            result_img.paste(dmgBar_2, (0, i * 40))

    result_draw = ImageDraw.Draw(result_img)

    text_color = (255, 255, 255)
    title_color = (255, 255, 100)
    text_size = genshin_font_origin(28)
    result_draw.text((45, 22), '角色动作', title_color, text_size, anchor='lm')
    result_draw.text((460, 22), '暴击伤害', title_color, text_size, anchor='lm')
    result_draw.text((695, 22), '期望伤害', title_color, text_size, anchor='lm')

    for index, power_name in enumerate(power_list):
        # 攻击类型ABCEQ应为label首位
        attack_type = power_name[0]
        # 如果是雷电将军, 则就按首位,因为Q的几段伤害均视为元素爆发
        if char_name == '雷电将军':
            pass
        else:
            # 重击或瞄准射击在label内,则视为B重击伤害,例如公子E内的重击伤害,不视为E伤害,而是B伤害
            if '重击' in power_name or '瞄准射击' in power_name:
                attack_type = 'B'
            # 特殊重击类型,例如甘雨和夜兰
            elif '破局矢' in power_name or '霜华矢' in power_name:
                attack_type = 'B'
            # 下落伤害类型,例如魈
            elif '高空下落' in power_name:
                attack_type = 'C'
            # 一段伤害, 二段伤害等等 应视为A伤害
            elif '段' in power_name and '伤害' in power_name:
                attack_type = 'A'

        # 额外的伤害增益,基于之前的特殊label
        sp_dmgBonus = 0
        sp_addDmg = 0
        sp_attack = 0

        if sp:
            for sp_single in sp:
                if sp_single['effect_name'] in power_name:
                    if sp_single['effect_attr'] == 'dmgBonus':
                        sp_dmgBonus += sp_single['effect_value']
                    elif sp_single['effect_attr'] == 'addDmg':
                        sp_addDmg += sp_single['effect_value']
                    elif sp_single['effect_attr'] == 'atk':
                        sp_attack += sp_single['effect_value']
                    else:
                        sp_attack += sp_single['effect_value']

        # 根据type计算有效属性
        if '攻击' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_atk'] + sp_attack
        elif '生命值' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_hp']
        elif '防御' in power_list[power_name]['type']:
            effect_prop = prop[f'{power_name[0]}_def']
        else:
            effect_prop = prop[f'{power_name[0]}_atk']

        # 按照ABCEQ等级查找倍率
        power = power_list[power_name]['value'][
            prop['{}_skill_level'.format(power_name[0])] - 1
        ]
        # 计算是否多次伤害
        power_plus = power_list[power_name]['plus']

        # 拿到百分比和固定值,百分比为float,形如2.2 也就是202%
        power_percent, power_value = await power_to_value(power, power_plus)

        # 额外加成,目前只有雷神
        if extra_effect and power_name in extra_effect:
            power_percent += extra_effect[power_name]

        # 计算这个label的伤害加成为多少
        # 这个label是否为物理伤害
        if power_name in ['Q光降之剑基础伤害', 'Q光降之剑基础伤害(13层)', 'Q每层能量伤害']:
            dmgBonus_cal = (
                prop['{}_dmgBonus'.format(attack_type)]
                + sp_dmgBonus
                + prop['physicalDmgBonus']
            )
        # 常规元素伤害
        else:
            dmgBonus_cal = (
                prop['{}_dmgBonus'.format(attack_type)] + sp_dmgBonus
            )
        # 计算暴击伤害
        critdmg_cal = prop['{}_critDmg'.format(attack_type)]
        # 计算暴击率
        critrate_cal = prop['{}_critRate'.format(attack_type)]
        em_cal = prop['{}_elementalMastery'.format(attack_type)]
        # 计算防御区
        d_cal = (char_level + 100) / (
            (char_level + 100)
            + (1 - prop['{}_d'.format(attack_type)])
            * (1 - prop['{}_ignoreDef'.format(attack_type)])
            * (enemy_level + 100)
        )
        # 计算抗性区
        if prop['{}_r'.format(attack_type)] > 0.75:
            r = 1 / (1 + 4 * prop['{}_r'.format(attack_type)])
        elif prop['{}_r'.format(attack_type)] > 0:
            r = 1 - prop['{}_r'.format(attack_type)]
        else:
            r = 1 - prop['{}_r'.format(attack_type)] / 2

        # 计算元素反应 增幅
        for reaction in ['蒸发', '融化']:
            if reaction in power_list[power_name]['name']:
                k = 0
                if reaction == '蒸发':
                    if raw_data['avatarElement'] == 'Pyro':
                        k = 1.5
                    else:
                        k = 2
                elif reaction == '融化':
                    if raw_data['avatarElement'] == 'Pyro':
                        k = 2
                    else:
                        k = 1.5
                reaction_add_dmg = k * (
                    1 + (2.78 * em_cal) / (em_cal + 1400) + prop['a']
                )
                break
        else:
            reaction_add_dmg = 1

        # 计算草系相关反应
        reaction_power = 0
        for reaction in ['超激化', '蔓激化']:
            if reaction in power_list[power_name]['name']:
                if reaction == '超激化':
                    k = 2.3
                else:
                    k = 2.5
                reaction_power = (
                    k
                    * base_value_list[char_level - 1]
                    * (1 + (5 * em_cal) / (em_cal + 1200))
                )
                break

        # 草系反应增加到倍率区
        power_value += reaction_power

        # 计算直接增加的伤害
        add_dmg = prop['{}_addDmg'.format(attack_type)] + sp_addDmg

        # 特殊伤害提高
        sp_power_percent = 0
        if '13层' in power_name:
            sp_power_percent = (
                float(
                    power_list['Q每层能量伤害']['value'][
                        prop['{}_skill_level'.format(power_name[0])] - 1
                    ].replace('%', '')
                )
                / 100
            ) * 13

        # 根据label_name 计算数值
        if '治疗' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['healBonus'])
        elif '扩散伤害' in power_name:
            crit_dmg = avg_dmg = (
                base_value_list[char_level - 1]
                * 1.2
                * (1 + (16.0 * em_cal) / (em_cal + 2000) + prop['a'])
                * (1 + prop['g'] / 100)
                * r
            )
            power_list[power_name]['name'] = power_list[power_name]['name'][1:]
        elif '(绽放)' in power_name:
            if '丰穰之核' in power_name:
                ex_add = ((prop['hp'] - 30000) / 1000) * 0.09
                if ex_add >= 4:
                    ex_add = 4
                prop['a'] += ex_add
            crit_dmg = avg_dmg = (
                base_value_list[char_level - 1]
                * 4
                * (1 + (16.0 * em_cal) / (em_cal + 2000) + prop['a'])
                * r
            )
            power_list[power_name]['name'] = power_list[power_name]['name'][1:]
        elif '伤害值提升' in power_name:
            crit_dmg = avg_dmg = effect_prop * power_percent + power_value
        elif '护盾' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['shieldBonus'])
            if char_name == '钟离' and '总护盾量' in power_name:
                crit_dmg = avg_dmg = avg_dmg * 1.5
        elif '提升' in power_name or '提高' in power_name:
            crit_dmg = avg_dmg = effect_prop * power_percent + power_value
        else:
            # 不暴击伤害
            normal_dmg = (
                (
                    effect_prop * (power_percent + sp_power_percent)
                    + power_value
                    + add_dmg
                )
                * (1 + dmgBonus_cal)
                * d_cal
                * r
                * reaction_add_dmg
            )
            # 暴击伤害
            crit_dmg = normal_dmg * (1 + critdmg_cal)
            # 平均伤害
            avg_dmg = crit_dmg * critrate_cal + (1 - critrate_cal) * normal_dmg
            # 如果平均伤害超过了暴击伤害,则直接使用暴击伤害(暴击率>100)
            if avg_dmg >= crit_dmg:
                avg_dmg = crit_dmg
            # 如果暴击率为负数,则期望伤害直接使用普通伤害
            if critrate_cal <= 0:
                avg_dmg = normal_dmg

        result_draw.text(
            (45, 22 + (index + 1) * 40),
            power_list[power_name]['name'],
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (460, 22 + (index + 1) * 40),
            str(round(crit_dmg)),
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (695, 22 + (index + 1) * 40),
            str(round(avg_dmg)),
            text_color,
            text_size,
            anchor='lm',
        )

    return result_img, len(power_list) + 2


async def power_to_value(power: str, power_plus: int) -> Tuple[float, float]:
    """
    将power转换为value
    """
    if '+' in power:
        power_percent = (
            float(power.split('+')[0].replace('%', '')) / 100
        ) * power_plus
        power_value = power.split('+')[1]
        if '%' in power_value:
            power_percent += (
                float(power_value.replace('%', '')) / 100 * power_plus
            )
            power_value = 0
        else:
            power_value = float(power_value)
    elif '%' in power:
        power_percent = float(power.replace('%', '')) / 100 * power_plus
        power_value = 0
    else:
        power_percent = 0
        power_value = float(power)

    return power_percent, power_value
