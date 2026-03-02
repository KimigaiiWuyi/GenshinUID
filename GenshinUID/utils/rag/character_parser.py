"""
角色数据解析器
负责将角色JSON数据解析为RAG知识块
"""

from typing import Dict, List

from gsuid_core.ai_core.models import KnowledgePoint

from .utils import clean_html_tags, format_birthday, determine_skill_type, build_skill_multiplier_table
from .models import CharacterInfo
from .constants import WEAPON_MAP, ELEMENT_MAP


def parse_character_json(json_data: Dict) -> List[KnowledgePoint]:
    """
    主解析函数：将角色 JSON 数据解析为 RAG 知识块

    Args:
        json_data: 角色原始 JSON 数据

    Returns:
        知识块列表，每个块包含 id, plugin, category, title, content
    """
    # 数据验证
    if not json_data or not isinstance(json_data, dict):
        return []

    # 解析角色基础信息
    char_info = CharacterInfo.from_dict(json_data)

    # 构建全局 Header，每个知识块都会包含此信息
    global_header = (
        f"【基本情报】\n"
        f"角色：{char_info.name} | ID：{char_info.id}\n"
        f"属性：{char_info.element} | 武器：{char_info.weapon}\n"
        f"稀有度：{char_info.rank}星 | 地区：{char_info.region}\n"
        f"---\n"
    )

    knowledge_points: List[KnowledgePoint] = []

    # ==================== 块 1：基础档案 ====================
    fetter = json_data.get("fetter", {})
    cv = fetter.get("cv", {})

    profile_content = (
        global_header + f"# {char_info.name} 基础档案\n\n"
        f"## 基本信息\n"
        f"- **称号**：{fetter.get('title', '未知')}\n"
        f"- **命之座**：{fetter.get('constellation', '未知')}\n"
        f"- **所属地区**：{fetter.get('native', '未知')}\n"
        f"- **生日**：{format_birthday(json_data.get('birthday'))}\n"
        f"\n## 背景介绍\n"
        f"{clean_html_tags(fetter.get('detail', ''))}\n"
        f"\n## 配音 (CV)\n"
        f"- 中文：{cv.get('CHS', '-')}\n"
        f"- 英文：{cv.get('EN', '-')}\n"
        f"- 日文：{cv.get('JP', '-')}\n"
        f"- 韩文：{cv.get('KR', '-')}\n"
    )

    knowledge_points.append(
        {
            "id": f"char_{char_info.id}_profile",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "profile",
            "title": f"{char_info.name}-基础档案",
            "content": profile_content,
            "tags": ["角色", "档案", char_info.name],
            "_hash": "",
        }
    )

    # ==================== 块 2：技能与天赋 ====================
    talent_data = json_data.get("talent", {})
    skill_texts = [global_header + f"# {char_info.name} 战斗技能与天赋机制\n\n"]

    # 按键名排序遍历（0,1,2,3,...）
    for key in sorted(talent_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        t = talent_data[key]
        if not isinstance(t, dict):
            continue

        t_name = t.get("name", "未知技能")
        t_desc = clean_html_tags(t.get("description", ""))
        promote = t.get("promote")
        cooldown = t.get("cooldown")
        cost = t.get("cost")

        # 智能推导技能类型
        skill_type = determine_skill_type(key, t_desc, promote)

        skill_section = f"## 【{skill_type}】{t_name}\n\n"

        # 添加技能描述
        if t_desc:
            skill_section += f"{t_desc}\n\n"

        # 添加技能属性（冷却时间、能量消耗等）
        attr_parts = []
        if cooldown is not None:
            attr_parts.append(f"冷却时间：{cooldown}秒")
        if cost is not None and cost > 0:
            attr_parts.append(f"元素能量：{cost}")
        if attr_parts:
            skill_section += f"**技能属性**：{' | '.join(attr_parts)}\n\n"

        # 添加倍率表
        if promote and isinstance(promote, dict):
            table = build_skill_multiplier_table(promote)
            if table:
                skill_section += f"**各等级伤害倍率与属性表：**\n\n{table}\n\n"

        skill_texts.append(skill_section)

    knowledge_points.append(
        {
            "id": f"char_{char_info.id}_skill",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "skill",
            "title": f"{char_info.name}-技能与倍率",
            "content": "\n".join(skill_texts),
            "tags": ["角色", "技能", char_info.name],
            "_hash": "",
        }
    )

    # ==================== 块 3：命之座 ====================
    const_data = json_data.get("constellation", {}) or {}
    const_texts = [global_header + f"# {char_info.name} 命之座效果\n\n"]

    # 命之座索引通常是 "0" 到 "5"，对应第1到第6命
    for i in range(6):
        c_key = str(i)
        c = const_data.get(c_key, {})
        if not c:
            continue

        c_name = c.get("name", f"第{i + 1}命")
        c_desc = clean_html_tags(c.get("description", ""))
        const_texts.append(f"## 第{i + 1}命：{c_name}\n\n{c_desc}\n\n")

    knowledge_points.append(
        {
            "id": f"char_{char_info.id}_constellation",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "constellation",
            "title": f"{char_info.name}-命之座",
            "content": "\n".join(const_texts),
            "tags": ["角色", "命之座", char_info.name],
            "_hash": "",
        }
    )

    return knowledge_points


def build_global_summary_kp(all_characters_data: List[Dict]) -> KnowledgePoint:
    """生成全局汇总知识块，用于回答统计类问题

    例如："单手剑角色有多少个？"、"所有火元素角色有哪些？"
    """
    # 按武器类型分类
    weapon_dict: Dict[str, List[str]] = {
        "单手剑": [],
        "双手剑": [],
        "长柄武器": [],
        "法器": [],
        "弓箭": [],
    }

    # 按元素类型分类
    element_dict: Dict[str, List[str]] = {
        "水元素": [],
        "火元素": [],
        "风元素": [],
        "雷元素": [],
        "冰元素": [],
        "岩元素": [],
        "草元素": [],
    }

    # 星级统计
    star_dict: Dict[str, List[str]] = {"5星": [], "4星": []}

    for char in all_characters_data:
        name = char.get("name", "未知")

        # 武器分类
        weapon_type = WEAPON_MAP.get(char.get("weaponType", ""), "未知")
        if weapon_type in weapon_dict:
            weapon_dict[weapon_type].append(name)

        # 元素分类
        element = ELEMENT_MAP.get(char.get("element", ""), "未知")
        if element in element_dict:
            element_dict[element].append(name)

        # 星级分类
        rarity = char.get("rarity", 4)
        if rarity == 5 or rarity == "5":
            star_dict["5星"].append(name)
        else:
            star_dict["4星"].append(name)

    # 构建汇总文本
    summary_text = "# 原神全角色分类全局汇总\n\n"
    summary_text += "> 本知识块包含所有角色的武器、元素、星级分类统计，用于回答角色数量统计类问题。\n\n"

    # 武器统计
    summary_text += "## 按武器类型分类\n\n"
    for weapon_type, names in weapon_dict.items():
        summary_text += f"### {weapon_type}角色 (共 {len(names)} 名)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    # 元素统计
    summary_text += "## 按元素类型分类\n\n"
    for element, names in element_dict.items():
        summary_text += f"### {element}角色 (共 {len(names)} 名)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    # 星级统计
    summary_text += "## 按稀有度分类\n\n"
    for star, names in star_dict.items():
        summary_text += f"### {star}角色 (共 {len(names)} 名)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    # 构建知识块
    return {
        "id": "global_summary_all_characters",
        "plugin": "genshin",
        "type": "knowledge",
        "category": "summary",
        "title": "原神全角色分类统计汇总",
        "content": summary_text,
        "tags": ["角色", "统计", "汇总", "武器", "元素", "星级"],
        "_hash": "",
    }
