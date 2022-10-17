from pathlib import Path
from typing import Union

from ..utils.minigg_api.get_minigg_data import get_minigg_map_data

MAP_DATA = Path(__file__).parent / 'map_data'


async def draw_genshin_map(
    resource_name: str,
    map_id: str,
    map_name: str,
) -> Union[bytes, str]:
    raw_data = await get_minigg_map_data(resource_name, map_id)
    if isinstance(raw_data, dict):
        raw_data = raw_data['message']
    else:
        with open(MAP_DATA / f'{map_name}_{resource_name}.jpg', 'wb') as f:
            f.write(raw_data)  # 保存到文件夹中
    return raw_data
