"""
武器数据解析器
负责将武器JSON数据解析为RAG知识块
"""

from typing import Dict, List

from gsuid_core.ai_core.models import KnowledgePoint

from .utils import clean_html_tags
from .models import WeaponInfo
from .constants import WEAPON_MAP, FIGHT_PROP_MAP


def parse_weapon_json(json_data: Dict) -> List[KnowledgePoint]:
    """
    解析武器JSON数据为RAG知识块

    Args:
        json_data: 武器原始JSON数据

    Returns:
        知识块列表
    """
    if not json_data or not isinstance(json_data, dict):
        return []

    # 解析武器基础信息
    weapon_info = WeaponInfo.from_dict(json_data)

    # 构建全局Header
    global_header = (
        f"【武器情报】\n"
        f"武器：{weapon_info.name} | ID：{weapon_info.id}\n"
        f"类型：{weapon_info.type.value} | 星级：{weapon_info.rank}星\n"
        f"---\n"
    )

    knowledge_points: List[KnowledgePoint] = []

    # ==================== 块 1：武器基础信息 ====================
    weapon_content = (
        global_header + f"# {weapon_info.name} 基础信息\n\n"
        f"## 基本信息\n"
        f"- **武器类型**：{weapon_info.type.value}\n"
        f"- **稀有度**：{weapon_info.rank}星\n"
        f"- **武器ID**：{weapon_info.id}\n"
    )

    # 添加武器描述
    if json_data.get("description"):
        weapon_content += f"\n## 武器描述\n{clean_html_tags(json_data.get('description', ''))}\n"

    # 添加武器故事
    if json_data.get("story"):
        weapon_content += f"\n## 武器故事\n{clean_html_tags(json_data.get('story', ''))}\n"

    knowledge_points.append(
        {
            "id": f"weapon_{weapon_info.id}_info",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "weapon_info",
            "title": f"{weapon_info.name}-基础信息",
            "content": weapon_content,
            "tags": ["武器", "基础信息", weapon_info.name],
            "_hash": "",
        }
    )

    # ==================== 块 2：武器基础属性 ====================
    base_stats = json_data.get("weaponStats", [])
    if base_stats:
        stats_content = global_header + f"# {weapon_info.name} 基础属性\n\n## 基础属性表\n"

        for stat in base_stats:
            level = stat.get("level", 1)
            base_atk = stat.get("baseAtk", 0)
            prop_type = stat.get("propType", "")
            prop_value = stat.get("propValue", 0)

            stats_content += f"- **等级 {level}**：基础攻击力 {base_atk}"
            if prop_type and prop_value:
                prop_name = FIGHT_PROP_MAP.get(prop_type, prop_type)
                stats_content += f"，{prop_name} {prop_value}"
            stats_content += "\n"

        knowledge_points.append(
            {
                "id": f"weapon_{weapon_info.id}_stats",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "weapon_stats",
                "title": f"{weapon_info.name}-基础属性",
                "content": stats_content,
                "tags": ["武器", "属性", weapon_info.name],
                "_hash": "",
            }
        )

    # ==================== 块 3：武器主属性信息 ====================
    # 查找主属性（通常是最高等级的基础属性）
    main_prop_type = ""
    main_prop_name = ""
    max_level = 0

    if base_stats:
        for stat in base_stats:
            level = stat.get("level", 1)
            prop_type = stat.get("propType", "")
            if level > max_level and prop_type:
                max_level = level
                main_prop_type = prop_type
                main_prop_name = FIGHT_PROP_MAP.get(prop_type, prop_type)

    if main_prop_type and main_prop_name:
        main_prop_content = (
            global_header + f"# {weapon_info.name} 主属性信息\n\n"
            f"## 主属性\n"
            f"- **主属性类型**：{main_prop_name}\n"
            f"- **主属性ID**：{main_prop_type}\n"
            f"- **适用武器类型**：{weapon_info.type.value}\n"
        )

        # 添加主属性说明
        main_prop_explanation = {
            "FIGHT_PROP_CRITICAL_HURT": "暴击伤害 - 提升角色暴击时造成的伤害",
            "FIGHT_PROP_CRITICAL": "暴击率 - 提升角色暴击的概率",
            "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率 - 提升元素爆发的充能速度",
            "FIGHT_PROP_ELEMENT_MASTERY": "元素精通 - 提升元素反应的伤害",
            "FIGHT_PROP_ATTACK_PERCENT": "攻击力 - 提升角色的基础攻击力",
            "FIGHT_PROP_DEFENSE_PERCENT": "防御力 - 提升角色的基础防御力",
            "FIGHT_PROP_HP_PERCENT": "生命值 - 提升角色的基础生命值",
        }

        explanation = main_prop_explanation.get(main_prop_type, "特殊属性")
        main_prop_content += f"\n## 属性说明\n{explanation}\n"

        # 添加主属性查询标签，便于RAG系统检索
        main_prop_tags = ["武器", "主属性", main_prop_name, weapon_info.name]
        if "暴击伤害" in main_prop_name:
            main_prop_tags.extend(["暴击伤害", "暴击"])
        elif "暴击率" in main_prop_name:
            main_prop_tags.extend(["暴击率", "暴击"])
        elif "元素充能效率" in main_prop_name:
            main_prop_tags.extend(["充能", "元素爆发"])
        elif "元素精通" in main_prop_name:
            main_prop_tags.extend(["精通", "元素反应"])

        knowledge_points.append(
            {
                "id": f"weapon_{weapon_info.id}_mainprop",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "weapon_mainprop",
                "title": f"{weapon_info.name}-主属性",
                "content": main_prop_content,
                "tags": main_prop_tags,
                "_hash": "",
            }
        )

    # ==================== 块 4：武器精炼效果 ====================
    affix_data = json_data.get("weaponAffix", [])
    if affix_data:
        affix_content = global_header + f"# {weapon_info.name} 精炼效果\n\n## 精炼等级效果\n"

        for affix in affix_data:
            name = affix.get("affixName", "")
            desc = clean_html_tags(affix.get("affixDesc", ""))
            level = affix.get("effect", 1)

            affix_content += f"### R{level}：{name}\n{desc}\n\n"

        knowledge_points.append(
            {
                "id": f"weapon_{weapon_info.id}_affix",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "weapon_affix",
                "title": f"{weapon_info.name}-精炼效果",
                "content": affix_content,
                "tags": ["武器", "精炼", weapon_info.name],
                "_hash": "",
            }
        )

    return knowledge_points


