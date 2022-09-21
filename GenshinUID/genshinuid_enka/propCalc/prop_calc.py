import json
import math
from pathlib import Path
from copy import deepcopy
from typing import List, Tuple, Union, Optional

from ...utils.minigg_api.get_minigg_data import get_char_info, get_weapon_info

PATH = Path(__file__).parent

with open(PATH / 'base_weapons.json', 'r', encoding='UTF-8') as f:
    base_weapons = json.load(f)

with open(PATH / 'base_artifacts.json', 'r', encoding='UTF-8') as f:
    base_artifacts = json.load(f)

ELEMENT_MAP = {
    '风': 'Anemo',
    '冰': 'Cryo',
    '草': 'Dendro',
    '雷': 'Electro',
    '岩': 'Geo',
    '水': 'Hydro',
    '水': 'Pyro',
}

baseFightProp = {
    'hp': 0.0,
    'baseHp': 0.0,
    'addHp': 0.0,
    'exHp': 0.0,
    'atk': 0.0,
    'baseAtk': 0.0,
    'addAtk': 0.0,
    'exAtk': 0.0,
    'def': 0.0,
    'baseDef': 0.0,
    'addDef': 0.0,
    'exDef': 0.0,
    'elementalMastery': 0.0,
    'critRate': 0.05,
    'critDmg': 0.5,
    'energyRecharge': 1.0,
    'healBonus': 0.0,
    'healedBonus': 0.0,
    'physicalDmgSub': 0.0,
    'physicalDmgBonus': 0.0,
    'dmgBonus': 0.0,
}

baseWeaponInfo = {
    'itemId': 0,
    'nameTextMapHash': '0',
    'weaponIcon': 'UI_EquipIcon_Bow_Changed',
    'weaponType': '',
    'weaponName': '',
    'weaponStar': 0,
    'promoteLevel': 0,
    'weaponLevel': 0,
    'weaponAffix': 1,
    'weaponStats': [
        {
            'appendPropId': '',
            'statName': '基础攻击力',
            'statValue': 0,
        },
        {
            'appendPropId': '',
            'statName': '',
            'statValue': 0,
        },
    ],
    'weaponEffect': '',
}

ATTR_MAP = {
    '元素精通': 'elementalMastery',
    '物理伤害加成': 'physicalDmgBonus',
    '元素伤害加成': 'dmgBonus',
    '充能效率': 'energyRecharge',
    '暴击伤害': 'critDmg',
    '暴击率': 'critRate',
    '攻击力': 'addAtk',
    '防御力': 'addDef',
}

MIN_MAP = {
    'hp': 'addHp',
    'exHp': 'exHp',
    'attack': 'addAtk',
    'exAtk': 'exAtk',
    'defense': 'addDef',
    'exDef': 'exDef',
    'dmgBonus': 'dmgBonus',
    'physicalDmgBonus': 'physicalDmgBonus',
    'ce': 'energyRecharge',
    'em': 'elementalMastery',
    'critdmg': 'critDmg',
    'critrate': 'critRate',
}


