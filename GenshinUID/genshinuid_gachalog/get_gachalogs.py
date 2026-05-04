import json
import shutil
import asyncio
from copy import deepcopy
from typing import Dict, Optional
from datetime import datetime, timedelta

import aiofiles

from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import SK_HINT

from ..utils.mys_api import mys_api
from .check_gachalogs import check_gachalogs
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

NULL_GACHA_LOG = {
    "新手祈愿": [],
    "常驻祈愿": [],
    "角色祈愿": [],
    "武器祈愿": [],
    "集录祈愿": [],
}

all_gacha_type_name = [
    "新手祈愿",
    "常驻祈愿",
    "角色祈愿",
    "武器祈愿",
    "集录祈愿",
]

gacha_type_meta_data = {
    "新手祈愿": ["100"],
    "常驻祈愿": ["200"],
    "角色祈愿": ["301", "400"],
    "武器祈愿": ["302"],
    "集录祈愿": ["500"],
}

full_lock = []
lock = []


async def get_full_gachalog(uid: str):
    if uid in full_lock:
        return "当前正在全量刷新抽卡记录中, 请勿重试!请稍后再试...!"

    full_lock.append(uid)
    path = PLAYER_PATH / str(uid)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 获取当前时间
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H-%M-%S")
    # 抽卡记录json路径
    gachalogs_path = path / "gacha_logs.json"
    if gachalogs_path.exists():
        gacha_log_backup_path = path / f"gacha_logs_{current_time}.json"
        shutil.copy(gachalogs_path, gacha_log_backup_path)
        logger.info(f"[全量刷新抽卡记录] 已备份抽卡记录到{gacha_log_backup_path}")
        async with aiofiles.open(gachalogs_path, "r", encoding="UTF-8") as f:
            gachalogs_history: Dict = json.loads(await f.read())
        gachalogs_history = remove_gachalog(gachalogs_history)
        async with aiofiles.open(gachalogs_path, "w", encoding="UTF-8") as f:
            await f.write(
                json.dumps(
                    gachalogs_history,
                    ensure_ascii=False,
                )
            )
        im = await save_gachalogs(uid, None)
    else:
        im = "你还没有已缓存的抽卡记录, 请使用刷新抽卡记录！"
    full_lock.remove(uid)
    return im


def remove_gachalog(gachalog: Dict, month: int = 5):
    now = datetime.now()
    threshold = now - timedelta(days=month * 30)

    map_num = {
        "新手祈愿": "new_gacha_num",
        "常驻祈愿": "normal_gacha_num",
        "角色祈愿": "char_gacha_num",
        "武器祈愿": "weapon_gacha_num",
        "集录祈愿": "mix_gacha_num",
    }
    for gacha_name in map_num:
        gachanum_name = map_num[gacha_name]
        gachalog["data"][gacha_name] = [
            item
            for item in gachalog["data"][gacha_name]
            if datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S") <= threshold
        ]
        gachalog[gachanum_name] = len(gachalog["data"][gacha_name])

    return gachalog


async def get_new_gachalog(uid: str, full_data: Dict, is_force: bool):
    temp = []
    for gacha_name in gacha_type_meta_data:
        for gacha_type in gacha_type_meta_data[gacha_name]:
            end_id = "0"
            for page in range(1, 999):
                data = await mys_api.get_gacha_log_by_authkey(
                    uid,
                    gacha_type,
                    page,
                    end_id,
                )
                await asyncio.sleep(0.9)
                if isinstance(data, int):
                    return {}
                data = data["list"]
                if data == []:
                    break
                end_id = data[-1]["id"]

                if gacha_name not in full_data:
                    full_data[gacha_name] = []

                data = await check_gachalogs(data)
                if data[-1] in full_data[gacha_name] and not is_force:
                    for item in data:
                        if item not in full_data[gacha_name]:
                            temp.append(item)
                    full_data[gacha_name][0:0] = temp
                    temp = []
                    break
                if len(full_data[gacha_name]) >= 1:
                    if int(data[-1]["id"]) <= int(full_data[gacha_name][0]["id"]):
                        full_data[gacha_name].extend(data)
                    else:
                        full_data[gacha_name][0:0] = data
                else:
                    full_data[gacha_name].extend(data)
                await asyncio.sleep(0.5)
    for i in full_data:
        full_data[i] = await check_gachalogs(full_data[i])
    return full_data


