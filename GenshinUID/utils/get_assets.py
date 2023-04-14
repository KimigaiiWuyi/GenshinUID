from typing import Literal, Optional

from PIL import Image
from aiohttp.client import ClientSession

AMBR_UI = 'https://api.ambr.top/assets/UI/{}.png'
ENKA_UI = 'https://enka.network/ui/{}.png'


async def _get_assets(
    name: str, type: Literal['ENKA', 'AMBR'] = 'AMBR'
) -> Optional[Image.Image]:
    if type == 'AMBR':
        URL = AMBR_UI
    else:
        URL = ENKA_UI
    async with ClientSession() as sess:
        async with sess.get(URL.format(name)) as res:
            if res.status == 200:
                content = await res.read()
                return Image.open(content)
            else:
                return None


async def get_assets_from_enka(name: str) -> Optional[Image.Image]:
    return await _get_assets(name, 'ENKA')


async def get_assets_from_ambr(name: str) -> Optional[Image.Image]:
    return await _get_assets(name, 'AMBR')
