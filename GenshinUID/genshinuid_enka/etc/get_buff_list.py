from typing import List, Literal

from ..etc.base_info import ELEMENT_MAP
from .MAP_PATH import char_effect_map, weapon_effect_map, artifact_effect_map


async def get_buff_list(
    raw_data: dict,
    type: Literal['group', 'normal', 'fight'],
    with_talent: bool = True,
) -> List[str]:
    all_effect: List[str] = []

    # 获取初始数据
    char_name = raw_data['avatarName']
    # 处理旅行者
    if char_name == '旅行者':
        for element in ELEMENT_MAP:
            if raw_data['avatarElement'] == ELEMENT_MAP[element]:
                char_name += f'({element})'
                break
    char_level = int(raw_data['avatarLevel'])
    weaponName = raw_data['weaponInfo']['weaponName']
    weaponAffix = raw_data['weaponInfo']['weaponAffix']

    main = type
    if type == 'group':
        main = 'fight'

    # 计算武器效果
    WEM = weapon_effect_map[weaponName]
    weapon_effet = WEM[main][f'{type}_effect'][str(weaponAffix)]
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
        all_effect.append(
            artifact_effect_map[equipSets['set']][f'{type}_effect']['2']
        )
        all_effect.append(
            artifact_effect_map[equipSets['set']][f'{type}_effect']['4']
        )
    elif equipSets['type'] == '2':
        all_effect.append(
            artifact_effect_map[equipSets['set']][f'{type}_effect']['2']
        )
    elif equipSets['type'] == '22':
        if equipSets['set'][-2] == '之':
            e = equipSets['set'][-3:]
        else:
            e = equipSets['set'][-2:]

        if equipSets['set'][2] == '之':
            t = equipSets['set'][:3]
        else:
            t = equipSets['set'][:2]

        for i in artifact_effect_map:
            if i.startswith(t):
                all_effect.extend(
                    artifact_effect_map[i][f'{type}_effect']['2'].split(';')
                )
            elif i.endswith(e):
                all_effect.extend(
                    artifact_effect_map[i][f'{type}_effect']['2'].split(';')
                )

    # 计算技能buff
    if char_name in char_effect_map:
        if with_talent:
            for talent in char_effect_map[char_name][main][f'{type}_talent']:
                if len(raw_data['talentList']) >= int(talent):
                    all_effect.append(
                        char_effect_map[char_name][main][f'{type}_talent'][
                            talent
                        ]
                    )
        # 计算角色buff
        for skill in char_effect_map[char_name][main][f'{type}_skill']:
            if char_level >= int(skill):
                all_effect.append(
                    char_effect_map[char_name][main][f'{type}_skill'][skill]
                )

    return all_effect