def build_weapon_global_summary_kp(all_weapons_data: List[Dict]) -> KnowledgePoint:
    """生成武器全局汇总知识块"""

    # 按武器类型分类
    weapon_type_dict: Dict[str, List[str]] = {
        "单手剑": [],
        "双手剑": [],
        "长柄武器": [],
        "法器": [],
        "弓箭": [],
    }

    # 按星级分类
    star_dict: Dict[str, List[str]] = {
        "1星": [],
        "2星": [],
        "3星": [],
        "4星": [],
        "5星": [],
    }

    # 按主属性分类（用于回答主属性相关问题）
    main_prop_dict: Dict[str, List[str]] = {
        "暴击伤害": [],
        "暴击率": [],
        "元素充能效率": [],
        "元素精通": [],
        "攻击力": [],
        "防御力": [],
        "生命值": [],
    }

    for weapon in all_weapons_data:
        name = weapon.get("name", "未知武器")

        # 武器类型分类
        weapon_type = WEAPON_MAP.get(weapon.get("weaponType", ""), "未知")
        if weapon_type in weapon_type_dict:
            weapon_type_dict[weapon_type].append(name)

        # 星级分类
        rarity = weapon.get("rank", 3)
        star_dict[f"{rarity}星"].append(name)

        # 主属性分类（需要从武器数据中获取主属性信息）
        # 这里简化处理，实际应用中需要解析武器数据
        if weapon.get("weaponType") == "WEAPON_CATALYST":  # 法器
            main_prop_dict["暴击伤害"].append(name)  # 假设法器主属性多为暴击伤害

    # 构建汇总文本
    summary_text = "# 原神全武器分类全局汇总\n\n"
    summary_text += "> 本知识块包含所有武器的类型、星级、主属性分类统计，用于回答武器相关查询问题。\n\n"

    # 武器类型统计
    summary_text += "## 按武器类型分类\n\n"
    for weapon_type, names in weapon_type_dict.items():
        summary_text += f"### {weapon_type} (共 {len(names)} 把)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    # 星级统计
    summary_text += "## 按星级分类\n\n"
    for star, names in star_dict.items():
        summary_text += f"### {star}武器 (共 {len(names)} 把)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    # 主属性统计
    summary_text += "## 按主属性分类\n\n"
    for prop, names in main_prop_dict.items():
        summary_text += f"### {prop}武器 (共 {len(names)} 把)\n"
        if names:
            summary_text += f"包含：{', '.join(sorted(names))}\n"
        summary_text += "\n"

    return {
        "id": "global_summary_all_weapons",
        "plugin": "genshin",
        "type": "knowledge",
        "category": "weapon_summary",
        "title": "原神全武器分类统计汇总",
        "content": summary_text,
        "tags": ["武器", "统计", "汇总", "类型", "星级", "主属性"],
        "_hash": "",
    }
