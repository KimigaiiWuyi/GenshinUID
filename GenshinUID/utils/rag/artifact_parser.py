"""
圣遗物数据解析器
负责将圣遗物JSON数据解析为RAG知识块
"""

from typing import Dict, List

from gsuid_core.ai_core.models import KnowledgePoint

from .utils import clean_html_tags
from .models import ArtifactInfo

# 圣遗物部位映射
ARTIFACT_POS_MAP = {
    "EQUIP_BRACER": "生之花",
    "EQUIP_NECKLACE": "死之羽",
    "EQUIP_SHOES": "时之沙",
    "EQUIP_RING": "空之杯",
    "EQUIP_DRESS": "理之冠",
}


def parse_artifact_json(json_data: Dict) -> List[KnowledgePoint]:
    """
    解析圣遗物JSON数据为RAG知识块

    Args:
        json_data: 圣遗物原始JSON数据

    Returns:
        知识块列表
    """
    if not json_data or not isinstance(json_data, dict):
        return []

    # 解析圣遗物基础信息
    artifact_info = ArtifactInfo.from_dict(json_data)

    # 构建全局Header
    global_header = (
        f"【圣遗物情报】\n套装：{artifact_info.name} | ID：{artifact_info.id}\n星级：{artifact_info.max_level}星\n---\n"
    )

    knowledge_points: List[KnowledgePoint] = []

    # ==================== 块 1：圣遗物基础信息 ====================
    artifact_content = (
        global_header + f"# {artifact_info.name} 基础信息\n\n"
        f"## 基本信息\n"
        f"- **套装名称**：{artifact_info.name}\n"
        f"- **套装ID**：{artifact_info.id}\n"
        f"- **英文名称**：{artifact_info.route}\n"
        f"- **最高星级**：{artifact_info.max_level}星\n"
    )

    # 添加套装效果
    affix_list = json_data.get("affixList", {})
    if affix_list:
        artifact_content += "\n## 套装效果\n"
        for affix_id, affix_desc in affix_list.items():
            # 提取件套数
            piece_count = "2"
            if "3" in affix_id or affix_desc.startswith("3"):
                piece_count = "3"
            elif "4" in affix_id or affix_desc.startswith("4"):
                piece_count = "4"
            clean_desc = clean_html_tags(affix_desc)
            artifact_content += f"- **{piece_count}件套**：{clean_desc}\n"

    # 添加获取来源
    source = json_data.get("source", [])
    if source:
        artifact_content += "\n## 获取方式\n"
        for src in source:
            if isinstance(src, dict):
                src_name = src.get("name", "")
                if src_name:
                    artifact_content += f"- {src_name}\n"

    knowledge_points.append(
        {
            "id": f"artifact_{artifact_info.id}_info",
            "plugin": "genshin",
            "type": "knowledge",
            "category": "artifact_info",
            "title": f"{artifact_info.name}-基础信息",
            "content": artifact_content,
            "tags": ["圣遗物", "套装", artifact_info.name],
            "_hash": "",
        }
    )

    # ==================== 块 2：圣遗物各部位详情 ====================
    suit_data = json_data.get("suit", {})
    if suit_data:
        suit_content = global_header + f"# {artifact_info.name} 各部位详情\n\n"

        for pos_key, pos_info in suit_data.items():
            if not isinstance(pos_info, dict):
                continue

            pos_name = ARTIFACT_POS_MAP.get(pos_key, pos_key)
            item_name = pos_info.get("name", "未知")
            description = clean_html_tags(pos_info.get("description", ""))
            max_level = pos_info.get("maxLevel", 0)

            suit_content += f"## 【{pos_name}】{item_name}\n\n"
            suit_content += f"{description}\n\n"
            suit_content += f"- **最高等级**：{max_level}级\n\n"

        knowledge_points.append(
            {
                "id": f"artifact_{artifact_info.id}_suit",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "artifact_suit",
                "title": f"{artifact_info.name}-部位详情",
                "content": suit_content,
                "tags": ["圣遗物", "部位", artifact_info.name],
                "_hash": "",
            }
        )

    return knowledge_points


def build_artifact_global_summary_kp(all_artifacts_data: List[Dict]) -> KnowledgePoint:
    """生成圣遗物全局汇总知识块，用于回答统计类问题

    例如："有哪些5星圣遗物套装？"、"哪些圣遗物适合主C？"
    """
    # 按星级分类
    star_dict: Dict[str, List[str]] = {"5星": [], "4星": [], "3星": [], "2星": [], "1星": []}

    for artifact in all_artifacts_data:
        name = artifact.get("name", "未知")
        max_level = artifact.get("maxLevel", 0) or artifact.get("levelList", [0])[-1]

        star_key = f"{max_level}星"
        if star_key in star_dict:
            star_dict[star_key].append(name)

    # 构建内容
    content = "# 圣遗物全局汇总\n\n## 圣遗物套装统计\n\n"

    for star, names in star_dict.items():
        if names:
            content += f"### {star}圣遗物套装（{len(names)}套）\n"
            for name in sorted(names):
                content += f"- {name}\n"
            content += "\n"

    return {
        "id": "artifact_global_summary",
        "plugin": "genshin",
        "type": "knowledge",
        "category": "artifact_summary",
        "title": "圣遗物全局汇总",
        "content": content,
        "tags": ["圣遗物", "汇总", "统计"],
        "_hash": "",
    }
