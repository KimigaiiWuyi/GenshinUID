"""原神图鉴通用筛选：角色 / 武器 / 圣遗物套装。不依赖用户绑定。"""

from __future__ import annotations

from typing import Optional

from pydantic_ai import RunContext

from gsuid_core.ai_core.models import ToolContext
from gsuid_core.ai_core.register import ai_tools

from ._common import (
    as_int,
    as_str,
    region_zh,
    element_zh,
    weapon_type_zh,
    normalize_element,
    normalize_weapon_type,
)
from ..utils.map.GS_MAP_PATH import charList, weaponList, reliquaryList

_CTX = ["原神", "Genshin", "游戏"]
_DOMAIN = "原神资料库"


def _char_entry(raw: object) -> dict[str, object] | None:
    if not isinstance(raw, dict):
        return None
    if "name" not in raw or "weaponType" not in raw:
        return None
    name = as_str(raw["name"])
    if not name or name.startswith("奇偶"):
        return None
    return raw


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=["按元素/武器类型/星级筛选原神角色图鉴：地区、突破属性"],
    aliases=["原神·角色图鉴", "原神·角色筛选"],
)
async def filter_genshin_chars(
    ctx: RunContext[ToolContext],
    element: Optional[str] = None,
    weapon_type: Optional[str] = None,
    star: Optional[int] = None,
) -> str:
    """查询并筛选原神角色图鉴（游戏全角色，不需要 UID）。

    问「有哪些火系长柄 / 5 星弓 / 稻妻雷系」用本工具。这是图鉴，不是用户自己的箱。
    用户练度走 get_user_genshin_char_list；看某角色面板图走触发器「查询 角色名」。

    Args:
        element: 元素。可选 风/火/水/雷/冰/岩/草 或 Anemo/Pyro 等。留空不限。
        weapon_type: 武器类型。可选 单手剑/双手剑/长柄武器/法器/弓（也可用 剑/大剑/枪/书）。
        star: 星级 4 或 5。留空不限。
    """
    _ = ctx
    want_el = normalize_element(element) if element else ""
    want_wp = normalize_weapon_type(weapon_type) if weapon_type else ""
    rows: list[str] = ["| 角色 | 星 | 元素 | 武器 | 地区 |", "|---|---|---|---|---|"]
    count = 0
    for item in charList.values():
        entry = _char_entry(item)
        if entry is None:
            continue
        name = as_str(entry["name"])
        if name == "旅行者":
            continue
        el = element_zh(as_str(entry["element"])) if "element" in entry and entry["element"] else "-"
        wp = weapon_type_zh(as_str(entry["weaponType"]))
        rank = as_int(entry["rank"]) if "rank" in entry else 0
        if want_el and el != want_el:
            continue
        if want_wp and wp != want_wp:
            continue
        if star is not None and rank != star:
            continue
        region = region_zh(as_str(entry["region"])) if "region" in entry else "-"
        rows.append(f"| {name} | {rank} | {el} | {wp} | {region} |")
        count += 1
    if count == 0:
        return f"无匹配角色（element={element} weapon_type={weapon_type} star={star}）"
    return f"匹配 {count} 名角色:\n" + "\n".join(rows)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=["按类型/星级筛选原神武器图鉴：名称、副属性"],
    aliases=["原神·武器图鉴", "原神·武器筛选"],
)
async def filter_genshin_weapons(
    ctx: RunContext[ToolContext],
    weapon_type: Optional[str] = None,
    star: Optional[int] = None,
    name: str = "",
) -> str:
    """查询并筛选原神武器图鉴（游戏全武器，不需要 UID）。

    问「有哪些 5 星长柄 / 雾切是什么武器」用本工具。用户自己装备的武器见角色面板数值工具。

    Args:
        weapon_type: 单手剑/双手剑/长柄武器/法器/弓。留空不限。
        star: 星级 3/4/5。留空不限。
        name: 可选名称子串，如 "雾切"、"猎人之径"。
    """
    _ = ctx
    want_wp = normalize_weapon_type(weapon_type) if weapon_type else ""
    keyword = name.strip()
    rows: list[str] = ["| 武器 | 星 | 类型 | 副属性 |", "|---|---|---|---|"]
    count = 0
    for item in weaponList.values():
        if not isinstance(item, dict) or "name" not in item or "type" not in item:
            continue
        if "isWeaponSkin" in item and item["isWeaponSkin"] is True:
            continue
        wname = as_str(item["name"])
        wp = weapon_type_zh(as_str(item["type"]))
        rank = as_int(item["rank"]) if "rank" in item else 0
        if want_wp and wp != want_wp:
            continue
        if star is not None and rank != star:
            continue
        if keyword and keyword not in wname:
            continue
        prop = as_str(item["specialProp"]) if "specialProp" in item else ""
        rows.append(f"| {wname} | {rank} | {wp} | {prop} |")
        count += 1
        if count >= 80:
            break
    if count == 0:
        return f"无匹配武器（weapon_type={weapon_type} star={star} name={name}）"
    extra = "（已截断到 80）" if count >= 80 else ""
    return f"匹配 {count} 件武器{extra}:\n" + "\n".join(rows)


@ai_tools(
    category="common",
    context_tags=_CTX,
    capability_domain=_DOMAIN,
    covers=["查询原神圣遗物套装图鉴：2件/4件套效果"],
    aliases=["原神·圣遗物图鉴", "原神·套装效果"],
)
async def filter_genshin_artifact_sets(
    ctx: RunContext[ToolContext],
    name: str = "",
    limit: int = 20,
) -> str:
    """查询原神圣遗物套装图鉴与 2/4 件套效果（不需要 UID）。

    问「绝缘四件什么效果 / 魔女套适合谁的机制」用本工具。用户身上已装备的件走 get_user_genshin_artifacts。

    Args:
        name: 套装名或子串，如 "绝缘"、"魔女"、"追忆"。留空列出常见 5 星套（截断）。
        limit: 留空列举时的条数上限，默认 20，最大 40。
    """
    _ = ctx
    keyword = name.strip()
    cap = min(max(limit, 1), 40)
    blocks: list[str] = []
    for item in reliquaryList.values():
        if not isinstance(item, dict) or "name" not in item:
            continue
        set_name = as_str(item["name"])
        levels = item["levelList"] if "levelList" in item and isinstance(item["levelList"], list) else []
        if 5 not in levels and not keyword:
            continue
        if keyword and keyword not in set_name:
            continue
        affix = item["affixList"] if "affixList" in item and isinstance(item["affixList"], dict) else {}
        effects = [as_str(v) for v in affix.values()]
        body = f"## {set_name}\n"
        if len(effects) >= 1:
            body += f"- 2件：{effects[0]}\n"
        if len(effects) >= 2:
            body += f"- 4件：{effects[1]}\n"
        blocks.append(body.rstrip())
        if not keyword and len(blocks) >= cap:
            break
        if keyword and len(blocks) >= cap:
            break
    if not blocks:
        return f"未找到圣遗物套装：{name or '（空查询）'}"
    return "\n\n".join(blocks)
