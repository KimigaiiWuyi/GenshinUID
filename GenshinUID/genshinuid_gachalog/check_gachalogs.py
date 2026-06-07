from typing import List

from gsuid_core.utils.api.mys.models import SingleGachaLog

from ..utils.map.GS_MAP_PATH import charList, weaponList


async def check_gachalogs(raw_data: List[SingleGachaLog]):
    for i in raw_data:
        if ("item_id" in i and not i["item_id"]) or "item_id" not in i:
            if i["item_type"] == "角色":
                for _id in charList:
                    if charList[_id]["name"] == i["name"]:
                        i["item_id"] = _id
                        break
            else:
                for _id in weaponList:
                    if weaponList[_id]["name"] == i["name"]:
                        i["item_id"] = _id
                        break
    return raw_data
