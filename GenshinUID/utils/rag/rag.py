"""
原神角色数据 RAG 解析脚本
功能：将角色 JSON 数据解析为结构化的知识块，适用于 RAG 系统
"""

import re
import json
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from gsuid_core.ai_core.models import KnowledgePoint
from gsuid_core.ai_core.register import ai_entity

from ..resource.RESOURCE_PATH import CHAR_DATA_PATH

# ==================== 枚举与常量 ====================


class SkillType(Enum):
    """技能类型枚举"""

    NORMAL_ATTACK = "普通攻击(A)"
    ELEMENTAL_SKILL = "元素战技(E)"
    ELEMENTAL_BURST = "元素爆发(Q)"
    PASSIVE = "被动天赋"


# ==================== 字典映射 ====================

ELEMENT_MAP = {
    "Water": "水元素",
    "Fire": "火元素",
    "Wind": "风元素",
    "Electric": "雷元素",
    "Ice": "冰元素",
    "Rock": "岩元素",
    "Grass": "草元素",
}

WEAPON_MAP = {
    "WEAPON_CLAYMORE": "双手剑",
    "WEAPON_SWORD": "单手剑",
    "WEAPON_SWORD_ONE_HAND": "单手剑",
    "WEAPON_POLE": "长柄武器",
    "WEAPON_CATALYST": "法器",
    "WEAPON_BOW": "弓箭",
}

FIGHT_PROP_MAP = {
    "FIGHT_PROP_BASE_HP": "基础生命值",
    "FIGHT_PROP_BASE_ATTACK": "基础攻击力",
    "FIGHT_PROP_BASE_DEFENSE": "基础防御力",
    "FIGHT_PROP_CRITICAL": "暴击率",
    "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率",
    "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
    "FIGHT_PROP_HEAL_BONUS": "治疗加成",
}

# 技能键名映射（用于快速识别技能类型）
SKILL_KEY_MAP = {"0": SkillType.NORMAL_ATTACK, "1": SkillType.ELEMENTAL_SKILL, "2": SkillType.ELEMENTAL_BURST}


# ==================== 数据类 ====================


@dataclass
class CharacterInfo:
    """角色基础信息"""

    id: str
    name: str
    element: str
    weapon: str
    rank: int
    region: str
    route: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterInfo":
        """从字典创建角色信息"""
        element_raw = data.get("element", "")
        weapon_raw = data.get("weaponType", "")

        element = ELEMENT_MAP.get(element_raw, element_raw) or "未知元素"
        weapon = WEAPON_MAP.get(weapon_raw, weapon_raw) or "未知武器"

        return cls(
            id=str(data.get("id", "unknown")),
            name=data.get("name", "未知角色"),
            element=element,
            weapon=weapon,
            rank=data.get("rank", 0),
            region=data.get("region", ""),
            route=data.get("route", ""),
        )


# ==================== 工具函数 ====================


def clean_html_tags(text: str) -> str:
    """
    清理 JSON 中的 HTML 标签和特殊格式

    Args:
        text: 原始文本

    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""

    # 移除颜色标签
    text = re.sub(r"<color=.*?>|</color>", "", text)
    # 移除链接标签
    text = re.sub(r"{LINK#.*?}|{/LINK}", "", text)
    # 将 \n 替换为真实的换行
    text = text.replace("\\n", "\n")
    # 移除多余的连续空格
    text = re.sub(r" +", " ", text)

    return text.strip()


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """
    安全获取嵌套字典的值

    Args:
        data: 字典
        *keys: 键层路径
        default: 默认值

    Returns:
        值或默认值
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def format_param_value(val: float, fmt: str) -> str:
    """
    根据解包数据的占位符格式（如 F1P, I, F1）格式化浮点数

    Args:
        val: 参数值
        fmt: 格式字符串

    Returns:
        格式化后的字符串
    """
    try:
        val = float(val)

        if "P" in fmt:
            # P代表百分比 (Percentage)
            if "F1" in fmt:
                return f"{val * 100:.1f}%"
            if "F2" in fmt:
                return f"{val * 100:.2f}%"
            return f"{val * 100:.1f}%"
        elif "I" in fmt:
            # I代表整数 (Integer)
            return f"{int(val)}"
        elif "F1" in fmt:
            # F1代表保留1位小数的浮点数
            return f"{val:.1f}"
        elif "F2" in fmt:
            return f"{val:.2f}"
        elif "F3" in fmt:
            return f"{val:.3f}"
        else:
            return str(round(val, 2))
    except (ValueError, TypeError, OverflowError):
        return str(val)


def format_birthday(birthday: Any) -> str:
    """
    格式化生日数据

    Args:
        birthday: 生日数据 [月, 日]

    Returns:
        格式化的生日字符串
    """
    if birthday and isinstance(birthday, (list, tuple)) and len(birthday) >= 2:
        return f"{birthday[0]}月{birthday[1]}日"
    return "未知"


# ==================== 核心解析函数 ====================


