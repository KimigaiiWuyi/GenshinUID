"""
RAG注册主模块
负责整合角色、武器、圣遗物和怪物的RAG注册功能
"""

import json
from typing import Dict, List

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.ai_core.models import KnowledgePoint
from gsuid_core.ai_core.register import ai_alias, ai_entity

from .weapon_parser import parse_weapon_json, build_weapon_global_summary_kp
from .monster_parser import parse_monster_json, build_monster_global_summary_kp
from .artifact_parser import parse_artifact_json, build_artifact_global_summary_kp
from ..map.GS_MAP_PATH import alias_data
from .character_parser import parse_character_json, build_global_summary_kp
from ..resource.RESOURCE_PATH import REL_DATA_PATH, CHAR_DATA_PATH, WEAPON_DATA_PATH, MONSTER_DATA_PATH
from ...genshinuid_adv.get_adv import adv_lst


def register_aliases():
    """注册角色别名"""
    for main_name, alias_list in alias_data.items():
        ai_alias(main_name, alias_list)


def add_aliases_to_tags(char_name: str, tags: List[str], aliases: Dict[str, List[str]]) -> List[str]:
    """为角色添加别名到标签中"""
    # 查找角色的所有别名
    for main_name, alias_list in aliases.items():
        if char_name == main_name and alias_list:
            tags.extend(alias_list)
            break
    return tags


def parse_char_adv_json(json_data: Dict, aliases: Dict[str, List[str]]) -> List[KnowledgePoint]:
    """解析角色攻略数据为RAG知识块

    同时构建圣遗物反向索引：圣遗物 -> 适合该圣遗物的角色列表
    """
    knowledge_points: List[KnowledgePoint] = []

    # 圣遗物反向索引：圣遗物名称 -> 适合该圣遗物的角色列表
    artifact_to_chars: Dict[str, List[str]] = {}

    # 遍历所有角色
    for char_name, char_data in json_data.items():
        # 收集该角色推荐的圣遗物（用于构建反向索引）
        artifact_data = char_data.get("artifact", [])
        for artifact_set in artifact_data:
            for artifact_name in artifact_set:
                if artifact_name not in artifact_to_chars:
                    artifact_to_chars[artifact_name] = []
                if char_name not in artifact_to_chars[artifact_name]:
                    artifact_to_chars[artifact_name].append(char_name)

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
        if artifact_data:
            adv_content += "## 推荐圣遗物 (角色适合圣遗物)\n"
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
        tags = ["角色", "攻略", "武器推荐", "圣遗物推荐", "圣遗物", char_name]
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

    # 生成圣遗物反向索引知识块
    for artifact_name, char_list in artifact_to_chars.items():
        # 去重并排序
        unique_chars = sorted(list(set(char_list)))

        reverse_content = f"# 【圣遗物反向索引】{artifact_name}\n\n## 适合使用 {artifact_name} 的角色\n\n"

        for char in unique_chars:
            reverse_content += f"- {char}\n"

        reverse_content += f"\n## 统计信息\n- 共有 {len(unique_chars)} 个角色适合使用此圣遗物\n"

        knowledge_points.append(
            {
                "id": f"artifact_reverse_{artifact_name}",
                "plugin": "genshin",
                "type": "knowledge",
                "category": "artifact_reverse_index",
                "title": f"{artifact_name}-适合角色",
                "content": reverse_content,
                "tags": ["圣遗物", "反向索引", "角色推荐", artifact_name],
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

        logger.info(t("log.genshinuid.p0_9c5177", p0=len(adv_lst)))

    except FileNotFoundError:
        logger.info(t("log.genshinuid.adv_lst_1c832d", adv_lst=adv_lst))
    except json.JSONDecodeError as e:
        logger.info(t("log.genshinuid.json_d2e26b", e=e))
    except Exception as e:
        logger.info(t("log.genshinuid.msg_b3f284", e=e))


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


def artifact_register():
    """注册所有圣遗物数据"""
    # 收集所有圣遗物数据，用于生成全局汇总
    all_artifacts_data: List[Dict] = []

    for i in REL_DATA_PATH.glob("*.json"):
        try:
            with open(i, "r", encoding="utf-8") as f:
                json_data: Dict = json.load(f)
                # 收集基础圣遗物信息用于汇总
                level_list = json_data.get("levelList", [4, 5])
                max_level = max(level_list) if level_list else 5
                all_artifacts_data.append(
                    {
                        "name": json_data.get("name", "未知圣遗物"),
                        "maxLevel": max_level,
                        "id": json_data.get("id", 0),
                    }
                )
                # 注册圣遗物详细知识块
                for kp in parse_artifact_json(json_data):
                    ai_entity(kp)
        except Exception as e:
            logger.warning(t("log.genshinuid.msg_fb7105", i=i, e=e))
            continue

    # 生成并注册圣遗物全局汇总知识块
    if all_artifacts_data:
        artifact_summary_kp = build_artifact_global_summary_kp(all_artifacts_data)
        ai_entity(artifact_summary_kp)

    logger.info(t("log.genshinuid.rag_p0_5ac7eb", p0=len(all_artifacts_data)))


def monster_register():
    """注册所有怪物数据"""
    # 收集所有怪物数据，用于生成全局汇总
    all_monsters_data: List[Dict] = []

    for i in MONSTER_DATA_PATH.glob("*.json"):
        try:
            with open(i, "r", encoding="utf-8") as f:
                json_data: Dict = json.load(f)
                # 收集基础怪物信息用于汇总
                all_monsters_data.append(
                    {
                        "name": json_data.get("name", "未知怪物"),
                        "type": json_data.get("type", "未知类型"),
                        "id": json_data.get("id", 0),
                    }
                )
                # 注册怪物详细知识块
                for kp in parse_monster_json(json_data):
                    ai_entity(kp)
        except Exception as e:
            logger.warning(t("log.genshinuid.msg_1d0015", i=i, e=e))
            continue

    # 生成并注册怪物全局汇总知识块
    if all_monsters_data:
        monster_summary_kp = build_monster_global_summary_kp(all_monsters_data)
        ai_entity(monster_summary_kp)

    logger.info(t("log.genshinuid.rag_p0_2cc983", p0=len(all_monsters_data)))


def rag_register():
    """执行完整的RAG注册"""
    logger.info(t("log.genshinuid.rag_53fb81"))
    char_register()
    logger.info(t("log.genshinuid.rag_2078ba"))

    logger.info(t("log.genshinuid.rag_faa0a1"))
    weapon_register()
    logger.info(t("log.genshinuid.rag_ddb0f4"))

    logger.info(t("log.genshinuid.rag_6c1c50"))
    artifact_register()
    logger.info(t("log.genshinuid.rag_987c4d"))

    logger.info(t("log.genshinuid.rag_ecfccd"))
    monster_register()
    logger.info(t("log.genshinuid.rag_3b7050"))

    logger.info(t("log.genshinuid.rag_46d8d0"))
    char_adv_register()
    logger.info(t("log.genshinuid.rag_e19e48"))

    register_aliases()

    logger.info(t("log.genshinuid.rag_f3d2e9"))


rag_register()
