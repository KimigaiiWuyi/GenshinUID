import json
from pathlib import Path

with open(
    Path(__file__).parent / 'avatarId2Name.json', 'r', encoding='utf8'
) as fp:
    char_id_data = json.load(fp)


async def avatar_id_to_name(avatar_id: str) -> str:
    """
    :说明:
      接受角色ID转换为角色名称
    :参数:
      * avatar_id (str): 角色ID。
    :返回:
      * name (str): 角色名称。
    """
    char_name = char_id_data[avatar_id]
    return char_name


async def name_to_avatar_id(name: str) -> str:
    """
    :说明:
      接受角色名称转换为角色ID
    :参数:
      * name (str): 角色名称。
    :返回:
      * avatar_id (str): 角色ID。
    """
    avatar_id = ''
    for i in char_id_data:
        if char_id_data[i] == name:
            avatar_id = i
            break
    return avatar_id
