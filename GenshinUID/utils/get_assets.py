from io import BytesIO
from typing import Literal, Optional

import aiofiles
from PIL import Image
from aiohttp.client import ClientSession

from .resource.RESOURCE_PATH import ICON_PATH

AMBR_UI = 'https://gi.yatta.top/assets/UI/{}.png'
ENKA_UI = 'https://enka.network/ui/{}.png'


async def _get_assets(
    name: str, type: Literal['ENKA', 'AMBR'] = 'AMBR'
) -> Optional[Image.Image]:
    path = ICON_PATH / f'{name}.png'
    if path.exists():
        return Image.open(path)
    if type == 'AMBR':
        URL = AMBR_UI
        EURL = ENKA_UI
    else:
        URL = ENKA_UI
        EURL = AMBR_UI
    async with ClientSession() as sess:
        async with sess.get(URL.format(name)) as res:
            if res.status == 200:
                content = await res.read()
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(content)
                return Image.open(BytesIO(content))
            else:
                async with sess.get(EURL.format(name)) as res:
                    if res.status == 200:
                        content = await res.read()
                        async with aiofiles.open(path, 'wb') as f:
                            await f.write(content)
                        return Image.open(BytesIO(content))
                    else:
                        return None


async def get_assets_from_enka(name: str) -> Optional[Image.Image]:
    return await _get_assets(name, 'ENKA')


async def get_assets_from_ambr(name: str) -> Optional[Image.Image]:
    return await _get_assets(name, 'AMBR')
