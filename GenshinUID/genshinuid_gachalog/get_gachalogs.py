import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..utils.mhy_api.get_mhy_data import get_gacha_log_by_authkey

PLAYER_PATH = Path(__file__).parents[1] / 'player'


async def save_gachalogs(uid: str, raw_data: Optional[dict] = None):
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
    gachalogs_history = None
    old_normal_gacha_num, old_char_gacha_num, old_weapon_gacha_num = 0, 0, 0
    if gachalogs_path.exists():
        with open(gachalogs_path, "r", encoding='UTF-8') as f:
            gachalogs_history = json.load(f)
        gachalogs_history = gachalogs_history['data']
        old_normal_gacha_num = len(gachalogs_history['常驻祈愿'])
        old_char_gacha_num = len(gachalogs_history['角色祈愿'])
        old_weapon_gacha_num = len(gachalogs_history['武器祈愿'])

    # 获取新抽卡记录
    if raw_data is None:
        raw_data = await get_gacha_log_by_authkey(uid, gachalogs_history)
    else:
        new_data = {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
        if gachalogs_history:
            for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
                for item in raw_data[i]:
                    if item not in gachalogs_history[i]:
                        new_data[i].append(item)
            raw_data = new_data
            for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
                raw_data[i].extend(gachalogs_history[i])

    if raw_data == {}:
        return '你还没有绑定过Stoken噢~'
    if not raw_data:
        return '你还没有绑定过Stoken或者Stoken已失效~'

    # 校验值 & 两个版本后删除这段
    temp_data = {'新手祈愿': [], '常驻祈愿': [], '角色祈愿': [], '武器祈愿': []}
    for i in ['新手祈愿', '常驻祈愿', '角色祈愿', '武器祈愿']:
        for item in raw_data[i]:
            if 'count' in item:
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
