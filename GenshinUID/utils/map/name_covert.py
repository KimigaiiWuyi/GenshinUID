from typing import Dict, Optional

from .GS_MAP_PATH import (
    alias_data,
    avatarId2Name,
    avatarId2Star_data,
    avatarName2Element,
    weaponId2Name_data,
    avatarId2SkillList_data,
    enName_to_avatarId_data,
)


async def weapon_id_to_name(weapon_id: str) -> str:
    if weapon_id in weaponId2Name_data:
        return weaponId2Name_data[weapon_id]
    else:
        return '未知'


async def name_to_weapon_id(weapon_name: str) -> str:
    for _id in weaponId2Name_data:
        if weapon_name == weaponId2Name_data[_id]:
            return _id
    else:
        return '11509'


async def avatar_id_to_skill_groupId(
    avatar_id: str,
) -> Optional[Dict[str, str]]:
    if avatar_id in avatarId2SkillList_data:
        return avatarId2SkillList_data[avatar_id]
    else:
        return None


async def name_to_element(name: str) -> str:
    if name in avatarName2Element:
        return avatarName2Element[name]
    else:
        return 'Cryo'


async def avatar_id_to_name(avatar_id: str) -> str:
    char_name = avatarId2Name[avatar_id]
    return char_name


async def name_to_avatar_id(name: str) -> str:
    avatar_id = ''
    for i in avatarId2Name:
        if avatarId2Name[i] == name:
            avatar_id = i
            break
    return avatar_id


async def avatar_id_to_char_star(char_id: str) -> str:
    char_star = avatarId2Star_data[str(char_id)]
    return char_star


async def alias_to_char_name(char_name: str) -> str:
    for i in alias_data:
        if (char_name in i) or (char_name in alias_data[i]):
            return i
    return char_name


async def enName_to_avatarId(en_name: str) -> str:
    avatar_id = enName_to_avatarId_data[en_name]
    return avatar_id


async def avatarId_to_enName(avatarId: str) -> str:
    for name in enName_to_avatarId_data:
        if enName_to_avatarId_data[name] == avatarId:
            return name
    else:
        return 'Ayaka'
