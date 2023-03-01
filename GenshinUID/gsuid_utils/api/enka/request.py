'''Enka Network 请求模块。
MiniGG Enka 加速服务在此模块内。
'''
from __future__ import annotations

from typing import Literal

from httpx import AsyncClient

from .models import EnkaData
from ...version import __version__

ADDRESS = {
    'enka': 'https://enka.network',
    'microgg': 'https://profile.microgg.cn',
}


async def get_enka_info(
    uid: str, address: Literal['enka', 'microgg'] = 'enka'
) -> EnkaData:
    '''请求 Enka Network

    Args:
        uid (str): 原神 UID
        address (Literal[&quot;enka&quot;, &quot;microgg&quot;, &quot;minigg&quot;], optional): API 地址. Defaults to 'enka'.

    Returns:
        EnkaData: Enka Network 响应数据
    '''  # noqa: E501
    async with AsyncClient(
        base_url=ADDRESS[address],
        headers={'User-Agent': f'gsuid-utils/{__version__}'},
    ) as client:
        req = await client.get(url=f'/api/uid/{uid}')
        return req.json()
