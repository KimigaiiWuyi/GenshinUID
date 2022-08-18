import json
from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw

from .base_value import base_value_list
from ...utils.genshin_fonts.genshin_fonts import genshin_font_origin

DMG_PATH = Path(__file__).parents[0]
DMG_TEXT_PATH = DMG_PATH / 'texture2d'

version = '2.8.0'
avatarName2SkillAdd_fileName = f'avatarName2SkillAdd_mapping_{version}.json'

with open(DMG_PATH / avatarName2SkillAdd_fileName, "r", encoding='UTF-8') as f:
    avatarName2SkillAdd = json.load(f)

with open(DMG_PATH / 'artifacts_effect.json', "r", encoding='UTF-8') as f:
    artifacts_effect_map = json.load(f)

with open(DMG_PATH / 'weapons_effect.json', "r", encoding='UTF-8') as f:
    weapons_effect_map = json.load(f)

with open(DMG_PATH / 'char_talent_effect.json', "r", encoding='UTF-8') as f:
    char_talent_effect_map = json.load(f)

with open(DMG_PATH / 'char_skill_effect.json', "r", encoding='UTF-8') as f:
    char_skill_effect_map = json.load(f)

dmgBar_1 = Image.open(DMG_TEXT_PATH / 'dmgBar_1.png')
dmgBar_2 = Image.open(DMG_TEXT_PATH / 'dmgBar_2.png')


