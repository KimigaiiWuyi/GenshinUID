"""
RAG模块数据模型
定义用于RAG系统的数据类
"""

from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass
from typing_extensions import NotRequired

from .constants import WEAPON_MAP, ELEMENT_MAP, WEAPON_TYPE_MAP, WeaponType


class GsKnowledgePoint(TypedDict):
    """插件知识块：Core KnowledgePoint 加上文档里的 type/category。"""

    id: str
    plugin: str
    title: str
    content: str
    tags: List[str]
    type: NotRequired[str]
    category: NotRequired[str]
    entity: NotRequired[str]
    source: NotRequired[str]
    _hash: NotRequired[str]


def make_kp(
    id: str,
    title: str,
    content: str,
    tags: List[str],
    *,
    plugin: str = "genshin",
    type: Optional[str] = None,
    category: Optional[str] = None,
    entity: Optional[str] = None,
    source: Optional[str] = None,
    _hash: Optional[str] = None,
) -> GsKnowledgePoint:
    point = GsKnowledgePoint(
        id=id,
        plugin=plugin,
        title=title,
        content=content,
        tags=tags,
    )
    if type is not None:
        point["type"] = type
    if category is not None:
        point["category"] = category
    if entity is not None:
        point["entity"] = entity
    if source is not None:
        point["source"] = source
    if _hash is not None:
        point["_hash"] = _hash
    return point


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


@dataclass
class WeaponInfo:
    """武器基础信息"""

    id: str
    name: str
    type: WeaponType
    type_raw: str
    rank: int  # 1-5星
    description: str = ""
    story: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeaponInfo":
        """从字典创建武器信息"""
        type_raw = data.get("weaponType", "")
        weapon_type = WEAPON_TYPE_MAP.get(type_raw, WeaponType.SWORD)

        return cls(
            id=str(data.get("id", "unknown")),
            name=data.get("name", "未知武器"),
            type=weapon_type,
            type_raw=type_raw,
            rank=data.get("rank", 3),
            description=data.get("description", ""),
            story=data.get("story", ""),
        )


@dataclass
class WeaponBaseStat:
    """武器基础属性"""

    level: int
    base_atk: float
    prop_type: str
    prop_value: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "等级": self.level,
            "基础攻击力": self.base_atk,
            "副属性": self.prop_type,
            "副属性值": self.prop_value,
        }


@dataclass
class WeaponAffix:
    """武器精炼效果"""

    name: str
    description: str
    level: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "精炼等级": f"R{self.level}",
            "名称": self.name,
            "效果": self.description,
        }


@dataclass
class SkillInfo:
    """技能信息"""

    name: str
    type: str
    description: str
    cooldown: Optional[float] = None
    cost: Optional[float] = None
    promote_table: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "名称": self.name,
            "类型": self.type,
            "描述": self.description,
        }
        if self.cooldown is not None:
            result["冷却时间"] = f"{self.cooldown}秒"
        if self.cost is not None:
            result["元素能量"] = str(self.cost)
        return result


@dataclass
class ConstellationInfo:
    """命之座信息"""

    level: int
    name: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "命座等级": f"第{self.level}命",
            "名称": self.name,
            "效果": self.description,
        }


@dataclass
class ArtifactInfo:
    """圣遗物套装信息"""

    id: str
    name: str
    route: str
    max_level: int
    icon: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArtifactInfo":
        """从字典创建圣遗物信息"""
        level_list = data.get("levelList", [4, 5])
        max_level = max(level_list) if level_list else 5

        return cls(
            id=str(data.get("id", "unknown")),
            name=data.get("name", "未知圣遗物"),
            route=data.get("route", ""),
            max_level=max_level,
            icon=data.get("icon", ""),
        )


@dataclass
class MonsterInfo:
    """怪物基础信息"""

    id: str
    name: str
    type: str
    title: str
    special_name: str
    description: str
    icon: str
    route: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonsterInfo":
        """从字典创建怪物信息"""
        return cls(
            id=str(data.get("id", "unknown")),
            name=data.get("name", "未知怪物"),
            type=data.get("type", "未知类型"),
            title=data.get("title", ""),
            special_name=data.get("specialName", ""),
            description=data.get("description", ""),
            icon=data.get("icon", ""),
            route=data.get("route", ""),
        )
