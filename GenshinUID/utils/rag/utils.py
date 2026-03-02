"""
RAG模块工具函数
提供通用的工具函数和文本处理功能
"""

import re
from typing import Any, Dict, Optional


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

        table_lines.append("| Lv.{lvl} | " + " | ".join(row_vals) + " |".format())

    return "\n".join(table_lines)


def determine_skill_type(talent_key: str, t_desc: str, promote_dict: Optional[Dict]) -> str:
    """
    通过解析文本、键名和成长数据，智能判断技能按键

    Args:
        talent_key: 天赋键名（如 "0", "1", "2" 等）
        t_desc: 技能描述
        promote_dict: 升级数据字典

    Returns:
        技能类型字符串
    """
    # 1. 首先根据键名快速判断
    if talent_key in ["0", "1", "2"]:
        skill_map = {"0": "普通攻击(A)", "1": "元素战技(E)", "2": "元素爆发(Q)"}
        return skill_map.get(talent_key, "被动天赋")

    # 2. 普攻 (A)：描述中通常直接包含 "普通攻击"
    if t_desc and "普通攻击" in t_desc:
        return "普通攻击(A)"

    # 3. 元素爆发 (Q)：大招的特征是升级数据里一定有一项叫 "元素能量"
    if promote_dict and isinstance(promote_dict, dict):
        level_1_data = promote_dict.get("1", {})
        desc_list = safe_get(level_1_data, "description", default=[])
        if any("元素能量" in d for d in desc_list if isinstance(d, str)):
            return "元素爆发(Q)"

    # 4. 元素战技 (E)：有成长数据，但不是普攻也不是大招，那就是 E 技能
    if promote_dict:
        return "元素战技(E)"

    return "被动天赋"
