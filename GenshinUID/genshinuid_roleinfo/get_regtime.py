import json
import time

from nonebot.log import logger

from ..utils.mhy_api.get_mhy_data import get_regtime_data


async def calc_reg_time(uid: str):
    # 获得原始数据
    raw_data = await get_regtime_data(uid)
    # 获取时间戳
    reg_time = json.loads(raw_data['data']['data'])["1"]
    # 转换为日期
    regtime_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(reg_time))
    # logger.debug(reg_time)
    return regtime_date
