"""
武器数据解析器
负责将武器JSON数据解析为RAG知识块
"""

from typing import Dict, List

from .utils import clean_html_tags
from .models import WeaponInfo, GsKnowledgePoint, make_kp
from .constants import WEAPON_MAP, FIGHT_PROP_MAP


def parse_weapon_json(json_data: Dict) -> List[GsKnowledgePoint]:
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

    knowledge_points: List[GsKnowledgePoint] = []

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
        make_kp(
            id=f"weapon_{weapon_info.id}_info",
            title=f"{weapon_info.name}-基础信息",
            content=weapon_content,
            tags=["武器", "基础信息", weapon_info.name],
            type="knowledge",
            category="weapon_info",
            entity=weapon_info.name,
            _hash="",
        )
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
            make_kp(
                id=f"weapon_{weapon_info.id}_stats",
                title=f"{weapon_info.name}-基础属性",
                content=stats_content,
                tags=["武器", "属性", weapon_info.name],
                type="knowledge",
                category="weapon_stats",
                entity=weapon_info.name,
                _hash="",
            )
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
            make_kp(
                id=f"weapon_{weapon_info.id}_mainprop",
                title=f"{weapon_info.name}-主属性",
                content=main_prop_content,
                tags=main_prop_tags,
                type="knowledge",
                category="weapon_mainprop",
                entity=weapon_info.name,
                _hash="",
            )
        )

    # ==================== 块 4：武器精炼效果 ====================
    affix_data = json_data.get("affix", {})
    if affix_data:
        # 获取第一个affix的key（通常是 "112515" 这种格式）
        first_affix_key = next(iter(affix_data.keys()), "")
        affix_info = affix_data.get(first_affix_key, {})

        affix_name = affix_info.get("name", "")
        upgrade_data = affix_info.get("upgrade", {})

        if upgrade_data:
            affix_content = global_header + f"# {weapon_info.name} 精炼效果\n\n"

            if affix_name:
                affix_content += f"## 特效名称：{affix_name}\n\n"

            affix_content += "## 精炼等级效果\n\n"

            # 解析精炼等级 0-4 对应 R1-R5
            for level in range(5):
                level_key = str(level)
                if level_key in upgrade_data:
                    desc = clean_html_tags(upgrade_data[level_key])
                    r_level = level + 1  # 0->R1, 4->R5
                    affix_content += f"### 精炼等阶 {r_level}\n{desc}\n\n"

            knowledge_points.append(
                make_kp(
                    id=f"weapon_{weapon_info.id}_affix",
                    title=f"{weapon_info.name}-精炼效果",
                    content=affix_content,
                    tags=["武器", "精炼", weapon_info.name, affix_name],
                    type="knowledge",
                    category="weapon_affix",
                    entity=weapon_info.name,
                    _hash="",
                )
            )

    # 保留对旧格式 weaponAffix 的支持
    old_affix_data = json_data.get("weaponAffix", [])
    if old_affix_data and not affix_data:
        affix_content = global_header + f"# {weapon_info.name} 精炼效果\n\n## 精炼等级效果\n"

        for affix in old_affix_data:
            name = affix.get("affixName", "")
            desc = clean_html_tags(affix.get("affixDesc", ""))
            level = affix.get("effect", 1)

            affix_content += f"### R{level}：{name}\n{desc}\n\n"

        knowledge_points.append(
            make_kp(
                id=f"weapon_{weapon_info.id}_affix",
                title=f"{weapon_info.name}-精炼效果",
                content=affix_content,
                tags=["武器", "精炼", weapon_info.name],
                type="knowledge",
                category="weapon_affix",
                entity=weapon_info.name,
                _hash="",
            )
        )

    # ==================== 块 5：武器数值对比信息 ====================
    # 提取关键数值用于对比分析
    max_level_stat = None
    if base_stats:
        for stat in base_stats:
            level = stat.get("level", 1)
            if max_level_stat is None or level > max_level_stat.get("level", 0):
                max_level_stat = stat

    if max_level_stat:
        base_atk = max_level_stat.get("baseAtk", 0)
        prop_type = max_level_stat.get("propType", "")
        prop_value = max_level_stat.get("propValue", 0)
        prop_name = FIGHT_PROP_MAP.get(prop_type, prop_type)

        # 精炼效果摘要
        affix_summary = ""

        # 首先尝试新格式的affix字段
        new_affix_data = json_data.get("affix", {})
        if new_affix_data:
            first_affix_key = next(iter(new_affix_data.keys()), "")
            affix_info = new_affix_data.get(first_affix_key, {})
            upgrade_data = affix_info.get("upgrade", {})

            # 获取R1和R5的描述
            r1_desc = upgrade_data.get("0", "")
            r5_desc = upgrade_data.get("4", "")

            if r1_desc:
                affix_summary += f"R1：{clean_html_tags(r1_desc)}"
            if r5_desc:
                affix_summary += f" | R5：{clean_html_tags(r5_desc)}"

        # 如果没有新格式数据，尝试旧格式的weaponAffix字段
        if not affix_summary:
            old_affix_data = json_data.get("weaponAffix", [])
            if old_affix_data:
                r1_affix = old_affix_data[0] if old_affix_data else None
                r5_affix = old_affix_data[-1] if len(old_affix_data) >= 5 else None
                if r1_affix:
                    affix_summary += f"R1：{clean_html_tags(r1_affix.get('affixDesc', ''))}"
                if r5_affix and len(old_affix_data) >= 5:
                    affix_summary += f" | R5：{clean_html_tags(r5_affix.get('affixDesc', ''))}"

        comparison_content = (
            global_header + f"# {weapon_info.name} 数值对比信息\n\n"
            f"## 核心数值（用于武器对比）\n"
            f"- **武器名称**：{weapon_info.name}\n"
            f"- **武器星级**：{weapon_info.rank}星\n"
            f"- **武器类型**：{weapon_info.type.value}\n"
            f"- **满级基础攻击力**：{base_atk}\n"
            f"- **满级副属性类型**：{prop_name}\n"
            f"- **满级副属性数值**：{prop_value}\n\n"
        )

        # 添加精炼效果
        if affix_summary:
            comparison_content += f"## 精炼效果摘要\n{affix_summary}\n\n"

        # 添加对比分析说明
        comparison_content += (
            f"## 武器对比分析要点\n"
            f"- **基础攻击力**：{base_atk}（{weapon_info.rank}星武器基准）\n"
            f"- **副属性**：{prop_name} {prop_value}\n"
            f"- **适用场景**：根据精炼效果和属性搭配分析\n"
        )

        # 构建tags列表，确保没有None值
        comparison_tags: List[str] = ["武器", "对比", "数值"]
        if weapon_info.name:
            comparison_tags.append(weapon_info.name)
        if prop_name:
            comparison_tags.append(prop_name)
        comparison_tags.append(f"{weapon_info.rank}星")

        knowledge_points.append(
            make_kp(
                id=f"weapon_{weapon_info.id}_comparison",
                title=f"{weapon_info.name}-数值对比信息",
                content=comparison_content,
                tags=comparison_tags,
                type="knowledge",
                category="weapon_comparison",
                entity=weapon_info.name,
                _hash="",
            )
        )

    return knowledge_points


