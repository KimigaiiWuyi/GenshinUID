import json
import base64
from copy import deepcopy
from typing import Dict, List
from datetime import datetime

import aiofiles
from httpx import get

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from ..version import GenshinUID_version
from .get_gachalogs import NULL_GACHA_LOG, save_gachalogs, all_gacha_type_name
from ..utils.map.GS_MAP_PATH import charList, weaponList, weaponId2Name_data
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

INT_TO_TYPE = {
    "100": "新手祈愿",
    "200": "常驻祈愿",
    "301": "角色祈愿",
    "400": "角色祈愿",
    "302": "武器祈愿",
    "500": "集录祈愿",
}


async def import_data(uid: str, raw_data: List[Dict]):
    result = deepcopy(NULL_GACHA_LOG)
    for item in raw_data:
        if "name" not in item and "item_id" not in item:
            logger.error(t("log.genshinuid.item_d387de", item=item))
            continue

        if item["item_type"] == "角色":
            for _id in charList:
                if charList[_id]["name"] == item["name"]:
                    item["item_id"] = _id
                    break
        else:
            for _id in weaponList:
                if weaponList[_id]["name"] == item["name"]:
                    item["item_id"] = _id
                    break

        if "name" not in item or "rank_type" not in item:
            if int(item["item_id"]) >= 100000:
                char_data = charList[str(item["item_id"])]
                item["name"] = char_data["name"]
                item["rank_type"] = "5" if char_data["rank"] == "QUALITY_ORANGE" else "4"
                item["item_type"] = "角色"
            else:
                weapon_data = weaponList[str(item["item_id"])]
                item["name"] = weapon_data["name"]
                item["rank_type"] = str(weapon_data["rank"])
                item["item_type"] = "武器"

        item["uid"] = uid
        item["item_id"] = item["item_id"] if "item_id" in item else ""
        item["count"] = "1"
        item["lang"] = "zh-cn"
        item["id"] = str(item["id"])
        del item["uigf_gacha_type"]
        result[INT_TO_TYPE[item["gacha_type"]]].append(item)
    return result


async def import_gachalogs(history_url: str, type: str, uid: str) -> str:
    history_data: Dict = {}
    if type == "url":
        history_data = json.loads(get(history_url).text)
    elif type == "json":
        history_data = json.loads(history_url)
        if history_data.get("code") == 300:
            return "[提瓦特小助手]抽卡记录不存在"
    else:
        data_bytes = base64.b64decode(history_url)
        try:
            history_data = json.loads(data_bytes.decode())
        except UnicodeDecodeError:
            history_data = json.loads(data_bytes.decode("gbk"))
        except json.decoder.JSONDecodeError:
            return "请传入正确的JSON格式文件!"

    if "info" in history_data and "uigf_version" in history_data["info"]:
        history_data["info"]["version"] = history_data["info"]["uigf_version"]

    if "info" in history_data and "version" in history_data["info"]:
        _version: str = str(history_data["info"]["version"])
        _version = _version.replace("version", "").replace("v", "")
        try:
            version = float(_version)
        except ValueError:
            return "请传入正确的UIGF文件!"

        if version >= 4.0:
            if "hk4e" in history_data:
                im = ""
                for sdata in history_data["hk4e"]:
                    data_uid = sdata["uid"]
                    result = await import_data(uid, sdata["list"])
                    im += await save_gachalogs(uid, result)
                return im
            else:
                return "你当前导入的UIGF文件不包含原神的抽卡数据, 请检查!"
        else:
            if "uid" in history_data["info"]:
                data_uid = history_data["info"]["uid"]
                if data_uid != uid:
                    return f"该抽卡记录UID{data_uid}与你绑定UID{uid}不符合！"
                raw_data = history_data["list"]
                result = await import_data(uid, raw_data)
                im = await save_gachalogs(uid, result)
                return im
            else:
                return "请传入正确的UIGF文件!"
    else:
        return "请传入正确的UIGF文件!"


async def export_gachalogs(uid: str, version: str) -> dict:
    logger.info(t("log.genshinuid.version_a70d6a", version=version))
    path = PLAYER_PATH / uid
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    # 获取当前时间
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    # 抽卡记录json路径
    gachalogs_path = path / "gacha_logs.json"
    if gachalogs_path.exists():
        async with aiofiles.open(gachalogs_path, "r", encoding="UTF-8") as f:
            raw_data = json.loads(await f.read())

        if version == "2":
            result = {
                "info": {
                    "uid": uid,
                    "lang": "zh-cn",
                    "export_time": current_time,
                    "export_app": "GenshinUID",
                    "export_app_version": GenshinUID_version,
                    "export_timestamp": round(now.timestamp()),
                    "uigf_version": "v2.2",
                },
                "list": [],
            }
            for i in all_gacha_type_name:
                for item in raw_data["data"][i]:
                    if item["gacha_type"] == "400":
                        item["uigf_gacha_type"] = "301"
                    else:
                        item["uigf_gacha_type"] = item["gacha_type"]
                    result["list"].append(item)
        else:
            result = {
                "info": {
                    "export_time": current_time,
                    "export_app": "GenshinUID",
                    "export_app_version": GenshinUID_version,
                    "export_timestamp": round(now.timestamp()),
                    "version": "v4.0",
                },
                "hk4e": [],
            }
            rog = {"uid": uid, "timezone": 0, "list": []}

            weaponNmae2Id = {}
            charNmae2Id = {}
            for i in weaponId2Name_data:
                weaponNmae2Id[weaponId2Name_data[i]] = i

            for i in charList:
                charNmae2Id[charList[i]["name"]] = i

            for i in all_gacha_type_name:
                # i: 新手祈愿, 常驻祈愿, ...
                for item in raw_data["data"][i]:
                    new_item = {
                        "gacha_type": item["gacha_type"],
                        "time": item["time"],
                        "id": item["id"],
                    }
                    # 角色祈愿2 也被转为角色祈愿301
                    if item["gacha_type"] == "400":
                        new_item["uigf_gacha_type"] = "301"
                    else:
                        new_item["uigf_gacha_type"] = item["gacha_type"]

                    if item["item_type"] == "武器":
                        new_item["item_id"] = int(weaponNmae2Id[item["name"]])
                    else:
                        new_item["item_id"] = int(charNmae2Id[item["name"]])

                    rog["list"].append(new_item)

            result["hk4e"].append(rog)

        # 保存文件
        logger.info(t("log.genshinuid.version_0c583a", version=version))
        async with aiofiles.open(path / f"UIGF_v{version}_{uid}.json", "w", encoding="UTF-8") as file:
            await file.write(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=4,
                )
            )
        logger.success(t("log.genshinuid.msg_b7a6fc"))
        im = {
            "retcode": "ok",
            "data": "导出成功!",
            "name": f"UIGF_v{version}_{uid}.json",
            "url": str((path / f"UIGF_v{version}_{uid}.json").absolute()),
        }
    else:
        logger.error(t("log.genshinuid.msg_eec51f"))
        im = {
            "retcode": "error",
            "data": "你还没有抽卡记录可以导出!",
            "name": "",
            "url": "",
        }

    return im
