"""
怪物数据解析器
负责将怪物JSON数据解析为RAG知识块
"""

from typing import Dict, List

from gsuid_core.ai_core.models import KnowledgePoint

from .utils import clean_html_tags
from .models import MonsterInfo

# 怪物类型映射
MONSTER_TYPE_MAP = {
    "MONSTER_ORDINARY": "普通敌人",
    "MONSTER_BOSS": "首领敌人",
    "MONSTER_ENV_ANIMAL": "环境动物",
}


def parse_monster_json(json_data: Dict) -> List[KnowledgePoint]:
    """
    解析怪物JSON数据为RAG知识块

    Args:
        json_data: 怪物原始JSON数据

    Returns:
        知识块列表
    """
    if not json_data or not isinstance(json_data, dict):
        return []

    # 解析怪物基础信息
    monster_info = MonsterInfo.from_dict(json_data)

    # 构建全局Header
    global_header = f"【怪物情报】\n怪物：{monster_info.name} | ID：{monster_info.id}\n类型：{monster_info.type}\n---\n"

    knowledge_points: List[KnowledgePoint] = []

    # ==================== 块 1：怪物基础信息 ====================
    monster_content = (
        global_header + f"# {monster_info.name} 基础信息\n\n"
        f"## 基本信息\n"
        f"- **怪物名称**：{monster_info.name}\n"
        f"- **怪物ID**：{monster_info.id}\n"
        f"- **怪物类型**：{monster_info.type}\n"
        f"- **称号/头衔**：{monster_info.title or '无'}\n"
        f"- **特殊名称**：{monster_info.special_name or '无'}\n"
    )

    # 添加描述
    if monster_info.description:
        cleaned_desc = clean_html_tags(monster_info.description)
        monster_content += f"\n## 描述\n{cleaned_desc}\n"

    knowledge_points.append(
        {
            "id": f"monster_{monster_info.id}_info",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "monster_info",
            "title": f"{monster_info.name}-基础信息",
            "content": monster_content,
            "tags": ["怪物", monster_info.type, monster_info.name],
            "_hash": "",
        }
    )

    # ==================== 块 2：怪物属性与抗性 ====================
    entries = json_data.get("entries", {})
    if entries:
        for entry_id, entry_data in entries.items():
            if not isinstance(entry_data, dict):
                continue

            entry_type = entry_data.get("type", "")
            entry_type_name = MONSTER_TYPE_MAP.get(entry_type, entry_type)

            attr_content = (
                global_header + f"# {monster_info.name} 属性与抗性\n\n## 基本属性\n- **敌人类型**：{entry_type_name}\n"
            )

            # 添加属性
            props = entry_data.get("prop", [])
            if props:
                attr_content += "\n## 基础属性\n"
                for prop in props:
                    prop_type = prop.get("propType", "")
                    init_value = prop.get("initValue", 0)
                    # 简化显示
                    prop_name = prop_type.replace("FIGHT_PROP_BASE_", "").replace("FIGHT_PROP_", "")
                    attr_content += f"- **{prop_name}**：{init_value}\n"

            # 添加抗性
            resistance = entry_data.get("resistance", {})
            if resistance:
                attr_content += "\n## 元素抗性\n"
                resist_map = {
                    "fireSubHurt": "火元素抗性",
                    "grassSubHurt": "草元素抗性",
                    "waterSubHurt": "水元素抗性",
                    "elecSubHurt": "雷元素抗性",
                    "windSubHurt": "风元素抗性",
                    "iceSubHurt": "冰元素抗性",
                    "rockSubHurt": "岩元素抗性",
                    "physicalSubHurt": "物理抗性",
                }
                for key, value in resistance.items():
                    resist_name = resist_map.get(key, key)
                    # 转换为百分比
                    resist_pct = value * 100
                    attr_content += f"- **{resist_name}**：{resist_pct:.0f}%\n"

            # 添加掉落物品
            reward = entry_data.get("reward", {})
            if reward:
                attr_content += "\n## 掉落物品\n"
                for item_id, item_data in reward.items():
                    if isinstance(item_data, dict):
                        item_name = item_data.get("name", "")
                        item_rank = item_data.get("rank", 0)
                        count = item_data.get("count", "")
                        if item_name:
                            if count:
                                attr_content += f"- **{item_name}**（{item_rank}星）：掉落概率 {count}\n"
                            else:
                                attr_content += f"- **{item_name}**（{item_rank}星）\n"

            knowledge_points.append(
                {
                    "id": f"monster_{monster_info.id}_attr_{entry_id}",
                    "plugin": "genshin",
                    "type": "knowledge",
                    "category": "monster_attr",
                    "title": f"{monster_info.name}-属性与抗性",
                    "content": attr_content,
                    "tags": ["怪物", "属性", "抗性", monster_info.name],
                    "_hash": "",
                }
            )

    return knowledge_points


def build_monster_global_summary_kp(all_monsters_data: List[Dict]) -> KnowledgePoint:
    """生成怪物全局汇总知识块，用于回答统计类问题

    例如："史莱姆有多少种？"、"所有精英敌人有哪些？"
    """
    # 按类型分类
    type_dict: Dict[str, List[str]] = {}

    for monster in all_monsters_data:
        name = monster.get("name", "未知")
        monster_type = monster.get("type", "未知类型")

        if monster_type not in type_dict:
            type_dict[monster_type] = []
        type_dict[monster_type].append(name)

    # 构建内容
    content = "# 怪物全局汇总\n\n## 怪物分类统计\n\n"

    for monster_type, names in sorted(type_dict.items()):
        if names:
            content += f"### {monster_type}（{len(names)}种）\n"
            # 只显示前20个，避免内容过长
            display_names = sorted(names)[:20]
            for name in display_names:
                content += f"- {name}\n"
            if len(names) > 20:
                content += f"- ... 等共{len(names)}种\n"
            content += "\n"

    return {
        "id": "monster_global_summary",
        "plugin": "genshin",
        "type": "knowledge",
        "category": "monster_summary",
        "title": "怪物全局汇总",
        "content": content,
        "tags": ["怪物", "汇总", "统计"],
        "_hash": "",
    }
