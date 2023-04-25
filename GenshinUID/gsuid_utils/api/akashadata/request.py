'''
虚空数据库 API 请求模块。
'''
from __future__ import annotations

import json
from typing import Literal, Optional

from httpx import AsyncClient

from ..types import AnyDict
from ...version import __version__
from .models import AKaShaRank, AkashaAbyssData
from .api import AKASHA_RANK_URL, AKASHA_ABYSS_URL

_HEADER = {'User-Agent': f'gsuid-utils/{__version__}'}


async def get_akasha_abyss_info() -> AkashaAbyssData:
    '''请求虚空数据库 API 深渊出场数据

    Returns:
        AkashaAbyssData: 虚空数据库 API 深渊出场数据响应数据
    '''  # noqa: E501
    raw_data = await _akasha_request(AKASHA_ABYSS_URL)
    raw_data = raw_data.lstrip('var static_abyss_total =')
    data = json.loads(raw_data)
    return data


async def get_akasha_abyss_rank(is_info: bool = False) -> AKaShaRank:
    raw_data = await _akasha_request(AKASHA_RANK_URL)
    raw_data = raw_data.lstrip('var static_abyss_total =')
    data_list = raw_data.split(';')
    data1 = data_list[0].lstrip('var static_schedule_version_dict =')
    data2 = data_list[1].lstrip('var static_abyss_record_dict =')
    schedule_version_dict = json.loads(data1)
    abyss_record_dict = json.loads(data2)
    if is_info:
        return schedule_version_dict
    return abyss_record_dict


async def _akasha_request(
    url: str,
    method: Literal['GET', 'POST'] = 'GET',
    header: AnyDict = _HEADER,
    params: Optional[AnyDict] = None,
    data: Optional[AnyDict] = None,
) -> str:
    async with AsyncClient(
        headers=header,
        verify=False,
        timeout=None,
    ) as client:
        req = await client.request(
            method=method, url=url, params=params, data=data
        )
        return req.text