def determine_skill_type(talent_key: str, t_desc: str, promote_dict: Optional[Dict]) -> SkillType:
    """
    通过解析文本、键名和成长数据，智能判断技能按键

    Args:
        talent_key: 天赋键名（如 "0", "1", "2" 等）
        t_desc: 技能描述
        promote_dict: 升级数据字典

    Returns:
        SkillType 枚举
    """
    # 1. 首先根据键名快速判断
    if talent_key in SKILL_KEY_MAP:
        return SKILL_KEY_MAP[talent_key]

    # 2. 普攻 (A)：描述中通常直接包含 "普通攻击"
    if t_desc and "普通攻击" in t_desc:
        return SkillType.NORMAL_ATTACK

    # 3. 元素爆发 (Q)：大招的特征是升级数据里一定有一项叫 "元素能量"
    if promote_dict and isinstance(promote_dict, dict):
        level_1_data = promote_dict.get("1", {})
        desc_list = safe_get(level_1_data, "description", default=[])
        if any("元素能量" in d for d in desc_list if isinstance(d, str)):
            return SkillType.ELEMENTAL_BURST

    # 4. 元素战技 (E)：有成长数据，但不是普攻也不是大招，那就是 E 技能
    if promote_dict:
        return SkillType.ELEMENTAL_SKILL

    return SkillType.PASSIVE


def build_skill_multiplier_table(promote_dict: Dict) -> str:
    """
    动态将 1~15 级技能的倍率与参数解析为 Markdown 表格

    Args:
        promote_dict: 升级数据字典，key 为等级字符串 "1" 到 "15"

    Returns:
        Markdown 格式的表格字符串
    """
    if not promote_dict or "1" not in promote_dict:
        return ""

    # 获取等级1的描述模板，提取列名（忽略空字符串）
    level_1_desc = promote_dict["1"].get("description", [])
    desc_templates = [d for d in level_1_desc if d and isinstance(d, str)]

    if not desc_templates:
        return ""

    # 提取属性名（分隔符前面的部分）
    attr_names = []
    for d in desc_templates:
        parts = d.split("|")
        attr_names.append(parts[0] if parts else "未知属性")

    table_lines = []

    # 1. 构建表头
    header = "| 等级 | " + " | ".join(attr_names) + " |"
    separator = "| :--- | " + " | ".join([":---"] * len(attr_names)) + " |"
    table_lines.extend([header, separator])

    # 2. 遍历所有等级 (1 到 15) 构建行
    for lvl in range(1, 16):
        lvl_str = str(lvl)
        if lvl_str not in promote_dict:
            continue

        level_data = promote_dict[lvl_str]
        params = level_data.get("params", [])
        descriptions = [d for d in level_data.get("description", []) if d and isinstance(d, str)]

        row_vals = []
        for d in descriptions:
            parts = d.split("|")
            val_template = parts[1] if len(parts) > 1 else ""

            # 正则替换：匹配 {paramX:Y}，如 {param1:F1P}
            def repl(match):
                try:
                    idx = int(match.group(1)) - 1
                    fmt = match.group(2)
                    if 0 <= idx < len(params):
                        return format_param_value(params[idx], fmt)
                except (ValueError, IndexError):
                    pass
                return match.group(0)

            filled_val = re.sub(r"\{param(\d+):([A-Za-z0-9_]+)\}", repl, val_template)
            row_vals.append(filled_val)

        table_lines.append(f"| Lv.{lvl} | " + " | ".join(row_vals) + " |")

    return "\n".join(table_lines)


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

        skill_section = f"## 【{skill_type.value}】{t_name}\n\n"

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


def char_register():
    # 收集所有角色数据，用于生成全局汇总
    all_characters_data: List[Dict] = []

    for i in CHAR_DATA_PATH.glob("*.json"):
        with open(i, "r", encoding="utf-8") as f:
            json_data: Dict = json.load(f)
            # 收集基础角色信息用于汇总
            all_characters_data.append(
                {
                    "name": json_data.get("name", "未知"),
                    "weaponType": json_data.get("weaponType", ""),
                    "element": json_data.get("element", ""),
                    "rarity": json_data.get("rarity", 4),
                }
            )
            # 注册角色详细知识块
            for kp in parse_character_json(json_data):
                ai_entity(kp)

    # 生成并注册全局汇总知识块
    if all_characters_data:
        summary_kp = build_global_summary_kp(all_characters_data)
        ai_entity(summary_kp)


char_register()

# ==================== 测试运行 ====================

if __name__ == "__main__":
    import os
    import sys

    # 获取当前目录下的第一个 JSON 文件进行测试
    json_files = [f for f in os.listdir(".") if f.endswith(".json")]

    if not json_files:
        print("当前目录下没有找到 JSON 文件！")
        sys.exit(1)

    # 选择最新文件或第一个文件
    test_file = sorted(json_files)[-1]
    print(f"正在测试文件：{test_file}")
    print("=" * 60)

    try:
        with open(test_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        knowledge_points = parse_character_json(raw_data)

        if not knowledge_points:
            print("解析失败：未生成任何知识块")
            sys.exit(1)

        print(f"[OK] 成功生成 {len(knowledge_points)} 个知识块：")
        print()

        for i, kp in enumerate(knowledge_points, 1):
            print(f"[{i}] {kp['title']} (ID: {kp['id']})")
            # 只显示前500字符的内容预览
            preview = kp["content"][:500].replace("\n", " ") + "..." if len(kp["content"]) > 500 else kp["content"]
            print(f"    预览: {preview}")
            print()

        # 打印第一个知识块的完整内容用于详细查看
        print("\n" + "=" * 60)
        print("【第一个知识块完整内容】")
        print("=" * 60)
        print(knowledge_points[0]["content"][:2000])  # 最多显示2000字符

    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"文件未找到: {test_file}")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
