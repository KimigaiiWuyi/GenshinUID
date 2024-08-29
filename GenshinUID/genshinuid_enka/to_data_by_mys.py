import json
from datetime import datetime
from typing import Dict, List, Tuple, Union

import aiofiles
from gsuid_core.utils.error_reply import get_error

from .to_card import pic_500, draw_enka_card
from ..utils.image.convert import convert_img
from .etc.MAP_PATH import avatarName2SkillAdd
from ..utils.mys_api import mys_api, get_base_data
from ..utils.map.name_covert import avatarId_to_enName
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.map.GS_MAP_PATH import (
    Id2PropId,
    name2Icon,
    propId2Name,
    skillId2Name,
    talentId2Name,
)

elementMap = {
    'Anemo': 44,
    'Geo': 45,
    'Dendro': 43,
    'Pyro': 40,
    'Hydro': 42,
    'Cryo': 46,
    'Electro': 41,
}

posMap = {
    '空之杯': 'goblet',
    '死之羽': 'plume',
    '理之冠': 'circlet',
    '生之花': 'flower',
    '时之沙': 'sands',
}


def get_value(value: str):
    if not value:
        return 0
    return float(value.replace('%', ''))


async def mys_to_data(uid: str):
    path = PLAYER_PATH / uid
    path.mkdir(parents=True, exist_ok=True)

    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    char_data = raw_data['avatars']
    char_ids = []
    for i in char_data:
        char_ids.append(i['id'])
    data = await mys_api.get_char_detail_data(uid, char_ids)
    if isinstance(data, int):
        return get_error(data)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    skill_icon_map = skillId2Name['Icon']
    talent_icon_map = talentId2Name['Icon']

    char_dict_list = []
    for char in data:
        base = char['base']
        avatar_name = base['name']
        avatar_id = base['id']
        en_name = await avatarId_to_enName(str(avatar_id))

        avatar_skill = []
        avatar_talent = []
        avatar_fight_prop = {}
        weapon_info = {}

        for talent in char['constellations']:
            if talent['is_actived']:
                talent_id = talent['id']
                avatar_talent.append(
                    {
                        'talentId': talent_id,
                        'talentName': talent['name'],
                        'talentIcon': talent_icon_map[str(talent_id)],
                    }
                )

        if avatar_name in avatarName2SkillAdd:
            skill_add = avatarName2SkillAdd[avatar_name]
        else:
            skill_add = ['E', 'Q']

        a_skill_level, e_skill_level, q_skill_level = 0, 0, 0
        for skillAdd_index in range(0, 2):
            if len(avatar_talent) >= 3 + skillAdd_index * 2:
                if skill_add[skillAdd_index] == 'E':
                    e_skill_level = 3
                elif skill_add[skillAdd_index] == 'Q':
                    q_skill_level = 3
                elif skill_add[skillAdd_index] == 'A':
                    a_skill_level = 3

        n = 0
        for skill in char['skills']:
            skill_id = str(skill['skill_id'])
            if len(skill_id) <= 4:
                continue

            if skill_id not in skill_icon_map:
                continue

            skill_icon = skill_icon_map[skill_id]
            if skill_id.endswith('3') and skill_icon.endswith('2'):
                continue

            n += 1
            skill_level = skill['level']

            if n == 1:
                skill_level -= a_skill_level
            elif n == 2:
                skill_level -= e_skill_level
            elif n == 3:
                skill_level -= q_skill_level

            avatar_skill.append(
                {
                    'skillId': skill_id,
                    'skillName': skill['name'],
                    'skillLevel': skill_level,
                    'skillIcon': skill_icon,
                }
            )

        weapon = char['weapon']
        weapon_main = weapon['main_property']
        main_prop_id = Id2PropId[str(weapon_main['property_type'])]
        weaponStats = [
            {
                'appendPropId': main_prop_id,
                'statName': propId2Name[main_prop_id],
                'statValue': get_value(weapon_main['final']),
            }
        ]
        weapon_sub = weapon['sub_property']
        if weapon_sub:
            sub_prop_id = Id2PropId[str(weapon_sub['property_type'])]
            weaponStats.append(
                {
                    'appendPropId': sub_prop_id,
                    'statName': propId2Name[sub_prop_id],
                    'statValue': get_value(weapon_sub['final']),
                }
            )

        weapon_info = {
            'itemId': weapon['id'],
            'nameTextMapHash': '807607555',
            'weaponIcon': 'UI_EquipIcon_Catalyst_Dvalin',
            'weaponType': weapon['type_name'],
            'weaponName': weapon['name'],
            'weaponStar': weapon['rarity'],
            'promoteLevel': 1,
            'weaponLevel': weapon['level'],
            'weaponAffix': weapon['affix_level'],
            'weaponStats': weaponStats,
            'weaponEffect': weapon['desc'],
        }
        all_prop = (
            char['base_properties']
            + char['extra_properties']
            + char['element_properties']
        )

        element_id = elementMap.get(base['element'], 41)
        for prop in all_prop:
            prop_id = prop['property_type']
            if prop_id == 2000:
                avatar_fight_prop['baseHp'] = get_value(prop['base'])
                avatar_fight_prop['addHp'] = get_value(prop['add'])
                avatar_fight_prop['hp'] = get_value(prop['final'])
            elif prop_id == 2001:
                avatar_fight_prop['baseAtk'] = get_value(prop['base'])
                avatar_fight_prop['addAtk'] = get_value(prop['add'])
                avatar_fight_prop['atk'] = get_value(prop['final'])
            elif prop_id == 2002:
                avatar_fight_prop['baseDef'] = get_value(prop['base'])
                avatar_fight_prop['addDef'] = get_value(prop['add'])
                avatar_fight_prop['def'] = get_value(prop['final'])
            elif prop_id == 28:
                avatar_fight_prop['elementalMastery'] = get_value(
                    prop['final']
                )
            elif prop_id == 20:
                avatar_fight_prop['critRate'] = get_value(prop['final'])
            elif prop_id == 22:
                avatar_fight_prop['critDmg'] = get_value(prop['final'])
            elif prop_id == 23:
                avatar_fight_prop['energyRecharge'] = get_value(prop['final'])
            elif prop_id == 26:
                avatar_fight_prop['healBonus'] = get_value(prop['final'])
            elif prop_id == 27:
                avatar_fight_prop['healedBonus'] = get_value(prop['final'])
            elif prop_id == 30:
                avatar_fight_prop['physicalDmgBonus'] = get_value(
                    prop['final']
                )
            elif prop_id == element_id:
                avatar_fight_prop['dmgBonus'] = get_value(prop['final']) / 100

        avatar_fight_prop['physicalDmgSub'] = 0

        relic_list = []
        artifact_set_list = []
        for relic in char['relics']:
            main_prop = relic['main_property']
            main_prop_id = Id2PropId[str(main_prop['property_type'])]

            sub_prop = relic['sub_property_list']
            reliquarySubstats = []
            for su in sub_prop:
                sub_prop_id = Id2PropId[str(su['property_type'])]
                reliquarySubstats.append(
                    {
                        'appendPropId': sub_prop_id,
                        'statName': propId2Name[sub_prop_id],
                        'statValue': get_value(su['value']),
                    }
                )

            artifact_set_list.append(relic['set']['name'])
            relic_list.append(
                {
                    'itemId': relic['id'],
                    'nameTextMapHash': '2007346252',
                    'icon': name2Icon[relic['name']],
                    'aritifactName': relic['name'],
                    'aritifactSetsName': relic['set']['name'],
                    'aritifactSetPiece': posMap[relic['pos_name']],
                    'aritifactPieceName': relic['pos_name'],
                    'aritifactStar': relic['rarity'],
                    'aritifactLevel': relic['level'],
                    'reliquaryMainstat': {
                        'mainPropId': main_prop_id,
                        'statValue': get_value(main_prop['value']),
                        'statName': propId2Name[main_prop_id],
                    },
                    'reliquarySubstats': reliquarySubstats,
                }
            )

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

        result = {
            'playerUid': uid,
            'playerName': raw_data['role']['nickname'],
            'avatarId': avatar_id,
            'avatarName': avatar_name,
            'avatarFetter': base['fetter'],
            'avatarLevel': str(base['level']),
            'avatarElement': base['element'],
            'dataTime': now,
            'avatarEnName': en_name,
            'avatarSkill': avatar_skill,
            'talentList': avatar_talent,
            'weaponInfo': weapon_info,
            'avatarFightProp': avatar_fight_prop,
            'equipSets': equipSets,
            'equipList': relic_list,
        }

        char_dict_list.append(result)
        async with aiofiles.open(
            path / f'{avatar_name}.json', 'w', encoding='UTF-8'
        ) as file:
            await file.write(json.dumps(result, indent=4, ensure_ascii=False))

    return char_dict_list


async def mys_to_card(uid: str) -> Union[str, bytes, Tuple[bytes, List[Dict]]]:
    char_data_list = await mys_to_data(uid)
    if char_data_list == []:
        return await convert_img(pic_500)
    elif isinstance(char_data_list, str):
        return char_data_list
    elif isinstance(char_data_list, bytes):
        return char_data_list

    img = await draw_enka_card(uid=uid, char_data_list=char_data_list)
    return img, char_data_list
    return img, char_data_list
