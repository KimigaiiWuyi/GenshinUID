from typing import Dict, List, Union

import httpx
from bs4 import BeautifulSoup, NavigableString

from .hhw_api import HHW_ABYSS


async def get_abyss_review(
    raw_data: bytes, _id: Union[str, int], floor: Union[str, int]
) -> Dict[str, List[str]]:
    bs = BeautifulSoup(raw_data, 'lxml')
    data = bs.find('section', {'id': f'Variant #{_id}'})

    if data is None or isinstance(data, NavigableString):
        return {}

    floor_data = data.find_all('td')
    abyss_list = []
    result = {}
    for index, td in enumerate(floor_data):
        temp = []
        if 'Monsters' in td.text:
            monsters = floor_data[index + 1].find_all('a')
            for monster in monsters:
                if monster.text:
                    temp.append(monster.text)
            if temp:
                abyss_list.append(temp)

    for index, half in enumerate(['-1上', '-1下', '-2上', '-2下', '-3上', '-3下']):
        result[f'{floor}{half}'] = abyss_list[index]

    return result


async def get_hhw_abyss_raw() -> bytes:
    raw_data = httpx.get(HHW_ABYSS)
    raw_data = raw_data.read()
    return raw_data
