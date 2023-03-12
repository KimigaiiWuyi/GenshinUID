'''
虚空数据库 API 请求模块。
'''
from __future__ import annotations

import json

from httpx import AsyncClient

from ...version import __version__
from .models import AkashaAbyssData

AKASHA_ABYSS_URL = (
    'https://akashadata.feixiaoqiu.com/static/data/abyss_total.js'
)


async def get_akasha_abyss_info() -> AkashaAbyssData:
    '''请求虚空数据库 API 深渊出场数据

    Returns:
        AkashaAbyssData: 虚空数据库 API 深渊出场数据响应数据
    '''  # noqa: E501
    async with AsyncClient(
        headers={'User-Agent': f'gsuid-utils/{__version__}'}, verify=False
    ) as client:
        req = await client.get(url=AKASHA_ABYSS_URL)
        raw = req.text.lstrip('var static_abyss_total =')
        return json.loads(raw)
