import re
import sys
from pathlib import Path
from typing import Dict, Union, Optional

sys.path.append(str(Path(__file__).parents[1]))
try:
    from ...utils.ambr_api.prop_map import PROP_MAP
    from ...utils.ambr_api.get_ambr_data import get_char_data, get_weapon_data
    from ...utils.ambr_api.grow_curve import GROW_CURVE_LIST, WEAPON_GROW_CURVE
except ImportError:
    from utils.ambr_api.prop_map import PROP_MAP
    from utils.ambr_api.get_ambr_data import get_char_data, get_weapon_data
    from utils.ambr_api.grow_curve import GROW_CURVE_LIST, WEAPON_GROW_CURVE

ELEMENT_MAP = {
    'Wind': '风',
    'Ice': '冰',
    'Grass': '草',
    'Water': '水',
    'Electric': '雷',
    'Rock': '岩',
    'Fire': '火',
}

TYPE_TO_INT = {
    'GROW_CURVE_HP_S4': 0,
    'GROW_CURVE_ATTACK_S4': 1,
    'GROW_CURVE_HP_S5': 2,
    'GROW_CURVE_ATTACK_S5': 3,
}

WEAPON_TYPE = {
    'WEAPON_SWORD_ONE_HAND': '单手剑',
    'WEAPON_CATALYST': '法器',
    'WEAPON_CLAYMORE': '双手剑',
    'WEAPON_BOW': '弓',
    'WEAPON_POLE': '长柄武器',
}


async def convert_ambr_to_weapon(weapon_id: Union[int, str]):
    raw_data = await get_weapon_data(weapon_id)
    if 'code' in raw_data:
        return None
    raw_data = raw_data['data']
    effect = list(raw_data['affix'].values())[0]
    effect_name = effect['name']
    effect_up = effect['upgrade']
    upgrade = raw_data['upgrade']
    baseatk = upgrade['prop'][0]['initValue']
    basesp = upgrade['prop'][-1]['initValue']
    result = {
        'name': raw_data['name'],
        'weapontype': raw_data['type'],
        'rarity': str(raw_data['rank']),
        'baseatk': baseatk,
        'substat': PROP_MAP[upgrade['prop'][1]['propType']],
        'effectname': effect_name,
        'level': 90,
        'ascension': 6,
    }
    for index, affix in enumerate(effect_up):
        effect_value = re.findall(
            r'<c[^\u4e00-\u9fa5]+>\d+?.?\d+[^\u4e00-\u9fa5]+r>',
            effect_up[affix],
        )
        attr_list = []
        if index == 0:
            result['effect'] = effect_up[affix]
        for i, v in enumerate(effect_value):
            if index == 0:
                result['effect'] = result['effect'].replace(v, f'{{{i}}}')
            r = re.search(r'>([0-9/.%]+)', v)
            if r:
                attr_list.append(r.group(1))
        result[f'r{index+1}'] = attr_list
    atk_curve_type = upgrade['prop'][0]['type']
    sp_curve_type = upgrade['prop'][1]['type']
    atk_curve = WEAPON_GROW_CURVE['90']['curveInfos'][atk_curve_type]
    sp_curve = WEAPON_GROW_CURVE['90']['curveInfos'][sp_curve_type]
    atk_promoto = upgrade['promote'][-1]['addProps']['FIGHT_PROP_BASE_ATTACK']
    result['attack'] = atk_curve * baseatk + atk_promoto
    result['specialized'] = sp_curve * basesp
    return result


async def convert_ambr_to_minigg(char_id: Union[str, int]) -> Optional[Dict]:
    raw_data = await get_char_data(char_id)
    if 'code' in raw_data:
        return None
    raw_data = raw_data['data']
    result = {
        'name': raw_data['name'],
        'title': raw_data['fetter']['title'],
        'rarity': raw_data['rank'],
        'weapontype': WEAPON_TYPE[raw_data['weaponType']],
        'element': ELEMENT_MAP[raw_data['element']],
        'images': {'namesideicon': raw_data['icon']},  # 暂时适配
        'substat': PROP_MAP[
            list(raw_data['upgrade']['promote'][-1]['addProps'].keys())[-1]
        ],
        'hp': raw_data['upgrade']['prop'][0]['initValue']
        * GROW_CURVE_LIST[89]['curveInfos'][
            TYPE_TO_INT[raw_data['upgrade']['prop'][0]['type']]
        ]['value']
        + raw_data['upgrade']['promote'][-1]['addProps']['FIGHT_PROP_BASE_HP'],
        'attack': raw_data['upgrade']['prop'][1]['initValue']
        * GROW_CURVE_LIST[89]['curveInfos'][
            TYPE_TO_INT[raw_data['upgrade']['prop'][1]['type']]
        ]['value']
        + raw_data['upgrade']['promote'][-1]['addProps'][
            'FIGHT_PROP_BASE_ATTACK'
        ],
        'defense': raw_data['upgrade']['prop'][2]['initValue']
        * GROW_CURVE_LIST[89]['curveInfos'][
            TYPE_TO_INT[raw_data['upgrade']['prop'][2]['type']]
        ]['value']
        + raw_data['upgrade']['promote'][-1]['addProps'][
            'FIGHT_PROP_BASE_DEFENSE'
        ],
        'specialized': raw_data['upgrade']['promote'][-1]['addProps'][
            list(raw_data['upgrade']['promote'][-1]['addProps'].keys())[-1]
        ],
    }
    return result


async def convert_ambr_to_talent(char_id: Union[str, int]) -> Optional[Dict]:
    raw_data = await get_char_data(char_id)
    if 'code' in raw_data:
        return None
    raw_data = raw_data['data']
    talent_data = raw_data['talent']
    result = {}
    if '7' in talent_data:
        num = ['0', '1', '4']
    else:
        num = ['0', '1', '3']
    for index, i in enumerate(num):
        result[f'combat{index+1}'] = {
            'name': talent_data[i]['name'],
            'info': talent_data[i]['description'],
            'attributes': {
                'labels': [],
                'parameters': {},
            },
        }
        label_str = ''
        for label in talent_data[i]['promote']['1']['description']:
            if label:
                label_str += label
                result[f'combat{index+1}']['attributes']['labels'].append(
                    label
                )
        para_list = re.findall(r'{(param[0-9]+):', label_str)

        # 进行排序
        nums = [
            i
            for i in sorted(
                [
                    int(i[-2:]) if i[-2].isdigit() else int(i[-1])
                    for i in para_list
                ]
            )
        ]

        num_temp = 0
        new_nums = []
        for num in nums:
            if num != num_temp + 1:
                new_nums.append(num_temp + 1)
            num_temp = num
            new_nums.append(num)

        new_para_list = [f'param{i}' for i in new_nums]

        for ig, para in enumerate(new_para_list):
            for level in talent_data[i]['promote']:
                if (
                    para
                    not in result[f'combat{index+1}']['attributes'][
                        'parameters'
                    ]
                ):
                    result[f'combat{index+1}']['attributes']['parameters'][
                        para
                    ] = []
                result[f'combat{index+1}']['attributes']['parameters'][
                    para
                ].append(talent_data[i]['promote'][level]['params'][ig])
    return result
