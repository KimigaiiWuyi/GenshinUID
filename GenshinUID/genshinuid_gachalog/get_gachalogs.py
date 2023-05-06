import json
import asyncio
from datetime import datetime
from typing import Dict, Optional

from gsuid_core.utils.error_reply import SK_HINT

from ..utils.mys_api import mys_api
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

gacha_type_meta_data = {
    '新手祈愿': ['100'],
    '常驻祈愿': ['200'],
    '角色祈愿': ['301', '400'],
    '武器祈愿': ['302'],
}


async def get_new_gachalog(uid: str, full_data: Dict, is_force: bool):
    temp = []
    for gacha_name in gacha_type_meta_data:
        for gacha_type in gacha_type_meta_data[gacha_name]:
            end_id = '0'
            for page in range(1, 999):
                data = await mys_api.get_gacha_log_by_authkey(
                    uid, gacha_type, page, end_id
                )
                await asyncio.sleep(0.9)
                if isinstance(data, int):
                    return {}
                data = data['list']
                if data == []:
                    break
                end_id = data[-1]['id']
                if data[-1] in full_data[gacha_name] and not is_force:
                    for item in data:
                        if item not in full_data[gacha_name]:
                            temp.append(item)
                    full_data[gacha_name][0:0] = temp
                    temp = []
                    break
                if len(full_data[gacha_name]) >= 1:
                    if int(data[-1]['id']) <= int(
                        full_data[gacha_name][0]['id']
                    ):
                        full_data[gacha_name].extend(data)
                    else:
                        full_data[gacha_name][0:0] = data
                else:
                    full_data[gacha_name].extend(data)
                await asyncio.sleep(0.5)
    return full_data


async def save_gachalogs(
    uid: str, raw_data: Optional[dict] = None, is_force: bool = False
) -> str:
    path = PLAYER_PATH / str(uid)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 获取当前时间
    now = datetime.now()
    current_time = now.strftime('%Y-%m-%d %H-%M-%S')

    # 初始化最后保存的数据
    result = {}

    # 抽卡记录json路径
    gachalogs_path = path / 'gacha_logs.json'

    # 如果有老的,准备合并, 先打开文件
    gachalogs_history = {}
    old_normal_gacha_num, old_char_gacha_num, old_weapon_gacha_num = 0, 0, 0
    if gachalogs_path.exists():
        with open(gachalogs_path, "r", encoding='UTF-8') as f:
            gachalogs_history: Dict = json.load(f)
        gachalogs_history = gachalogs_history['data']
        old_normal_gacha_num = len(gachalogs_history['常驻祈愿'])
        old_char_gacha_num = len(gachalogs_history['角色祈愿'])
        old_weapon_gacha_num = len(gachalogs_history['武器祈愿'])
    else:
        gachalogs_history = {
            '新手祈愿': [],
            '常驻祈愿': [],
            '角色祈愿': [],
            '武器祈愿': [],
        }

    # 获取新抽卡记录
    if raw_data is None:
        raw_data = await get_new_gachalog(uid, gachalogs_history, is_force)
    else:
        new_data = {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
        if gachalogs_history:
            for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
                for item in raw_data[i]:
                    if (
                        item not in gachalogs_history[i]
                        and item not in new_data[i]
                    ):
                        new_data[i].append(item)
            raw_data = new_data
            for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
                raw_data[i].extend(gachalogs_history[i])

    if raw_data == {} or not raw_data:
        return SK_HINT

    temp_data = {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
    for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
        for item in raw_data[i]:
            if item not in temp_data[i]:
                temp_data[i].append(item)
    raw_data = temp_data

    result['uid'] = uid
    result['data_time'] = current_time
    result['normal_gacha_num'] = len(raw_data['常驻祈愿'])
    result['char_gacha_num'] = len(raw_data['角色祈愿'])
    result['weapon_gacha_num'] = len(raw_data['武器祈愿'])
    for i in ['常驻祈愿', '角色祈愿', '武器祈愿']:
        if len(raw_data[i]) > 1:
            raw_data[i].sort(key=lambda x: (-int(x['id'])))
    result['data'] = raw_data

    # 计算数据
    normal_add = result['normal_gacha_num'] - old_normal_gacha_num
    char_add = result['char_gacha_num'] - old_char_gacha_num
    weapon_add = result['weapon_gacha_num'] - old_weapon_gacha_num
    all_add = normal_add + char_add + weapon_add

    # 保存文件
    with open(gachalogs_path, 'w', encoding='UTF-8') as file:
        json.dump(result, file, ensure_ascii=False)

    # 回复文字
    if all_add == 0:
        im = f'UID{uid}没有新增祈愿数据!'
    else:
        im = (
            f'UID{uid}数据更新成功！'
            f'本次更新{all_add}个数据\n'
            f'常驻祈愿{normal_add}个\n角色祈愿{char_add}个\n武器祈愿{weapon_add}个！'
        )
    return im
