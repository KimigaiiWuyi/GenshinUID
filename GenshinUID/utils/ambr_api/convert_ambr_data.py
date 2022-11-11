import re
import sys
from pathlib import Path
from typing import Dict, Union, Optional

sys.path.append(str(Path(__file__).parents[1]))
try:
    from ...utils.ambr_api.prop_map import PROP_MAP
    from ...utils.ambr_api.grow_curve import GROW_CURVE_LIST
    from ...utils.ambr_api.get_ambr_data import get_char_data
except ImportError:
    from utils.ambr_api.prop_map import PROP_MAP
    from utils.ambr_api.grow_curve import GROW_CURVE_LIST
    from utils.ambr_api.get_ambr_data import get_char_data

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
        for ig, para in enumerate(para_list):
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
