import json
from pathlib import Path

with open(
    Path(__file__).parent / 'char_alias.json', 'r', encoding='utf8'
) as fp:
    char_alias_data = json.load(fp)


async def alias_to_char_name(char_name: str) -> str:
    for i in char_alias_data:
        if (char_name in i) or (char_name in char_alias_data[i]):
            return i
    return char_name