def build_weapon_global_summary_kp(all_weapons_data: List[Dict]) -> GsKnowledgePoint:
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

    return make_kp(
        id="global_summary_all_weapons",
        title="原神全武器分类统计汇总",
        content=summary_text,
        tags=["武器", "统计", "汇总", "类型", "星级", "主属性"],
        type="knowledge",
        category="weapon_summary",
        _hash="",
    )


def build_weapon_comparison_summary_kp(all_weapons_data: List[Dict]) -> GsKnowledgePoint:
    """生成武器数值对比汇总知识块，用于回答武器强度对比问题"""

    # 按星级分类的武器数值汇总
    star_weapon_stats: Dict[str, List[Dict]] = {
        "5星": [],
        "4星": [],
    }

    for weapon in all_weapons_data:
        name = weapon.get("name", "未知武器")
        rank = weapon.get("rank", 3)
        weapon_stats = weapon.get("weaponStats", [])

        # 获取满级数据
        max_level_stat = None
        for stat in weapon_stats:
            level = stat.get("level", 1)
            if max_level_stat is None or level > max_level_stat.get("level", 0):
                max_level_stat = stat

        if max_level_stat:
            base_atk = max_level_stat.get("baseAtk", 0)
            prop_type = max_level_stat.get("propType", "")
            prop_value = max_level_stat.get("propValue", 0)
            prop_name = FIGHT_PROP_MAP.get(prop_type, prop_type)

            weapon_data = {
                "name": name,
                "base_atk": base_atk,
                "prop_name": prop_name,
                "prop_value": prop_value,
            }

            if rank >= 5:
                star_weapon_stats["5星"].append(weapon_data)
            elif rank == 4:
                star_weapon_stats["4星"].append(weapon_data)

    # 构建对比汇总文本
    comparison_text = "# 原神武器数值对比汇总\n\n"
    comparison_text += "> 本知识块包含所有武器的数值信息，用于回答武器强度对比、强多少等问题。\n\n"

    # 5星武器数值汇总
    comparison_text += "## 5星武器数值汇总\n\n"
    comparison_text += "| 武器名称 | 满级基础攻击力 | 副属性 | 副属性数值 |\n"
    comparison_text += "|---------|-------------|-------|----------|\n"
    for weapon in sorted(star_weapon_stats["5星"], key=lambda x: x["base_atk"], reverse=True):
        comparison_text += (
            f"| {weapon['name']} | {weapon['base_atk']} | {weapon['prop_name']} | {weapon['prop_value']}% |\n"
        )
    comparison_text += "\n"

    # 4星武器数值汇总
    comparison_text += "## 4星武器数值汇总\n\n"
    comparison_text += "| 武器名称 | 满级基础攻击力 | 副属性 | 副属性数值 |\n"
    comparison_text += "|---------|-------------|-------|----------|\n"
    for weapon in sorted(star_weapon_stats["4星"], key=lambda x: x["base_atk"], reverse=True):
        comparison_text += (
            f"| {weapon['name']} | {weapon['base_atk']} | {weapon['prop_name']} | {weapon['prop_value']}% |\n"
        )
    comparison_text += "\n"

    # 添加武器对比分析方法
    comparison_text += "## 武器强度对比分析方法\n\n"
    comparison_text += "### 1. 基础攻击力对比\n"
    comparison_text += "- 5星武器满级基础攻击力范围：542-741\n"
    comparison_text += "- 4星武器满级基础攻击力范围：454-620\n"
    comparison_text += "- 同星级武器，基础攻击力差异约为10-15%\n\n"
    comparison_text += "### 2. 副属性对比\n"
    comparison_text += "- 暴击伤害：最高66.2%（5星）/ 37.7%（4星）\n"
    comparison_text += "- 暴击率：最高33.1%（5星）/ 36.8%（4星）\n"
    comparison_text += "- 元素充能效率：最高55.1%（4星）\n"
    comparison_text += "- 元素精通：最高221（4星）\n\n"
    comparison_text += "### 3. 精炼效果对比\n"
    comparison_text += "- 精炼等级R1→R5，效果提升约50-100%\n"
    comparison_text += "- 高精炼4星武器可媲美低精炼5星武器\n"

    return make_kp(
        id="global_weapon_comparison_summary",
        title="原神武器数值对比汇总",
        content=comparison_text,
        tags=["武器", "对比", "数值", "强度", "攻击力", "副属性", "精炼"],
        type="knowledge",
        category="weapon_comparison_summary",
        _hash="",
    )
