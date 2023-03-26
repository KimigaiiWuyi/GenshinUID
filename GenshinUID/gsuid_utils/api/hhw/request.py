'''
内鬼网(hhw) API 请求模块。
'''
from __future__ import annotations

from typing import Dict, Union, Optional

from httpx import AsyncClient
from bs4 import BeautifulSoup, NavigableString

from ...version import __version__

HHW_ABYSS = 'https://genshin.honeyhunterworld.com/d_1001/?lang=CHS'


async def get_abyss_review(
    raw_data: bytes, _id: Union[str, int], floor: Union[str, int]
) -> Optional[Dict[str, str]]:
    '''请求内鬼网 API 深渊怪物数据

    Returns:
        Dict: 内鬼网 API 深渊怪物数据
    '''  # noqa: E501
    bs = BeautifulSoup(raw_data, 'lxml')
    data = bs.find('section', {'id': f'Variant #{_id}'})

    if data is None or isinstance(data, NavigableString):
        return None

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


async def get_abyss_review_raw() -> bytes:
    async with AsyncClient(
        headers={'User-Agent': f'gsuid-utils/{__version__}'}, timeout=None
    ) as client:
        req = await client.get(url=HHW_ABYSS)
        return req.read()
