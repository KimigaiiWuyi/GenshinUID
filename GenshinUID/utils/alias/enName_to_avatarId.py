import json
from pathlib import Path

from ...version import Genshin_version

with open(
    Path(__file__).parents[1]
    / 'enka_api'
    / 'map'
    / f'enName2AvatarID_mapping_{Genshin_version}.json',
    'r',
    encoding='utf8',
) as fp:
    enName_to_avatarId_data = json.load(fp)


async def enName_to_avatarId(en_name: str) -> str:
    avatar_id = enName_to_avatarId_data[en_name]
    return avatar_id


async def avatarId_to_enName(avatarId: str) -> str:
    for name in enName_to_avatarId_data:
        if enName_to_avatarId_data[name] == avatarId:
            return name
    else:
        return 'Ayaka'
