from typing import Dict, List, Union

from gsuid_core.logger import logger

from ..utils.map.GS_MAP_PATH import mysData, avatarName2Weapon
from ..utils.map.name_covert import (
    name_to_element,
    avatar_id_to_name,
    weapon_id_to_name,
    avatar_id_to_skill_groupId,
)

ELEMENT_MAP = {
    "Pyro": 1,
    "Anemo": 2,
    "Geo": 3,
    "Dendro": 4,
    "Electro": 5,
    "Hydro": 6,
    "Cryo": 7,
}


async def get_all_char_dict() -> List[Dict]:
    result = []
    weapon_list: Dict[str, List[str]] = {
        '单手剑': [],
        '双手剑': [],
        '弓': [],
        '法器': [],
        '长柄武器': [],
    }

    for weapon in mysData['data']['all_weapon']:
        weapon_id = str(weapon['id'])
        if int(weapon_id[2]) <= 3:
            continue

        if weapon_id.startswith('11'):
            weapon_list['单手剑'].append(weapon_id)
        elif weapon_id.startswith('12'):
            weapon_list['双手剑'].append(weapon_id)
        elif weapon_id.startswith('13'):
            weapon_list['长柄武器'].append(weapon_id)
        elif weapon_id.startswith('14'):
            weapon_list['法器'].append(weapon_id)
        elif weapon_id.startswith('15'):
            weapon_list['弓'].append(weapon_id)

    for char in mysData['data']['all_avatar']:
        char_id = str(char['id'])

        char_name = await avatar_id_to_name(char_id)
        if char_name not in avatarName2Weapon:
            continue
        char_weapon_type = avatarName2Weapon[char_name]
        if weapon_list[char_weapon_type]:
            weapon = weapon_list[char_weapon_type].pop()
        else:
            weapon = 0
        d = await char_id_to_compute_dict(
            char_id,
            weapon_id=weapon,
        )
        if d is not None:
            result.append(d)

    return result


async def char_id_to_compute_dict(
    char_id: Union[str, int],
    current_level: int = 1,
    target_level: int = 90,
    skill1_current_level: int = 1,
    skill1_target_level: int = 10,
    skill2_current_level: int = 1,
    skill2_target_level: int = 10,
    skill3_current_level: int = 1,
    skill3_target_level: int = 10,
    weapon_id: Union[str, int] = 0,
    weapon_current_level: int = 1,
    weapon_target_level: int = 90,
):
    char_id = str(char_id)
    char_name = await avatar_id_to_name(char_id)
    element = await name_to_element(char_name)
    element_id = ELEMENT_MAP[element]

    if char_id in ['10000005', '10000001', '10000007']:
        return None

    skill_list = await avatar_id_to_skill_groupId(char_id)
    if not skill_list:
        logger.debug(f'[char_id_to_compute_dict] {char_id}')
        raise ValueError("[char_id_to_compute_dict] 未找到该角色技能")

    skill_data = []
    skill_level = [
        [skill1_current_level, skill1_target_level],
        [skill2_current_level, skill2_target_level],
        [skill3_current_level, skill3_target_level],
    ]

    n = 0
    for skill_id in skill_list:
        if skill_id.endswith(('1', '2', '9')):
            skill_data.append(
                {
                    "id": skill_id,
                    "group_id": skill_id,
                    "name": skill_list[skill_id],
                    "max_level": 10,
                    "levelRange": skill_level[n],
                    "level_current": skill_level[n][0],
                    "level_target": skill_level[n][1],
                }
            )
            n += 1

    data = {
        "avatar_id": int(char_id),
        "avatar_level_current": current_level,
        "avatar_level_target": target_level,
        "element_attr_id": element_id,
        "level": 5,
        "name": char_name,
        "skill_list": skill_data,
    }

    if weapon_id != 0:
        data['weapon'] = {
            "id": int(weapon_id),
            "name": await weapon_id_to_name(str(weapon_id)),
            "weapon_cat_id": 1,
            "weapon_level": 5,
            "max_level": 90,
            "is_recommend": False,
            "levelRange": [weapon_current_level, weapon_target_level],
            "level_current": weapon_current_level,
            "level_target": weapon_target_level,
        }

    return data
