from typing import Union

from gsuid_core.utils.api.mys_api import _MysApi
from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.api.mys.models import IndexData

mys_api = _MysApi()


async def get_base_data(uid: str) -> Union[bytes, str, IndexData]:
    # 获取Cookies
    raw_data = await mys_api.get_info(uid, None)
    if isinstance(raw_data, int):
        return await get_error_img(raw_data)
    return raw_data
