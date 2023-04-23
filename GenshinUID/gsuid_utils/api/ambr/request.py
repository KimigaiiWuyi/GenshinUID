'''
安柏计划 API 请求模块。
'''
from __future__ import annotations

from typing import Dict, Union, Literal, Optional, cast

from httpx import AsyncClient

from ..types import AnyDict
from ...version import __version__
from .models import (
    AmbrBook,
    AmbrEvent,
    AmbrWeapon,
    AmbrGCGList,
    AmbrMonster,
    AmbrCharacter,
    AmbrGCGDetail,
    AmbrBookDetail,
    AmbrMonsterList,
)
from .api import (
    AMBR_BOOK_URL,
    AMBR_CHAR_URL,
    AMBR_EVENT_URL,
    AMBR_GCG_DETAIL,
    AMBR_WEAPON_URL,
    AMBR_MONSTER_URL,
    AMBR_GCG_LIST_URL,
    AMBR_MONSTER_LIST,
    AMBR_BOOK_DATA_URL,
    AMBR_BOOK_DETAILS_URL,
)

_HEADER = {'User-Agent': f'gsuid-utils/{__version__}'}


async def get_ambr_event_info() -> Optional[Dict[str, AmbrEvent]]:
    data = await _ambr_request(url=AMBR_EVENT_URL)
    if isinstance(data, Dict):
        return cast(Dict[str, AmbrEvent], data)
    return None


async def get_ambr_char_data(id: Union[int, str]) -> Optional[AmbrCharacter]:
    data = await _ambr_request(url=AMBR_CHAR_URL.format(id))
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrCharacter, data)
    return None


async def get_ambr_monster_data(id: Union[int, str]) -> Optional[AmbrMonster]:
    data = await _ambr_request(url=AMBR_MONSTER_URL.format(id))
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrMonster, data)
    return None


async def get_ambr_gcg_detail(id: Union[int, str]) -> Optional[AmbrGCGDetail]:
    data = await _ambr_request(url=AMBR_GCG_DETAIL.format(id))
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrGCGDetail, data)
    return None


async def get_ambr_gcg_list() -> Optional[AmbrGCGList]:
    data = await _ambr_request(url=AMBR_GCG_LIST_URL)
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrGCGList, data)
    return None


async def get_ambr_monster_list() -> Optional[AmbrMonsterList]:
    data = await _ambr_request(url=AMBR_MONSTER_LIST)
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrMonsterList, data)
    return None


async def get_ambr_weapon_data(id: Union[int, str]) -> Optional[AmbrWeapon]:
    data = await _ambr_request(url=AMBR_WEAPON_URL.format(id))
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrWeapon, data)
    return None


async def get_all_book_id() -> Optional[Dict[str, AmbrBook]]:
    data = await _ambr_request(url=AMBR_BOOK_URL)
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']['items']
        return cast(Dict[str, AmbrBook], data)
    return None


async def get_book_volume(id: Union[int, str]) -> Optional[AmbrBookDetail]:
    data = await _ambr_request(url=AMBR_BOOK_DETAILS_URL.format(id))
    if isinstance(data, Dict) and data['response'] == 200:
        data = data['data']
        return cast(AmbrBookDetail, data)
    return None


async def get_story_data(story_id: Union[int, str]) -> Optional[str]:
    data = await _ambr_request(url=AMBR_BOOK_DATA_URL.format(story_id))
    if isinstance(data, Dict) and data['response'] == 200:
        return data['data']
    return None


async def _ambr_request(
    url: str,
    method: Literal['GET', 'POST'] = 'GET',
    header: AnyDict = _HEADER,
    params: Optional[AnyDict] = None,
    data: Optional[AnyDict] = None,
) -> Optional[AnyDict]:
    async with AsyncClient(timeout=None) as client:
        req = await client.request(
            method, url=url, headers=header, params=params, json=data
        )
        data = req.json()
        if data and 'code' in data:
            data['response'] = data['code']
        return data
