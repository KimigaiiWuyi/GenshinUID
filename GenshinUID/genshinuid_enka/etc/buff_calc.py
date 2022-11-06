from typing import List
from copy import deepcopy

from ...utils.enka_api.map.GS_MAP_PATH import (
    avatarName2Weapon,
    avatarName2Element,
)

PERCENT_ATTR = ['dmgBonus', 'addAtk', 'addDef', 'addHp']


async def get_effect_prop(
    prop: dict,
    effect_list: List[str],
    char_name: str,
) -> dict:
    if 'A_d' not in prop:
        for attr in [
            'shieldBonus',
            'addDmg',
            'addHeal',
            'ignoreDef',
            'd',
            'g',
            'a',
        ]:
            prop[attr] = 0
        prop['r'] = 0.1
        prop['k'] = 1
        prop['sp'] = []
        if prop['baseHp'] + prop['addHp'] == prop['hp']:
            prop['exHp'] = prop['addHp']
            prop['exAtk'] = prop['addAtk']
            prop['exDef'] = prop['addDef']
            prop['addHp'] = 0
            prop['addAtk'] = 0
            prop['addDef'] = 0

        # 给每个技能 分别添加上属性
        for prop_attr in deepcopy(prop):
            for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
                prop[f'{prop_limit}_{prop_attr}'] = prop[prop_attr]

        weapon_type = avatarName2Weapon[char_name]

        # 计算角色伤害加成应该使用什么
        for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
            if weapon_type == '法器' or char_name in [
                '荒泷一斗',
                '刻晴',
                '诺艾尔',
                '胡桃',
                '宵宫',
                '魈',
                '神里绫华',
            ]:
                prop['{}_dmgBonus'.format(prop_limit)] = prop['dmgBonus']
            elif weapon_type == '弓':
                if prop_limit in ['A', 'C']:
                    prop['{}_dmgBonus'.format(prop_limit)] = prop[
                        'physicalDmgBonus'
                    ]
                elif prop_limit in ['B', 'E', 'Q']:
                    prop['{}_dmgBonus'.format(prop_limit)] = prop['dmgBonus']
            else:
                if prop_limit in ['A', 'B', 'C']:
                    prop['{}_dmgBonus'.format(prop_limit)] = prop[
                        'physicalDmgBonus'
                    ]
                elif prop_limit in ['E', 'Q']:
                    prop['{}_dmgBonus'.format(prop_limit)] = prop['dmgBonus']

    # 防止复数效果
    with_trans_effect: List[str] = []
    without_trans_effect: List[str] = []
    for effect in effect_list:
        if ';' in effect:
            effect = effect.split(';')
        else:
            effect = [effect]

        for _effect in effect:
            if _effect == '':
                continue
            else:
                if '%' in _effect:
                    with_trans_effect.append(_effect)
                else:
                    without_trans_effect.append(_effect)

    new_effect_list: List[str] = without_trans_effect + with_trans_effect

    # 正式开始计算
    for effect in new_effect_list:
        # 分割效果
        # 例如:Q:dmgBonus+96%27%em
        # 分割后:
        # effect_limit = Q
        effect_limit = ''
        if ':' in effect:
            effect_limit = effect.split(':')[0]
            effect = effect.split(':')[1]

        effect_attr, effect_value = effect.split('+')
        effect_max = 9999999
        effect_base: str = ''

        # 判断effect_value中有几个百分号
        p_count = effect_value.count('%')
        # 如果有%,则认为是基于值的提升
        base_check = True
        if p_count >= 2:
            effect_max, effect_value, effect_base = effect_value.split('%')
        elif p_count == 1:
            effect_value, effect_base = effect_value.split('%')
        else:
            base_check = False

        # effect_attr, effect_value, effect_base, effect_max
        # dmgBonus, 27, em, 96

        # 暂时不处理extraDmg
        if effect_attr == 'extraDmg':
            continue

        effect_max = float(effect_max) / 100
        # 如果要增加的属性不是em元素精通,那么都要除于100
        if effect_attr not in ['exHp', 'exAtk', 'exDef', 'elementalMastery']:
            # 正常除100
            effect_value = float(effect_value) / 100
        # 元素精通则为正常值
        else:
            if effect_base in ['hp', 'elementalMastery', 'def']:
                effect_value = float(effect_value) / 100
            else:
                effect_value = float(effect_value)

        # 如果属性是血量,攻击,防御值,并且是按照%增加的,那么增加值应为百分比乘上基础值
        if base_check:
            if effect_base == 'energyRecharge':
                if effect_attr in PERCENT_ATTR:
                    effect_base_value = prop[effect_base] - 1
                else:
                    effect_base_value = (prop[effect_base] - 1) / 100

                # 针对莫娜的
                if char_name == '莫娜':
                    effect_base_value += 1
            elif effect_base == 'elementalMastery':
                # 针对草神的
                if char_name == '纳西妲' and effect_attr == 'dmgBonus':
                    effect_base_value = (prop[effect_base] - 200) / 100
                else:
                    effect_base_value = prop[effect_base]
            else:
                effect_base_value = prop[effect_base]
            effect_value = effect_value * effect_base_value

        # 判断是否超过上限,超过则使用上限值
        if effect_value >= effect_max:
            effect_value = effect_max

        if char_name == '旅行者':
            char_element = 'Hydro'
        else:
            char_element = avatarName2Element[char_name]

        # 判断是否是自己属性的叠加
        if 'DmgBonus' in effect_attr:
            if effect_attr.replace('DmgBonus', '') == char_element:
                effect_attr = 'dmgBonus'
            else:
                continue

        # 如果效果有限制条件
        if effect_limit:
            # 如果限制条件为中文,则为特殊label才生效
            if '\u4e00' <= effect_limit[-1] <= '\u9fff':
                prop['sp'].append(
                    {
                        'effect_name': effect_limit,
                        'effect_attr': effect_attr,
                        'effect_value': effect_value,
                    }
                )
            # 如果限制条件为英文,例如Q,则为Q才生效
            else:
                # 形如ABC:dmgBonus+75,则遍历ABC,增加值
                for limit in effect_limit:
                    prop['{}_{}'.format(limit, effect_attr)] += effect_value
        # 如果没有限制条件,直接增加
        else:
            if effect_attr in ['a', 'addDmg']:
                pass
            else:
                for attr in ['A', 'B', 'C', 'E', 'Q']:
                    prop[f'{attr}_{effect_attr}'] += effect_value
            prop[f'{effect_attr}'] += effect_value

    prop['hp'] = (prop['addHp'] + 1) * prop['baseHp'] + prop['exHp']
    prop['atk'] = (prop['addAtk'] + 1) * prop['baseAtk'] + prop['exAtk']
    prop['def'] = (prop['addDef'] + 1) * prop['baseDef'] + prop['exDef']
    for prop_limit in ['A', 'B', 'C', 'E', 'Q']:
        for attr in ['hp', 'atk', 'def']:
            attr_up = attr[0].upper() + attr[1:]
            prop[f'{prop_limit}_{attr}'] = (
                prop[f'{prop_limit}_add{attr_up}'] + 1
            ) * prop[f'base{attr_up}'] + prop[f'ex{attr_up}']
    return prop
