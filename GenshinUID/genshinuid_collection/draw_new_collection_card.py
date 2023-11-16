from PIL import Image
from gsuid_core.utils.download_resource.download_image import get_image

from ..utils.resource.RESOURCE_PATH import ICON_PATH
from .draw_collection_card import TEXT_PATH, get_base_data


async def draw_explore(uid: str):
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, str) or isinstance(
        raw_data, (bytes, bytearray, memoryview)
    ):
        return raw_data

    worlds = raw_data['world_explorations']
    for world in worlds:
        area_bg = (
            Image.open(TEXT_PATH / 'area_bg')
            .resize((216, 216))
            .convert('RGBA')
        )
        icon = await get_image(world['icon'], ICON_PATH)
        # percent = world['exploration_percentage']

        area_bg.paste(icon, (27, 27), icon)
