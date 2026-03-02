"""
RAG注册主模块
负责整合角色和武器的RAG注册功能
"""

import json
from typing import Dict, List

from gsuid_core.logger import logger
from gsuid_core.ai_core.models import KnowledgePoint
from gsuid_core.ai_core.register import ai_entity

from .weapon_parser import parse_weapon_json, build_weapon_global_summary_kp
from ..map.GS_MAP_PATH import alias_data
from .character_parser import parse_character_json, build_global_summary_kp
from ..resource.RESOURCE_PATH import CHAR_DATA_PATH, WEAPON_DATA_PATH
from ...genshinuid_adv.get_adv import adv_lst


def add_aliases_to_tags(char_name: str, tags: List[str], aliases: Dict[str, List[str]]) -> List[str]:
    """为角色添加别名到标签中"""
    # 查找角色的所有别名
    for main_name, alias_list in aliases.items():
        if char_name == main_name and alias_list:
            tags.extend(alias_list)
            break
    return tags


def parse_char_adv_json(json_data: Dict, aliases: Dict[str, List[str]]) -> List[KnowledgePoint]:
    """解析角色攻略数据为RAG知识块"""
    knowledge_points: List[KnowledgePoint] = []

    # 遍历所有角色
    for char_name, char_data in json_data.items():
        # 构建全局Header
        global_header = f"【角色攻略】\n角色：{char_name}\n---\n"

        # 角色攻略内容
        adv_content = global_header + f"# {char_name} 角色攻略\n\n## 推荐武器\n"

        # 处理武器推荐
        weapon_data = char_data.get("weapon", {})
        for star_level, weapons in weapon_data.items():
            if weapons:  # 如果有推荐武器
                adv_content += f"### {star_level}星武器推荐：\n"
                for weapon in weapons:
                    adv_content += f"- {weapon}\n"
                adv_content += "\n"

        # 处理圣遗物推荐
        artifact_data = char_data.get("artifact", [])
        if artifact_data:
            adv_content += "## 推荐圣遗物\n"
            for i, artifact_set in enumerate(artifact_data):
                adv_content += f"### 配装方案 {i + 1}：\n"
                for artifact in artifact_set:
                    adv_content += f"- {artifact}\n"
                adv_content += "\n"

        # 处理备注信息
        remark_data = char_data.get("remark", [])
        if remark_data:
            adv_content += "## 角色信息\n"
            for remark in remark_data:
                adv_content += f"- {remark}\n"
            adv_content += "\n"

        # 构建标签，包含别名
        tags = ["角色", "攻略", "武器推荐", "圣遗物", char_name]
        tags = add_aliases_to_tags(char_name, tags, aliases)

        # 添加武器类型标签
        weapon_data = char_data.get("weapon", {})
        for star_level, weapons in weapon_data.items():
            if weapons:
                tags.append(f"{star_level}星武器")

        # 添加知识块
        knowledge_points.append(
            {
                "id": f"char_adv_{char_name}",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "character_adv",
                "title": f"{char_name}-角色攻略",
                "content": adv_content,
                "tags": tags,
                "_hash": "",
            }
        )

    return knowledge_points


def char_adv_register():
    """注册角色攻略数据"""
    aliases = alias_data

    try:
        # 注册角色攻略知识块
        for kp in parse_char_adv_json(adv_lst, aliases):
            ai_entity(kp)

        logger.info(f"角色攻略数据注册完成，共处理 {len(adv_lst)} 个角色")

    except FileNotFoundError:
        logger.info(f"警告：未找到角色攻略文件 {adv_lst}")
    except json.JSONDecodeError as e:
        logger.info(f"JSON解析错误：{e}")
    except Exception as e:
        logger.info(f"注册角色攻略数据时发生错误：{e}")


def char_register():
    """注册所有角色数据"""
    # 收集所有角色数据，用于生成全局汇总
    all_characters_data: List[Dict] = []
    aliases = alias_data

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
                # 添加别名到角色知识块标签
                char_name = json_data.get("name", "")
                kp["tags"] = add_aliases_to_tags(char_name, kp["tags"], aliases)
                ai_entity(kp)

    # 生成并注册全局汇总知识块
    if all_characters_data:
        summary_kp = build_global_summary_kp(all_characters_data)
        ai_entity(summary_kp)


def weapon_register():
    """注册所有武器数据"""
    # 收集所有武器数据，用于生成全局汇总
    all_weapons_data: List[Dict] = []

    for i in WEAPON_DATA_PATH.glob("*.json"):
        with open(i, "r", encoding="utf-8") as f:
            json_data: Dict = json.load(f)
            # 收集基础武器信息用于汇总
            all_weapons_data.append(
                {
                    "name": json_data.get("name", "未知武器"),
                    "weaponType": json_data.get("weaponType", ""),
                    "rank": json_data.get("rank", 3),
                }
            )
            # 注册武器详细知识块
            for kp in parse_weapon_json(json_data):
                ai_entity(kp)

    # 生成并注册武器全局汇总知识块
    if all_weapons_data:
        weapon_summary_kp = build_weapon_global_summary_kp(all_weapons_data)
        ai_entity(weapon_summary_kp)


def rag_register():
    """执行完整的RAG注册"""
    logger.info("开始注册角色RAG数据...")
    char_register()
    logger.info("角色RAG注册完成")

    logger.info("开始注册武器RAG数据...")
    weapon_register()
    logger.info("武器RAG注册完成")

    logger.info("开始注册角色攻略RAG数据...")
    char_adv_register()
    logger.info("角色攻略RAG注册完成")

    logger.info("所有RAG数据注册完成！")


rag_register()