async def save_gachalogs(uid: str, raw_data: Optional[dict] = None, is_force: bool = False) -> str:
    if uid in lock:
        return "当前正在刷新抽卡记录中, 请勿重试!请稍后再试...!"
    lock.append(uid)
    path = PLAYER_PATH / str(uid)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 获取当前时间
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H-%M-%S")

    # 初始化最后保存的数据
    result = {}

    # 抽卡记录json路径
    gachalogs_path = path / "gacha_logs.json"

    # 如果有老的,准备合并, 先打开文件
    gachalogs_history = {}

    (
        old_normal_gacha_num,
        old_char_gacha_num,
        old_weapon_gacha_num,
        old_mix_gacha_num,
        old_new_gacha_num,
    ) = (0, 0, 0, 0, 0)

    if gachalogs_path.exists():
        async with aiofiles.open(gachalogs_path, "r", encoding="UTF-8") as f:
            gachalogs_history: Dict = json.loads(await f.read())
        gachalogs_history = gachalogs_history["data"]
        old_normal_gacha_num = len(gachalogs_history["常驻祈愿"])
        old_char_gacha_num = len(gachalogs_history["角色祈愿"])
        old_weapon_gacha_num = len(gachalogs_history["武器祈愿"])
        if "集录祈愿" in gachalogs_history:
            old_mix_gacha_num = len(gachalogs_history["集录祈愿"])
        else:
            gachalogs_history["集录祈愿"] = []
            old_mix_gacha_num = 0
        if "新手祈愿" in gachalogs_history:
            old_new_gacha_num = len(gachalogs_history["新手祈愿"])
        else:
            gachalogs_history["新手祈愿"] = []
            old_new_gacha_num = 0
    else:
        gachalogs_history = deepcopy(NULL_GACHA_LOG)

    for i in all_gacha_type_name:
        gachalogs_history[i] = await check_gachalogs(gachalogs_history[i])

    # 获取新抽卡记录
    if raw_data is None:
        raw_data = await get_new_gachalog(uid, gachalogs_history, is_force)
    else:
        new_data = deepcopy(NULL_GACHA_LOG)
        if gachalogs_history:
            for i in all_gacha_type_name:
                for item in raw_data[i]:
                    if item not in gachalogs_history[i] and item not in new_data[i]:
                        new_data[i].append(item)
            raw_data = new_data
            for i in all_gacha_type_name:
                raw_data[i].extend(gachalogs_history[i])

    if raw_data == {} or not raw_data:
        lock.remove(uid)
        return SK_HINT

    if "集录祈愿" not in raw_data:
        raw_data["集录祈愿"] = []
    if "新手祈愿" not in raw_data:
        raw_data["新手祈愿"] = []

    temp_data = deepcopy(NULL_GACHA_LOG)
    for i in all_gacha_type_name:
        for item in raw_data[i]:
            if item not in temp_data[i]:
                temp_data[i].append(item)
    raw_data = temp_data

    result["uid"] = uid
    result["data_time"] = current_time
    result["new_gacha_num"] = len(raw_data["新手祈愿"])
    result["normal_gacha_num"] = len(raw_data["常驻祈愿"])
    result["char_gacha_num"] = len(raw_data["角色祈愿"])
    result["weapon_gacha_num"] = len(raw_data["武器祈愿"])
    result["mix_gacha_num"] = len(raw_data["集录祈愿"])
    for i in all_gacha_type_name:
        if len(raw_data[i]) > 1:
            raw_data[i].sort(key=lambda x: -int(x["id"]))
    result["data"] = raw_data

    # 计算数据
    normal_add = result["normal_gacha_num"] - old_normal_gacha_num
    char_add = result["char_gacha_num"] - old_char_gacha_num
    weapon_add = result["weapon_gacha_num"] - old_weapon_gacha_num
    mix_add = result["mix_gacha_num"] - old_mix_gacha_num
    new_add = result["new_gacha_num"] - old_new_gacha_num
    all_add = normal_add + char_add + weapon_add

    # 保存文件
    with open(gachalogs_path, "w", encoding="UTF-8") as file:
        json.dump(result, file, ensure_ascii=False)

    # 回复文字
    if all_add == 0:
        im = f"UID{uid}没有新增祈愿数据!"
    else:
        im = (
            f"UID{uid}数据更新成功！"
            f"本次更新{all_add}个数据\n"
            f"常驻祈愿{normal_add}个\n角色祈愿{char_add}个\n"
            f"武器祈愿{weapon_add}个！\n集录祈愿{mix_add}个！"
        )
        if new_add > 0:
            im += f"\n新手祈愿{new_add}个！"
    lock.remove(uid)
    return im
