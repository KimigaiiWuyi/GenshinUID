import json
import random
import asyncio
from typing import Dict, List, Tuple, Optional

import aiofiles
from gsuid_core.utils.api.akashadata.models import (
    AKaShaRank,
    AKaShaUsage,
    AKaShaCharData,
)
from gsuid_core.utils.api.akashadata.request import (
    get_akasha_abyss_rank,
    get_akasha_all_char_info,
)

from ..utils.resource.RESOURCE_PATH import DATA_PATH
from ..utils.map.name_covert import name_to_avatar_id, alias_to_char_name

all_char_info_path = DATA_PATH / 'all_char_info.json'
abyss_rank_path = DATA_PATH / 'abyss_rank.json'
abyss_info_path = DATA_PATH / 'abyss_info.json'


async def save_all_char_info():
    all_char_info = await get_akasha_all_char_info()
    async with aiofiles.open(all_char_info_path, 'w') as f:
        await f.write(json.dumps(all_char_info))


async def save_all_abyss_rank():
    abyss_rank = await get_akasha_abyss_rank()
    await asyncio.sleep(random.randint(0, 3))
    abyss_info = await get_akasha_abyss_rank(True)

    async with aiofiles.open(abyss_rank_path, 'w') as f:
        await f.write(json.dumps(abyss_rank))

    async with aiofiles.open(abyss_info_path, 'w') as f:
        await f.write(json.dumps(abyss_info))


async def get_abyssinfo_data():
    if not abyss_info_path.exists():
        await save_all_abyss_rank()

    async with aiofiles.open(abyss_info_path, 'r') as f:
        abyss_info: Dict[str, Dict[str, str]] = json.loads(await f.read())
    return abyss_info


async def get_akasha_char_data(
    char_name: str,
) -> Optional[Tuple[AKaShaCharData, List[AKaShaUsage]]]:
    if not all_char_info_path.exists():
        await save_all_char_info()
    if not abyss_rank_path.exists():
        await save_all_abyss_rank()

    async with aiofiles.open(all_char_info_path, 'r') as f:
        all_char_info: Dict[str, AKaShaCharData] = json.loads(await f.read())

    async with aiofiles.open(abyss_rank_path, 'r') as f:
        abyss_rank: AKaShaRank = json.loads(await f.read())
        useage_rank = abyss_rank['usage_list']

    char_name = await alias_to_char_name(char_name)
    char_id = await name_to_avatar_id(char_name)

    if not char_id:
        return None

    _char_id = char_id.lstrip('1').lstrip('0')
    if _char_id not in all_char_info:
        return None

    char_data = all_char_info[_char_id]
    _char_id_int = int(_char_id)
    char_useage: List[AKaShaUsage] = []
    for _char in useage_rank:
        if _char['i'] == _char_id_int:
            char_useage.append(_char)
    return char_data, char_useage


async def draw_char_card(char_name: str):
    data = await get_akasha_char_data(char_name)
    if data is None:
        return
    char_data, char_useage = data[0], data[1]
    return char_data, char_useage
