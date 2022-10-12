import json
from pathlib import Path

from ...version import Genshin_version

avatarId2Star_fileName = f'avatarId2Star_mapping_{Genshin_version}.json'

with open(
    Path(__file__).parents[1] / 'enka_api' / 'map' / avatarId2Star_fileName,
    'r',
    encoding='utf8',
) as fp:
    avatarId2Star_data = json.load(fp)


async def avatar_id_to_char_star(char_id: str) -> str:
    char_star = avatarId2Star_data[str(char_id)]
    return char_star
