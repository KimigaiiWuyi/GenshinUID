import json
import shutil
import asyncio
from copy import deepcopy
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import aiofiles

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from ..utils.mys_api import mys_api
from .check_gachalogs import (
    check_gachalogs,
    merge_gacha_list,
    upsert_gacha_item,
    gacha_list_contains,
)
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

NULL_GACHA_LOG: Dict[str, List[Dict[str, Any]]] = {
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

full_lock: List[str] = []
lock: List[str] = []


def _to_record_list(items: List[Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in items:
        if isinstance(item, dict):
            records.append(dict(item))
    return records


async def get_full_gachalog(uid: str) -> str:
    if uid in full_lock:
        return "当前正在全量刷新抽卡记录中, 请勿重试!请稍后再试...!"

    full_lock.append(uid)
    path = PLAYER_PATH / str(uid)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H-%M-%S")
    gachalogs_path = path / "gacha_logs.json"
    if gachalogs_path.exists():
        gacha_log_backup_path = path / f"gacha_logs_{current_time}.json"
        shutil.copy(gachalogs_path, gacha_log_backup_path)
        logger.info(t("log.genshinuid.gacha_log_backup_path_b0e4e5", gacha_log_backup_path=gacha_log_backup_path))
        async with aiofiles.open(gachalogs_path, "r", encoding="UTF-8") as f:
            gachalogs_history: Dict[str, Any] = json.loads(await f.read())
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


def remove_gachalog(gachalog: Dict[str, Any], month: int = 5) -> Dict[str, Any]:
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


async def get_new_gachalog(
    uid: str,
    full_data: Dict[str, List[Dict[str, Any]]],
    is_force: bool,
) -> Dict[str, List[Dict[str, Any]]]:
    temp: List[Dict[str, Any]] = []
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
                data_list = _to_record_list(list(data["list"]))
                if data_list == []:
                    break
                end_id = str(data_list[-1]["id"])

                if gacha_name not in full_data:
                    full_data[gacha_name] = []

                records = await check_gachalogs(data_list)
                for item in records:
                    if "op_gacha_type" in item:
                        del item["op_gacha_type"]

                # 到达已缓存区间：按预设 key/id 合并后停止，不按整 dict 判断
                if gacha_list_contains(full_data[gacha_name], records[-1]) and not is_force:
                    for item in records:
                        if not gacha_list_contains(full_data[gacha_name], item):
                            temp.append(item)
                        else:
                            upsert_gacha_item(full_data[gacha_name], item)
                    full_data[gacha_name][0:0] = temp
                    temp = []
                    break
                if len(full_data[gacha_name]) >= 1:
                    if int(records[-1]["id"]) <= int(full_data[gacha_name][0]["id"]):
                        full_data[gacha_name].extend(records)
                    else:
                        full_data[gacha_name][0:0] = records
                else:
                    full_data[gacha_name].extend(records)
                await asyncio.sleep(0.5)
    for pool_name in full_data:
        checked = await check_gachalogs(full_data[pool_name])
        full_data[pool_name] = merge_gacha_list(checked)
    return full_data


async def save_gachalogs(
    uid: str,
    raw_data: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    is_force: bool = False,
) -> str:
    if uid in lock:
        return "当前正在刷新抽卡记录中, 请勿重试!请稍后再试...!"
    lock.append(uid)
    path = PLAYER_PATH / str(uid)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H-%M-%S")

    result: Dict[str, Any] = {}
    gachalogs_path = path / "gacha_logs.json"

    gachalogs_history: Dict[str, List[Dict[str, Any]]] = {}

    (
        old_normal_gacha_num,
        old_char_gacha_num,
        old_weapon_gacha_num,
        old_mix_gacha_num,
        old_new_gacha_num,
    ) = (0, 0, 0, 0, 0)

    repaired_num = 0

    if gachalogs_path.exists():
        async with aiofiles.open(gachalogs_path, "r", encoding="UTF-8") as f:
            file_data: Dict[str, Any] = json.loads(await f.read())
        history_data = file_data["data"]
        if not isinstance(history_data, dict):
            lock.remove(uid)
            return "抽卡记录文件格式错误，请检查本地 gacha_logs.json！"

        # json 反序列化为任意 dict，运行时再收敛为记录列表
        gachalogs_history = {}
        for pool_name in all_gacha_type_name:
            pool_items = history_data[pool_name] if pool_name in history_data else []
            if isinstance(pool_items, list):
                gachalogs_history[pool_name] = _to_record_list(pool_items)
            else:
                gachalogs_history[pool_name] = []

        # 先自愈本地重复，再统计旧数量，避免修复后显示负数新增
        for i in all_gacha_type_name:
            before = len(gachalogs_history[i])
            for item in gachalogs_history[i]:
                if "op_gacha_type" in item:
                    del item["op_gacha_type"]
            gachalogs_history[i] = merge_gacha_list(await check_gachalogs(gachalogs_history[i]))
            repaired_num += before - len(gachalogs_history[i])

        old_normal_gacha_num = len(gachalogs_history["常驻祈愿"])
        old_char_gacha_num = len(gachalogs_history["角色祈愿"])
        old_weapon_gacha_num = len(gachalogs_history["武器祈愿"])
        old_mix_gacha_num = len(gachalogs_history["集录祈愿"])
        old_new_gacha_num = len(gachalogs_history["新手祈愿"])
    else:
        gachalogs_history = deepcopy(NULL_GACHA_LOG)

    api_failed = False
    # API 失败时只回写自愈快照，避免拉页中间态落盘
    healed_snapshot = deepcopy(gachalogs_history) if repaired_num > 0 else None
    if raw_data is None:
        raw_data = await get_new_gachalog(uid, gachalogs_history, is_force)
        if raw_data == {} or not raw_data:
            api_failed = True
            if healed_snapshot is not None:
                raw_data = healed_snapshot
            else:
                lock.remove(uid)
                return "🔔 你还没有绑定过Stoken哦~\n📎 请使用扫码登陆命令获取Stoken\n🚩 或者查看帮助文档获取绑定方式"
    else:
        new_data = deepcopy(NULL_GACHA_LOG)
        if gachalogs_history:
            for i in all_gacha_type_name:
                if i not in raw_data:
                    raw_data[i] = []
                for item in raw_data[i]:
                    if "op_gacha_type" in item:
                        del item["op_gacha_type"]
                    if gacha_list_contains(gachalogs_history[i], item):
                        upsert_gacha_item(gachalogs_history[i], item)
                    elif gacha_list_contains(new_data[i], item):
                        upsert_gacha_item(new_data[i], item)
                    else:
                        new_data[i].append(item)
            raw_data = new_data
            for i in all_gacha_type_name:
                raw_data[i].extend(gachalogs_history[i])

    if raw_data == {} or not raw_data:
        lock.remove(uid)
        return "🔔 你还没有绑定过Stoken哦~\n📎 请使用扫码登陆命令获取Stoken\n🚩 或者查看帮助文档获取绑定方式"

    if "集录祈愿" not in raw_data:
        raw_data["集录祈愿"] = []
    if "新手祈愿" not in raw_data:
        raw_data["新手祈愿"] = []

    for i in all_gacha_type_name:
        if i not in raw_data:
            raw_data[i] = []
        raw_data[i] = merge_gacha_list(raw_data[i])

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

    normal_add = result["normal_gacha_num"] - old_normal_gacha_num
    char_add = result["char_gacha_num"] - old_char_gacha_num
    weapon_add = result["weapon_gacha_num"] - old_weapon_gacha_num
    mix_add = result["mix_gacha_num"] - old_mix_gacha_num
    new_add = result["new_gacha_num"] - old_new_gacha_num
    all_add = normal_add + char_add + weapon_add

    with open(gachalogs_path, "w", encoding="UTF-8") as file:
        json.dump(result, file, ensure_ascii=False)

    repair_hint = f"（已自动修复{repaired_num}条重复记录）" if repaired_num > 0 else ""
    if api_failed:
        im = f"UID{uid}刷新抽卡记录失败，请检查Stoken/网络后重试。{repair_hint}"
    elif all_add == 0:
        im = f"UID{uid}没有新增祈愿数据!{repair_hint}"
    else:
        im = (
            f"UID{uid}数据更新成功！"
            f"本次更新{all_add}个数据\n"
            f"常驻祈愿{normal_add}个\n角色祈愿{char_add}个\n"
            f"武器祈愿{weapon_add}个！\n集录祈愿{mix_add}个！"
        )
        if new_add > 0:
            im += f"\n新手祈愿{new_add}个！"
        if repair_hint:
            im += f"\n{repair_hint}"
    lock.remove(uid)
    return im
