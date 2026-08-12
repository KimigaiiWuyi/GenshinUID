from copy import deepcopy
from typing import Any, Dict, List, Tuple, Optional

from ..utils.map.GS_MAP_PATH import charList, weaponList

# 标准字段；相等判断只看这些 key，忽略扩展字段（如 _isoTime）
GACHA_CORE_KEYS: Tuple[str, ...] = (
    "uid",
    "gacha_type",
    "item_id",
    "count",
    "time",
    "name",
    "lang",
    "item_type",
    "rank_type",
    "id",
)


def _value_to_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _is_empty(value: object) -> bool:
    return value is None or value == ""


def build_gacha_core(item: Dict[str, Any]) -> Dict[str, str]:
    """按预设 key 构建比较用 dict；缺字段/None 视为空串，兼容老数据。"""
    core: Dict[str, str] = {}
    for key in GACHA_CORE_KEYS:
        if key in item:
            core[key] = _value_to_str(item[key])
        else:
            core[key] = ""
    return core


def gacha_core_equal(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    return build_gacha_core(a) == build_gacha_core(b)


def get_gacha_id(item: Dict[str, Any]) -> str:
    if "id" not in item:
        return ""
    return _value_to_str(item["id"])


def merge_gacha_item(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    """同条记录合并：补空标准字段，并入缺失扩展字段，不覆盖已有非空值。"""
    merged: Dict[str, Any] = dict(base)
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = value
            continue
        if _is_empty(merged[key]) and not _is_empty(value):
            merged[key] = value
    return merged


def find_gacha_item(items: List[Dict[str, Any]], item: Dict[str, Any]) -> int:
    """先预设 key 全等，再按 id；找不到返回 -1。"""
    item_id = get_gacha_id(item)
    item_core = build_gacha_core(item)

    for index, existing in enumerate(items):
        if build_gacha_core(existing) == item_core:
            return index

    if item_id:
        for index, existing in enumerate(items):
            if get_gacha_id(existing) == item_id:
                return index

    return -1


def gacha_list_contains(items: List[Dict[str, Any]], item: Dict[str, Any]) -> bool:
    return find_gacha_item(items, item) >= 0


def upsert_gacha_item(items: List[Dict[str, Any]], item: Dict[str, Any]) -> bool:
    """已存在则合并覆盖原位并返回 False，否则追加并返回 True。"""
    index = find_gacha_item(items, item)
    if index >= 0:
        items[index] = merge_gacha_item(items[index], item)
        return False
    items.append(item)
    return True


def merge_gacha_list(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 id（优先）/ 预设 key 去重并合并扩展字段，用于刷新自愈。"""
    result: List[Dict[str, Any]] = []
    id_map: Dict[str, int] = {}
    core_map: Dict[Tuple[str, ...], int] = {}

    for raw in items:
        item = deepcopy(raw)
        item_id = get_gacha_id(item)
        core_key = tuple(build_gacha_core(item)[k] for k in GACHA_CORE_KEYS)

        index: Optional[int] = None
        if item_id and item_id in id_map:
            index = id_map[item_id]
        elif core_key in core_map:
            index = core_map[core_key]

        if index is not None:
            old_core_key = tuple(build_gacha_core(result[index])[k] for k in GACHA_CORE_KEYS)
            merged = merge_gacha_item(result[index], item)
            result[index] = merged
            new_core_key = tuple(build_gacha_core(merged)[k] for k in GACHA_CORE_KEYS)
            if old_core_key in core_map and core_map[old_core_key] == index:
                del core_map[old_core_key]
            core_map[new_core_key] = index
            merged_id = get_gacha_id(merged)
            if merged_id:
                id_map[merged_id] = index
        else:
            index = len(result)
            result.append(item)
            core_map[core_key] = index
            if item_id:
                id_map[item_id] = index

    return result


async def check_gachalogs(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for i in raw_data:
        has_item_id = "item_id" in i and bool(i["item_id"])
        if has_item_id:
            continue
        if "item_type" not in i or "name" not in i:
            continue
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
