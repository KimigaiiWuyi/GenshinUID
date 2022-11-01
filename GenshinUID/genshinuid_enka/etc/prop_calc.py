from copy import deepcopy
from typing import List, Optional

from .buff_calc import get_effect_prop
from ..etc.get_buff_list import get_buff_list
from .MAP_PATH import char_effect_map, weapon_effect_map, artifact_effect_map
from ...utils.minigg_api.get_minigg_data import get_char_info, get_weapon_info

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

ATTR_MAP = {
    '元素精通': 'elementalMastery',
    '物理伤害加成': 'physicalDmgBonus',
    '元素伤害加成': 'dmgBonus',
    '充能效率': 'energyRecharge',
    '暴击伤害': 'critDmg',
    '暴击率': 'critRate',
    '攻击力': 'addAtk',
    '防御力': 'addDef',
    '生命值': 'addHp',
    '百分比血量': 'addHp',
}


async def get_card_prop(
    raw_data: dict,
    weapon: Optional[str] = None,
    weapon_affix: Optional[int] = None,
    talent_num: Optional[int] = None,
) -> dict:
    char_name = raw_data['avatarName']
    char_level = int(raw_data['avatarLevel'])

    # 创造一个假武器
    if weapon:
        weapon_info = deepcopy(baseWeaponInfo)
        weapon_raw_data = await get_weapon_info(weapon)
        if 'errcode' in weapon_raw_data:
            return {}
        weapon_info['weaponStar'] = int(weapon_raw_data['rarity'])
        if weapon_info['weaponStar'] >= 3:
            weapon_level_data = await get_weapon_info(weapon, '90')
            weapon_info['weaponLevel'] = 90
            weapon_info['promoteLevel'] = 6
        else:
            weapon_level_data = await get_weapon_info(weapon, '70')
            weapon_info['weaponLevel'] = 70
            weapon_info['promoteLevel'] = 4
        weapon_info['weaponName'] = weapon_raw_data['name']
        if weapon_affix is None:
            if weapon_info['weaponStar'] >= 5:
                weapon_info['weaponAffix'] = 1
            else:
                weapon_info['weaponAffix'] = 5
        else:
            weapon_info['weaponAffix'] = weapon_affix
        weapon_info['weaponStats'][0]['statValue'] = round(
            weapon_level_data['attack']
        )
        if weapon_raw_data['substat'] != '':
            weapon_info['weaponStats'][1]['statName'] = weapon_raw_data[
                'substat'
            ]
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
        weapon_info['weaponType'] = weapon_raw_data['weapontype']
        raw_data['weaponInfo'] = weapon_info

    # 修改假命座:
    if talent_num:
        talent_list = []
        for i in range(1, talent_num + 1):
            talent_list.append(
                {
                    'talentId': 300 + i,
                    'talentName': f'FakeTalent{i}',
                    'talentIcon': f'UI_Talent_S_{raw_data["avatarEnName"]}_0{i}',
                }
            )
        raw_data['talentList'] = talent_list

    # 武器基本属
    weapon_affix = raw_data['weaponInfo']['weaponAffix']
    weapon_atk = raw_data['weaponInfo']['weaponStats'][0]['statValue']
    if len(raw_data['weaponInfo']['weaponStats']) > 1:
        weapon_sub = raw_data['weaponInfo']['weaponStats'][1]['statName']
        weapon_sub_val = raw_data['weaponInfo']['weaponStats'][1]['statValue']
    else:
        weapon_sub = ''
        weapon_sub_val = 0

    fight_prop = deepcopy(baseFightProp)
    if '珊瑚宫心海' == char_name:
        fight_prop['critRate'] -= 1.0
        fight_prop['healBonus'] += 0.25

    char_name_covert = char_name
    if char_name == '旅行者':
        char_name_covert = '荧'

    char_raw = await get_char_info(name=char_name_covert, mode='char')
    char_data = await get_char_info(
        name=char_name_covert, mode='char', level=str(char_level)
    )
    if char_data is None or isinstance(char_data, List):
        return {}

    fight_prop['baseHp'] = char_data['hp']
    fight_prop['baseAtk'] = char_data['attack'] + weapon_atk
    fight_prop['baseDef'] = char_data['defense']
    fight_prop['exHp'] = 0
    fight_prop['exAtk'] = 0
    fight_prop['exDef'] = 0

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

    raw_data['avatarFightProp'] = fight_prop
    all_effects = await get_buff_list(raw_data, 'normal')

    # 计算圣遗物效果
    for equip in raw_data['equipList']:
        statNmae = equip['reliquaryMainstat']['statName']
        statValue = equip['reliquaryMainstat']['statValue']
        all_effects.append(await text_to_effect(statNmae, statValue))
        for sub in equip['reliquarySubstats']:
            sub_name = sub['statName']
            sub_value = sub['statValue']
            all_effects.append(await text_to_effect(sub_name, sub_value))

    fight_prop = await get_effect_prop(fight_prop, all_effects, char_name)
    raw_data['avatarFightProp'] = fight_prop
    return raw_data


ELEMENT_MAP = {
    '风': 'Anemo',
    '冰': 'Cryo',
    '草': 'Dendro',
    '雷': 'Electro',
    '岩': 'Geo',
    '水': 'Hydro',
    '火': 'Pyro',
}


async def text_to_effect(name: str, value: float) -> str:
    str = ''
    if name == '血量':
        str = f'exHp+{value}'
    elif name == '百分比血量':
        str = f'addHp+{value}'
    elif name == '攻击力':
        str = f'exAtk+{value}'
    elif name == '百分比攻击力':
        str = f'addAtk+{value}'
    elif name == '防御力':
        str = f'exDef+{value}'
    elif name == '百分比防御力':
        str = f'addDef+{value}'
    elif name == '暴击率':
        str = f'critRate+{value}'
    elif name == '暴击伤害':
        str = f'critDmg+{value}'
    elif name == '元素精通':
        str = f'elementalMastery+{value}'
    elif name == '元素充能效率':
        str = f'energyRecharge+{value}'
    elif name == '物理伤害加成':
        str = f'physicalDmgBonus+{value}'
    elif '元素伤害加成' in name:
        str = f'{ELEMENT_MAP[name[0]]}DmgBonus+{value}'
    return str
