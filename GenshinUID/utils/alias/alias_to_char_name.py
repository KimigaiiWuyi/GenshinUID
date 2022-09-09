import json
from pathlib import Path

with open(
    Path(__file__).parent / 'char_alias.json', 'r', encoding='utf8'
) as fp:
    char_alias_data = json.load(fp)


async def alias_to_char_name(char_name: str) -> str:
    for i in char_alias_data:
        if char_name in i:
            char_name = i
        else:
            for k in char_alias_data[i]:
                if char_name in k:
                    char_name = i
    return char_name
