import json
from pathlib import Path

with open(
    Path(__file__).parent / 'enName2AvatarID.json', 'r', encoding='utf8'
) as fp:
    enName_to_avatarId_data = json.load(fp)


async def enName_to_avatarId(en_name: str) -> str:
    avatar_id = enName_to_avatarId_data[en_name]
    return avatar_id
