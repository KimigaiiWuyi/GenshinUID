import json

import aiofiles

from ..genshinuid_config.gs_config import gsconfig
from ..utils.map.name_covert import avatar_id_to_name
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

is_enable_akasha = gsconfig.get_config('EnableAkasha').data


async def get_rank(uid: str) -> str:
    if not is_enable_akasha:
        return '未开启排名系统...'
    path = PLAYER_PATH / uid / 'rank.json'
    if not path.exists():
        return '你还没有排名缓存, 请使用[强制刷新]生成/刷新数据！'

    async with aiofiles.open(path, 'r', encoding='UTF-8') as file:
        rank_data = json.loads(await file.read())

    if len(rank_data) == 0:
        return '你还没有排名缓存, 请使用[强制刷新]生成/刷新数据！'

    im_list = []

    for char in rank_data:
        raw_data = rank_data[char]
        data = raw_data['calculations']['fit']
        char_name = await avatar_id_to_name(char)
        result = '{:.2f}'.format(data['result'])
        rank = data['ranking']
        if isinstance(rank, str):
            rank = int(rank[1:])
        outof = data['outOf']
        percent = '{:.2f}'.format((rank / outof) * 100)
        im_list.append(
            f'{char_name}: {result} - 大约{rank}名/{outof} (前{percent}%)'
        )
    im_list.append('# 图片版施工中')

    return '\n'.join(im_list)
