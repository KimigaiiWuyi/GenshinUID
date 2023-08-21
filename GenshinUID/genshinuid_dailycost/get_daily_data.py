import time
from datetime import datetime, timedelta
from typing import Dict, Literal, Optional

from gsuid_core.utils.api.ambr.request import (
    get_all_upgrade,
    get_ambr_daily_data,
)


def _add_result(upgrades, type: Literal['weapon', 'avatar'], domain, result):
    for _th in upgrades[type]:
        for item in upgrades[type][_th]['items']:
            if int(item) in domain['reward']:
                if domain['name'] not in result:
                    result[domain['name']] = []
                if domain['reward'][-1] not in result[domain['name']]:
                    result[domain['name']].append(domain['reward'][-1])
                if upgrades[type][_th] not in result[domain['name']]:
                    result[domain['name']].append(upgrades[type][_th])
    return result


async def generate_daily_data() -> Optional[Dict]:
    upgrades = await get_all_upgrade()
    daily_data = await get_ambr_daily_data()

    if upgrades is None or daily_data is None:
        return None

    # 获取当前日期并以4点为分界线
    now = time.localtime()
    now_str = time.strftime('%Y-%m-%d %H:%M:%S', now)
    now_dt = datetime.strptime(now_str, '%Y-%m-%d %H:%M:%S')
    new_dt = now_dt - timedelta(hours=4)
    day = new_dt.strftime('%A').lower()

    result = {}

    if day == 'sunday':
        return result

    for domain in daily_data[day]:
        if '炼武' in domain['name']:
            result = _add_result(upgrades, 'weapon', domain, result)
        else:
            result = _add_result(upgrades, 'avatar', domain, result)
    return result
