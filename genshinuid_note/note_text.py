from ..utils.mhy_api.get_mhy_data import get_award

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
    data = await get_award(uid)
    nickname = data['data']['nickname']
    day_stone = data['data']['day_data']['current_primogems']
    day_mora = data['data']['day_data']['current_mora']
    lastday_stone = data['data']['day_data']['last_primogems']
    lastday_mora = data['data']['day_data']['last_mora']
    month_stone = data['data']['month_data']['current_primogems']
    month_mora = data['data']['month_data']['current_mora']
    lastmonth_stone = data['data']['month_data']['last_primogems']
    lastmonth_mora = data['data']['month_data']['last_mora']
    group_str = ''
    for i in data['data']['month_data']['group_by']:
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