async def get_card_prop(raw_data: dict, weapon: Optional[str] = None) -> dict:
    char_name = raw_data['avatarName']
    char_level = raw_data['avatarLevel']
    char_element = raw_data['avatarElement']

    if weapon:
        weapon_info = deepcopy(baseWeaponInfo)
        weapon_raw_data = await get_weapon_info(weapon)
        if 'errcode' in weapon_raw_data:
            return {}
        weapon_level_data = await get_weapon_info(weapon, '90')
        weapon_info['weaponName'] = weapon_raw_data['name']
        weapon_info['weaponStar'] = int(weapon_raw_data['rarity'])
        weapon_info['promoteLevel'] = 6
        weapon_info['weaponLevel'] = 90
        weapon_info['weaponAffix'] = 1
        weapon_info['weaponStats'][0]['statValue'] = round(
            weapon_level_data['attack']
        )
        weapon_info['weaponStats'][1]['statName'] = weapon_raw_data['substat']
        if weapon_raw_data['substat'] == '元素精通':
            fake_value = round(weapon_level_data['specialized'])
        else:
            fake_value = float(
                '{:.2f}'.format(weapon_level_data['specialized'] * 100)
            )
        weapon_info['weaponStats'][1]['statValue'] = fake_value
        if 'effect' in weapon_raw_data:
            weapon_info['weaponEffect'] = weapon_raw_data['effect'].format(
                *weapon_raw_data['r{}'.format(str(weapon_info['weaponAffix']))]
            )
        else:
            weapon_info['weaponEffect'] = '无特效。'
        raw_data['weaponInfo'] = weapon_info

    # 武器基本属性
    weapon_name = raw_data['weaponInfo']['weaponName']
    weapon_affix = raw_data['weaponInfo']['weaponAffix']
    weapon_atk = raw_data['weaponInfo']['weaponStats'][0]['statValue']
    weapon_sub = raw_data['weaponInfo']['weaponStats'][1]['statName']
    weapon_sub_val = raw_data['weaponInfo']['weaponStats'][1]['statValue']

    fight_prop = deepcopy(baseFightProp)

    char_raw = await get_char_info(name=char_name, mode='char')
    char_data = await get_char_info(
        name=char_name, mode='char', level=char_level
    )
    if char_data is None or isinstance(char_data, List):
        return {}

    baseHp = fight_prop['baseHp'] = char_data['hp']
    baseAtk = fight_prop['baseAtk'] = char_data['attack'] + weapon_atk
    baseDef = fight_prop['baseDef'] = char_data['defense']

    # 计算突破加成
    if isinstance(char_raw, dict):
        for attr in ATTR_MAP:
            if attr in char_raw['substat']:
                sp = char_data['specialized']
                if attr == '暴击伤害':
                    sp -= 0.5
                elif attr == '暴击率':
                    sp -= 0.05
                fight_prop[ATTR_MAP[attr]] += sp
            if attr in weapon_sub:
                if attr == '元素精通':
                    weapon_sub_val *= 100
                fight_prop[ATTR_MAP[attr]] += weapon_sub_val / 100
    else:
        return {}

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
                equipSets['set'] += equip

    all_effects: List[str] = []

    # 计算圣遗物套装效果
    if equipSets['type'] == '4':
        for i in base_artifacts[equipSets['set']]:
            all_effects.extend(base_artifacts[equipSets['set']][i].split(';'))
    elif equipSets['type'] == '2':
        all_effects.extend(base_artifacts[equipSets['set']]['2'].split(';'))
    elif equipSets['type'] == '22':
        if equipSets['set'][2] == '之':
            t = equipSets['set'][:3]
        else:
            t = equipSets['set'][:2]

        if equipSets['set'][-2] == '之':
            e = equipSets['set'][-3:]
        else:
            e = equipSets['set'][-2:]

        for i in base_artifacts:
            if i.startswith(t):
                all_effects.extend(base_artifacts[i]['2'].split(';'))
            elif i.endswith(e):
                all_effects.extend(base_artifacts[i]['2'].split(';'))

    # 计算武器效果
    all_effects.extend(base_weapons[weapon_name][str(weapon_affix)].split(';'))

    # 计算圣遗物效果
    for equip in raw_data['equipList']:
        statNmae = equip['reliquaryMainstat']['statName']
        statValue = equip['reliquaryMainstat']['statValue']
        all_effects.append(await text_to_effect(statNmae, statValue))
        for sub in equip['reliquarySubstats']:
            sub_name = sub['statName']
            sub_value = sub['statValue']
            all_effects.append(await text_to_effect(sub_name, sub_value))

    add_effects: List[str] = []
    print(all_effects)
    for effect in all_effects:
        if effect == '':
            continue
        else:
            effect_attr, effect_value = effect.split('+')
            if '%' in effect_value:
                add_effects.append(effect)
                continue
            else:
                if effect_attr.startswith('ex') or effect_attr == 'em':
                    effect_value = float(effect_value)
                else:
                    effect_value = float(effect_value) / 100
                for i in MIN_MAP:
                    if effect_attr == i:
                        fight_prop[MIN_MAP[i]] += effect_value
                        break
                else:
                    if effect_attr.replace('DmgBonus', '') == char_element:
                        fight_prop['dmgBonus'] += effect_value

    tempHp = baseHp * (fight_prop['addHp'] + 1)
    tempAtk = baseAtk * (fight_prop['addAtk'] + 1)
    tempDef = baseDef * (fight_prop['addDef'] + 1)

    for effect in add_effects:
        if effect == '':
            continue
        else:
            effect_attr, effect_value = effect.split('+')
            effect_value, effect_base = effect_value.split('%')
            effect_value = float(effect_value) / 100

            if effect_base == 'hp':
                for i in MIN_MAP:
                    if effect_attr == i:
                        if effect_attr == 'attack':
                            effect_now = 'exAtk'
                        else:
                            effect_now = MIN_MAP[i]
                        fight_prop[effect_now] += effect_value * tempHp
                        break
            elif effect_base == 'ce':
                for i in MIN_MAP:
                    if effect_attr == i:
                        fight_prop[MIN_MAP[i]] += effect_value * (
                            fight_prop['energyRecharge'] - 1
                        )
                        break
            elif effect_base == 'attack':
                for i in MIN_MAP:
                    if effect_attr == i:
                        fight_prop[MIN_MAP[i]] += effect_value * tempAtk
                        break
            elif effect_base == 'defense':
                for i in MIN_MAP:
                    if effect_attr == i:
                        fight_prop[MIN_MAP[i]] += effect_value * tempDef
                        break
            else:
                for j in MIN_MAP:
                    for i in MIN_MAP:
                        if effect_attr == i:
                            fight_prop[MIN_MAP[i]] += (
                                effect_value * fight_prop[j]
                            )
                            break

    # 将addAtk和addDef转换为具体数值
    fight_prop['addHp'] = baseHp * fight_prop['addHp'] + fight_prop['exHp']
    fight_prop['addAtk'] = baseAtk * fight_prop['addAtk'] + fight_prop['exAtk']
    fight_prop['addDef'] = baseDef * fight_prop['addDef'] + fight_prop['exDef']
    fight_prop['hp'] = fight_prop['addHp'] + fight_prop['baseHp']
    fight_prop['atk'] = fight_prop['addAtk'] + fight_prop['baseAtk']
    fight_prop['def'] = fight_prop['addDef'] + fight_prop['baseDef']

    raw_data['avatarFightProp'] = fight_prop
    return raw_data


async def text_to_effect(name: str, value: float) -> str:
    str = ''
    if name == '血量':
        str = f'exHp+{value}'
    elif name == '百分比血量':
        str = f'hp+{value}'
    elif name == '攻击力':
        str = f'exAtk+{value}'
    elif name == '百分比攻击力':
        str = f'attack+{value}'
    elif name == '防御力':
        str = f'exDef+{value}'
    elif name == '百分比防御力':
        str = f'defense+{value}'
    elif name == '暴击率':
        str = f'critrate+{value}'
    elif name == '暴击伤害':
        str = f'critdmg+{value}'
    elif name == '元素精通':
        str = f'em+{value}'
    elif name == '元素充能效率':
        str = f'ce+{value}'
    elif name == '物理伤害加成':
        str = f'physicalDmgBonus+{value}'
    elif '元素伤害加成' in name:
        str = f'dmgBonus+{value}'
    return str
