from pathlib import Path
from typing import Union

from ..gsuid_utils.api.minigg.request import get_map_data
from ..gsuid_utils.api.minigg.exception import MiniggNotFoundError

MAP_DATA = Path(__file__).parent / 'map_data'


async def draw_genshin_map(
    resource_name: str,
    map_id: str,
    map_name: str,
) -> Union[bytes, str]:
    try:
        raw_data = await get_map_data(resource_name, map_id)
    except MiniggNotFoundError:
        return f'未在{map_name}找到所需资源...'
    with open(MAP_DATA / f'{map_name}_{resource_name}.jpg', 'wb') as f:
        f.write(raw_data)  # 保存到文件夹中
    return raw_data
