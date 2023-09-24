import json
import asyncio

from gsuid_core.utils.database.models import GsBind, GsUser

from ..utils.resource.RESOURCE_PATH import MAIN_PATH

V3_DATA_PATH = MAIN_PATH / 'v3_data.json'


async def import_v3_data() -> str:
    if not V3_DATA_PATH.exists():
        return '在数据文件夹内未发现v3数据...'
    with open(V3_DATA_PATH, 'r') as file:
        v3_data = json.loads(file.read())
    await asyncio.sleep(3)
    for bind_data in v3_data['bind']:
        bind_data['bot_id'] = v3_data['bot_id']
        await GsBind.full_insert_data(**bind_data)
    for user_data in v3_data['user']:
        user_data['bot_id'] = v3_data['bot_id']
        await GsUser.full_insert_data(**user_data)
    return '导入v3数据成功! '