async def draw_dmgCacl_img(raw_data: dict) -> Tuple[Image.Image, int]:
    with open(DMG_PATH / 'char_action.json', "r", encoding='UTF-8') as f:
        char_action = json.load(f)
    char_name = raw_data['avatarName']
    char_level = int(raw_data['avatarLevel'])
    weaponName = raw_data['weaponInfo']['weaponName']
    weaponType = raw_data['weaponInfo']['weaponType']
    weaponAffix = raw_data['weaponInfo']['weaponAffix']

    skillList = raw_data['avatarSkill']
    a_skill_name = skillList[0]['skillName'].replace('普通攻击·', '')
    prop = {}
    prop['A_skill_level'] = skillList[0]['skillLevel']
    e_skill_name = skillList[1]['skillName']
    prop['E_skill_level'] = skillList[1]['skillLevel']
    q_skill_name = skillList[-1]['skillName']
    prop['Q_skill_level'] = skillList[-1]['skillLevel']

    enemy_level = char_level
    skill_add = avatarName2SkillAdd[char_name]
    for skillAdd_index in range(0, 2):
        if len(raw_data['talentList']) >= 3 + skillAdd_index * 2:
            if skill_add[skillAdd_index] == 'E':
                prop['E_skill_level'] += 3
            elif skill_add[skillAdd_index] == 'Q':
                prop['Q_skill_level'] += 3

    fight_prop = raw_data['avatarFightProp']
    prop['basehp'] = fight_prop['baseHp']
    prop['baseattack'] = fight_prop['baseAtk']
    prop['basedefense'] = fight_prop['baseDef']

    prop['hp'] = fight_prop['hp']
    prop['attack'] = fight_prop['atk']
    prop['defense'] = fight_prop['def']
    prop['em'] = fight_prop['elementalMastery']
    prop['critrate'] = fight_prop['critRate']
    prop['critdmg'] = fight_prop['critDmg']
    prop['ce'] = fight_prop['energyRecharge']
    prop['physicalDmgBonus'] = physicalDmgBonus = fight_prop[
        'physicalDmgBonus'
    ]
    prop['dmgBonus'] = dmgBonus = fight_prop['dmgBonus']
    prop['healBouns'] = fight_prop['healBonus']
    prop['shieldBouns'] = 0

    if char_name not in char_action:
        faild_img = Image.new('RGBA', (950, 1))
        return faild_img, 0
    power_list = char_action[char_name]

    # 给每个技能 分别添加上属性
    for prop_attr in [
        'dmgBonus',
        'critrate',
        'critdmg',
        'addDmg',
        'd',
        'r',
        'ignoreDef',
    ]:
        if prop_attr in ['addDmg', 'd', 'r', 'ignoreDef']:
            prop['{}'.format(prop_attr)] = 0
        for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
            prop['{}_{}'.format(prop_limit, prop_attr)] = 0

    # 计算角色伤害加成应该使用什么
    for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
        if weaponType == '法器' or char_name in [
            '荒泷一斗',
            '刻晴',
            '诺艾尔',
            '胡桃',
            '宵宫',
            '魈',
        ]:
            prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        elif '万叶' in char_name and len(raw_data['talentList']) >= 6:
            prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        elif weaponType == '弓':
            if prop_limit in ['A', 'C']:
                prop['{}_dmgBonus'.format(prop_limit)] = physicalDmgBonus
            elif prop_limit in ['B', 'E', 'Q']:
                prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus
        else:
            if prop_limit in ['A', 'B', 'C']:
                prop['{}_dmgBonus'.format(prop_limit)] = physicalDmgBonus
            elif prop_limit in ['E', 'Q']:
                prop['{}_dmgBonus'.format(prop_limit)] = dmgBonus

    # 初始化各种值
    prop['hp_green'] = fight_prop['addHp']
    prop['attack_green'] = fight_prop['addAtk']
    prop['defense_green'] = fight_prop['addDef']

    prop['r'] = 0.1
    prop['a'] = 0
    prop['g'] = 0
    prop['k'] = 1

    all_effect = []

    # 计算武器buff
    weapon_effet = weapons_effect_map[weaponName][str(weaponAffix)]
    all_effect.append(weapon_effet)

    # 计算圣遗物套装
    if 'equipSets' in raw_data:
        equipSets = raw_data['equipSets']
    else:
        artifact_set_list = []
        for i in raw_data['equipList']:
            artifact_set_list.append(i['aritifactSetsName'])
        equipSetList = set(artifact_set_list)
        equipSets = {'type': '', 'set': ''}
        for equip in equipSetList:
            if artifact_set_list.count(equip) >= 4:
                equipSets['type'] = '4'
                equipSets['set'] = equip
                break
            elif artifact_set_list.count(equip) == 1:
                pass
            elif artifact_set_list.count(equip) >= 2:
                equipSets['type'] += '2'
                equipSets['set'] += '|' + equip

    if equipSets['set'].startswith('|'):
        equipSets['set'] = equipSets['set'][1:]

    # 计算圣遗物buff
    if equipSets['type'] == '4':
        all_effect.append(artifacts_effect_map[equipSets['set']]['4'])
    elif equipSets['type'] == '2':
        all_effect.append(artifacts_effect_map[equipSets['set']]['2'])
    elif equipSets['type'] == '22':
        if equipSets['set'][-2] == '之':
            first_artifact = equipSets['set'][-3:]
        else:
            first_artifact = equipSets['set'][-2:]
        second_artifact = equipSets['set'][:2]
        temp = []
        temp_number = 0
        for artifacts_single_effect in artifacts_effect_map:
            if first_artifact in artifacts_single_effect:
                temp_number += 1
                temp.append(artifacts_effect_map[artifacts_single_effect]['2'])
                if temp_number >= 2:
                    break
        all_effect.extend(temp)

    # 计算技能buff
    for talent in char_talent_effect_map[char_name]:
        if int(talent) <= len(raw_data['talentList']):
            all_effect.append(char_talent_effect_map[char_name][talent])
        else:
            break

    # 计算角色buff
    for skill in char_skill_effect_map[char_name]:
        if int(skill) <= char_level:
            all_effect.append(char_skill_effect_map[char_name][skill])
        else:
            break

    # 开启效果
    power_effect = ''
    if 'effect' in power_list:
        for skill_effect_single in power_list['effect']:
            skill_effect_name = skill_effect_single['name']
            skill_effect_value = skill_effect_single['value']
            skill_effect = skill_effect_single['effect']
            skill_effect_level = prop[
                '{}_skill_level'.format(skill_effect_name[0])
            ]
            skill_effect_value_detail = skill_effect_value[skill_effect_level]
            if skill_effect[-1] == '}':
                skill_effect_value_detail = skill_effect_value_detail.replace(
                    '%', ''
                )
            add_limit = skill_effect.split(':')
            if len(add_limit) == 1:
                for i in power_list:
                    if i == 'effect':
                        pass
                    else:
                        power_list[i]['name'] = (
                            '开{}后 '.format(skill_effect_name[0])
                            + power_list[i]['name']
                        )
            else:
                for i in power_list:
                    if i == 'effect':
                        pass
                    else:
                        add_type = i[0]
                        if '重击' in i or '蓄力' in i:
                            add_type = 'B'
                        elif '冲击伤害' in i:
                            add_type = 'C'
                        if add_type in add_limit[0]:
                            power_list[i]['name'] = (
                                '开{}后 '.format(skill_effect_name[0])
                                + power_list[i]['name']
                            )
            power_effect = skill_effect.format(skill_effect_value_detail)
            all_effect.append(power_effect)
        del power_list['effect']

    extra_effect = {}
    if 'extra' in power_list:
        if char_name == '雷电将军':
            extra_value = (
                float(
                    power_list["extra"]["value"][
                        prop["Q_skill_level"]
                    ].replace("%", "")
                )
                * 0.6
            )
            extra_effect = {'Q梦想一刀基础伤害(满愿力)': extra_value}
        del power_list['extra']

    # 在计算buff前, 引入特殊效果
    if char_name == '雷电将军':
        all_effect.append('Q:dmgBonus+27')

    sp = []
    # 计算全部的buff，添加入属性
    if all_effect:
        all_effect = ';'.join(all_effect)
        all_effect_list = all_effect.split(';')
        for effect in all_effect_list:
            if effect == '':
                continue

            effect_limit = ''
            if ':' in effect:
                pass
            else:
                effect = ':' + effect

            effect_limit = effect.split(':')[0]
            effect_attr = effect.split(':')[1].split('+')[0]
            effect_value = effect.split(':')[1].split('+')[-1]

            base_check = True
            if '%' in effect_value:
                effect_value_base_on_attr = effect_value.split('%')[-1]
                effect_value_base_on_value = '%'.join(
                    effect_value.split('%')[:-1]
                )
                if '%' in effect_value_base_on_value:
                    effect_value_base_on_max_value = (
                        effect_value_base_on_value.split('%')[0]
                    )
                    effect_value_base_on_value = (
                        effect_value_base_on_value.split('%')[-1]
                    )
                    effect_now_value = (
                        float(effect_value_base_on_value)
                        * prop[effect_value_base_on_attr]
                    )
                    effect_value = (
                        float(effect_value_base_on_max_value)
                        if effect_now_value
                        >= float(effect_value_base_on_max_value)
                        else effect_now_value
                    )
                else:
                    effect_value = (
                        float(effect_value_base_on_value)
                        * prop[effect_value_base_on_attr]
                    )
                base_check = False

            if effect_attr != 'em':
                effect_value = float(effect_value) / 100
                if effect_attr in ['hp', 'attack', 'defense'] and base_check:
                    effect_value += (
                        effect_value * prop['base{}'.format(effect_attr)]
                    )
            else:
                effect_value = float(effect_value)

            if effect_limit:
                if '\u4e00' <= effect_limit[0] <= '\u9fff':
                    sp.append(
                        {
                            'effect_name': effect_limit,
                            'effect_attr': effect_attr,
                            'effect_value': effect_value,
                        }
                    )
                else:
                    for limit in effect_limit:
                        prop[
                            '{}_{}'.format(limit, effect_attr)
                        ] += effect_value
            else:
                prop['{}'.format(effect_attr)] += effect_value

    w = 950
    h = 40 * (len(power_list) + 1)
    result_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
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
        attack_type = power_name[0]
        if '重击' in power_name or '瞄准射击' in power_name:
            attack_type = 'B'
        elif '冲击伤害' in power_name:
            attack_type = 'C'
        elif '段' in power_name and '伤害' in power_name:
            attack_type = 'A'

        sp_dmgBonus = 0
        sp_addDmg = 0

        if sp:
            for sp_single in sp:
                if sp_single['effect_name'] == power_name[1:]:
                    if sp_single['effect_attr'] == 'dmgBouns':
                        sp_dmgBonus += sp_single['effect_value']
                    elif sp_single['effect_attr'] == 'addDmg':
                        sp_addDmg += sp_single['effect_value']

        if '攻击' in power_list[power_name]['type']:
            effect_prop = prop['attack']
        elif '生命值' in power_list[power_name]['type']:
            effect_prop = prop['hp']
        elif '防御' in power_list[power_name]['type']:
            effect_prop = prop['defense']
        else:
            effect_prop = prop['attack']

        power = power_list[power_name]['value'][
            prop['{}_skill_level'.format(power_name[0])]
        ]
        power_plus = power_list[power_name]['plus']

        power_percent, power_value = await power_to_value(power, power_plus)

        if extra_effect and power_name in extra_effect:
            power_percent += extra_effect[power_name]

        dmgBonus_cal = prop['{}_dmgBonus'.format(attack_type)] + sp_dmgBonus
        critdmg_cal = prop['critdmg'] + prop['{}_critdmg'.format(attack_type)]
        critrate_cal = (
            prop['critrate'] + prop['{}_critrate'.format(attack_type)]
        )
        d_cal = (char_level + 100) / (
            (char_level + 100)
            + (1 - prop['{}_d'.format(attack_type)])
            * (1 - prop['{}_ignoreDef'.format(attack_type)])
            * (enemy_level + 100)
        )
        r = 1 - prop['r']

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
                    1 + (2.78 * prop['em']) / (prop['em'] + 1400) + prop['a']
                )
                break
        else:
            reaction_add_dmg = 1

        add_dmg = prop['{}_addDmg'.format(attack_type)] + sp_addDmg

        if '治疗' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['healBouns'])
        elif '扩散伤害' in power_name:
            crit_dmg = avg_dmg = (
                base_value_list[char_level]
                * 1.2
                * (1 + (16.0 * prop['em']) / (prop['em'] + 2000) + prop['a'])
                * r
            )
            power_list[power_name]['name'] = power_list[power_name]['name'][1:]
        elif '伤害值提升' in power_name:
            crit_dmg = avg_dmg = effect_prop * power_percent + power_value
        elif '护盾' in power_name:
            crit_dmg = avg_dmg = (
                effect_prop * power_percent + power_value
            ) * (1 + prop['shieldBouns'])
        elif '提升' in power_name or '提高' in power_name:
            continue
        else:
            crit_dmg = (effect_prop * power_percent + power_value) * (
                1 + critdmg_cal
            ) * (1 + dmgBonus_cal) * d_cal * r * reaction_add_dmg + add_dmg
            avg_dmg = (
                (crit_dmg - add_dmg) * critrate_cal
                + (1 - critrate_cal)
                * (effect_prop * power_percent + power_value)
                * (1 + dmgBonus_cal)
                * d_cal
                * r
                * reaction_add_dmg
                + add_dmg
            )

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
    else:
        power_percent = float(power.replace('%', '')) / 100 * power_plus
        power_value = 0

    return power_percent, power_value
