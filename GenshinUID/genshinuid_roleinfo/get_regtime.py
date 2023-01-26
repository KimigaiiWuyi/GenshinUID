import json
import time

from nonebot.log import logger

from ..utils.mhy_api.get_mhy_data import get_regtime_data


async def calc_reg_time(uid: str):
    # 获得原始数据
    try:
        raw_data = await get_regtime_data(uid)
        # 获取时间戳
        reg_time = json.loads(raw_data['data']['data'])['1']
        # 转换为日期
        regtime_date = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(reg_time)
        )
        return f'UID{uid} 的注册时间为\n{regtime_date}'
    except Exception as e:
        logger.error(e)
        return '数据获取错误, 可尝试使用“刷新ck”功能。'
