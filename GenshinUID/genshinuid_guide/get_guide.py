from typing import Optional

from ..utils.download_resource.RESOURCE_PATH import GUIDE_PATH
from ..utils.alias.alias_to_char_name import alias_to_char_name


async def get_gs_guide(msg: str) -> Optional[bytes]:
    if not msg:
        return None
    name = await alias_to_char_name(msg)
    img = GUIDE_PATH / f'{name}.png'
    if img.exists():
        with open(img, 'rb') as f:
            return f.read()
    else:
        return None
