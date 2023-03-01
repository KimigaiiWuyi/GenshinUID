from typing import Optional

from ..utils.resource.RESOURCE_PATH import GUIDE_PATH
from ..utils.map.name_covert import alias_to_char_name


async def get_gs_guide(msg: str) -> Optional[bytes]:
    if not msg:
        return None
    name = await alias_to_char_name(msg)
    if name.startswith('旅行者'):
        name = f'{name[:3]}-{name[-1]}'
    img = GUIDE_PATH / f'{name}.png'
    if img.exists():
        with open(img, 'rb') as f:
            return f.read()
    else:
        return None
