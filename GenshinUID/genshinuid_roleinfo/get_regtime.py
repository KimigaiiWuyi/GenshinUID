import json
import time

from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error

from ..utils.mys_api import mys_api


async def calc_reg_time(uid: str) -> str:
    # 获得原始数据
    try:
        raw_data = await mys_api.get_regtime_data(uid)
        if isinstance(raw_data, int):
            return get_error(raw_data)
        # 获取时间戳
        reg_time = json.loads(raw_data['data'])['1']
        # 转换为日期
        regtime_date = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(reg_time)
        )
        return f'UID{uid} 的注册时间为\n{regtime_date}'
    except Exception as e:
        logger.error(e)
        return '数据获取错误, 可尝试使用【刷新ck】或者发送【扫码登陆】以绑定CK。'
