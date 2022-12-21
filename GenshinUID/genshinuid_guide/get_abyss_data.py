import json
from pathlib import Path
from typing import Dict, List, Union

from .abyss_history import history_data
from ..utils.hhw_api.get_hhw_data import get_abyss_review, get_hhw_abyss_raw

REVIEW_PATH = Path(__file__).parent / "review.json"


async def generate_data():
    raw_data = await get_hhw_abyss_raw()
    result = {}
    for version in history_data:
        for floor in history_data[version]:
            _id = history_data[version][floor]
            data = await get_abyss_review(raw_data, _id, floor)
            result[version] = data

    with open(REVIEW_PATH, 'w', encoding='UTF-8') as file:
        json.dump(result, file, ensure_ascii=False)


async def get_review(version: Union[str, float]) -> Union[List, str]:
    with open(REVIEW_PATH, "r", encoding='UTF-8') as f:
        review: Dict[str, Dict[str, List[str]]] = json.load(f)

    if isinstance(version, float):
        version = str(version)

    im_list = []
    if version in review:
        im_list.append(f'{version}版本深渊阵容')
        for floor in review[version]:
            im_list.append(floor)
            im_list.append('\n'.join(review[version][floor]))
        return im_list
    else:
        return '暂无该版本的深渊阵容...'
