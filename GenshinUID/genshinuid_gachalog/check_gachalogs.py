from typing import Dict, List

from ..utils.map.GS_MAP_PATH import charList, weaponList


async def check_gachalogs(raw_data: List[Dict]):
    for i in raw_data:
        if ("item_id" in i and not i["item_id"]) or "item_id" not in i:
            if i["item_type"] == "角色":
                for _id in charList:
                    if charList[_id]["CHS"] == i["name"]:
                        i["item_id"] = _id
                        break
            else:
                for _id in weaponList:
                    if weaponList[_id]["CHS"] == i["name"]:
                        i["item_id"] = _id
                        break
    return raw_data
