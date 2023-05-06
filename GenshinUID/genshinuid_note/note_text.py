from gsuid_core.utils.error_reply import get_error

from ..utils.mys_api import mys_api

month_im = """
==============
{}
UID：{}
==============
本日获取原石：{}
本日获取摩拉：{}
==============
昨日获取原石：{}
昨日获取摩拉：{}
==============
本月获取原石：{}
本月获取摩拉：{}
==============
上月获取原石：{}
上月获取摩拉：{}
==============
原石收入组成：
{}=============="""


async def award(uid) -> str:
    data = await mys_api.get_award(uid)
    if isinstance(data, int):
        return get_error(data)
    nickname = data['nickname']
    day_stone = data['day_data']['current_primogems']
    day_mora = data['day_data']['current_mora']
    lastday_stone = 0
    lastday_mora = 0
    if int(uid[0]) < 6:
        lastday_stone = data['day_data']['last_primogems']
        lastday_mora = data['day_data']['last_mora']
    month_stone = data['month_data']['current_primogems']
    month_mora = data['month_data']['current_mora']
    lastmonth_stone = data['month_data']['last_primogems']
    lastmonth_mora = data['month_data']['last_mora']
    group_str = ''
    for i in data['month_data']['group_by']:
        group_str = (
            group_str
            + i['action']
            + '：'
            + str(i['num'])
            + '（'
            + str(i['percent'])
            + '%）'
            + '\n'
        )

    im = month_im.format(
        nickname,
        uid,
        day_stone,
        day_mora,
        lastday_stone,
        lastday_mora,
        month_stone,
        month_mora,
        lastmonth_stone,
        lastmonth_mora,
        group_str,
    )
    return im
