"""
RAG模块常量定义
包含枚举、映射字典等常量数据
"""

from enum import Enum


class SkillType(Enum):
    """技能类型枚举"""

    NORMAL_ATTACK = "普通攻击(A)"
    ELEMENTAL_SKILL = "元素战技(E)"
    ELEMENTAL_BURST = "元素爆发(Q)"
    PASSIVE = "被动天赋"


class WeaponType(Enum):
    """武器类型枚举"""

    CLAYMORE = "双手剑"
    SWORD = "单手剑"
    POLE = "长柄武器"
    CATALYST = "法器"
    BOW = "弓箭"


# ==================== 元素映射 ====================
ELEMENT_MAP = {
    "Water": "水元素",
    "Fire": "火元素",
    "Wind": "风元素",
    "Electric": "雷元素",
    "Ice": "冰元素",
    "Rock": "岩元素",
    "Grass": "草元素",
}

# ==================== 武器映射 ====================
WEAPON_MAP = {
    "WEAPON_CLAYMORE": "双手剑",
    "WEAPON_SWORD": "单手剑",
    "WEAPON_SWORD_ONE_HAND": "单手剑",
    "WEAPON_POLE": "长柄武器",
    "WEAPON_CATALYST": "法器",
    "WEAPON_BOW": "弓箭",
}

# ==================== 武器类型反向映射 ====================
WEAPON_TYPE_MAP = {
    "WEAPON_CLAYMORE": WeaponType.CLAYMORE,
    "WEAPON_SWORD": WeaponType.SWORD,
    "WEAPON_SWORD_ONE_HAND": WeaponType.SWORD,
    "WEAPON_POLE": WeaponType.POLE,
    "WEAPON_CATALYST": WeaponType.CATALYST,
    "WEAPON_BOW": WeaponType.BOW,
}

# ==================== 战斗属性映射 ====================
FIGHT_PROP_MAP = {
    "FIGHT_PROP_BASE_HP": "基础生命值",
    "FIGHT_PROP_BASE_ATTACK": "基础攻击力",
    "FIGHT_PROP_BASE_DEFENSE": "基础防御力",
    "FIGHT_PROP_CRITICAL": "暴击率",
    "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率",
    "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
    "FIGHT_PROP_HEAL_BONUS": "治疗加成",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "物理伤害加成",
    "FIGHT_PROP_FIRE_ADD_HURT": "火元素伤害加成",
    "FIGHT_PROP_ELEC_ADD_HURT": "雷元素伤害加成",
    "FIGHT_PROP_WATER_ADD_HURT": "水元素伤害加成",
    "FIGHT_PROP_ICE_ADD_HURT": "冰元素伤害加成",
    "FIGHT_PROP_WIND_ADD_HURT": "风元素伤害加成",
    "FIGHT_PROP_ROCK_ADD_HURT": "岩元素伤害加成",
    "FIGHT_PROP_GRASS_ADD_HURT": "草元素伤害加成",
}

# 技能键名映射（用于快速识别技能类型）
SKILL_KEY_MAP = {"0": SkillType.NORMAL_ATTACK, "1": SkillType.ELEMENTAL_SKILL, "2": SkillType.ELEMENTAL_BURST}

# ==================== 武器突破属性映射 ====================
WEAPON_AFFIX_MAP = {
    "FIGHT_PROP_ATTACK_PERCENT": "攻击力",
    "FIGHT_PROP_DEFENSE_PERCENT": "防御力",
    "FIGHT_PROP_HP_PERCENT": "生命值",
    "FIGHT_PROP_CHARGE_EFFICIENCY": "元素充能效率",
    "FIGHT_PROP_ELEMENT_MASTERY": "元素精通",
    "FIGHT_PROP_PHYSICAL_ADD_HURT": "物理伤害加成",
    "FIGHT_PROP_CRITICAL": "暴击率",
    "FIGHT_PROP_CRITICAL_HURT": "暴击伤害",
}

# ==================== 武器星级对应基础属性 ====================
WEAPON_STAR_BASE_STATS = {
    1: {"基础攻击力": 23, "突破上限": 4},
    2: {"基础攻击力": 33, "突破上限": 4},
    3: {"基础攻击力": 38, "突破上限": 6},
    4: {"基础攻击力": 42, "突破上限": 6},
    5: {"基础攻击力": 46, "突破上限": 6},
}
