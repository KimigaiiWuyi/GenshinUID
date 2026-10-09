from __future__ import annotations

import sys
import types
from pathlib import Path

_RAG = Path(__file__).resolve().parents[1] / "GenshinUID" / "utils" / "rag"
_RAG_PKG = "GenshinUID.utils.rag"
# 先占住包，避免 rag/__init__.py 在导入解析器时把整库注册跑起来。
_stubbed = _RAG_PKG not in sys.modules
if _stubbed:
    _pkg = types.ModuleType(_RAG_PKG)
    _pkg.__path__ = [str(_RAG)]
    _pkg.__package__ = _RAG_PKG
    sys.modules[_RAG_PKG] = _pkg

from GenshinUID.utils.rag.models import GsKnowledgePoint  # noqa: E402
from GenshinUID.utils.rag.character_parser import parse_character_json  # noqa: E402

if _stubbed:
    del sys.modules[_RAG_PKG]


def _char(constellation: dict[str, object], talent: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "id": 10000109,
        "name": "梦见月瑞希",
        "element": "Wind",
        "weaponType": "WEAPON_CATALYST",
        "rank": 5,
        "region": "INAZUMA",
        "constellation": constellation,
        "talent": talent or {},
    }


def _content(points: list[GsKnowledgePoint], category: str) -> str:
    for point in points:
        if "category" in point and point["category"] == category:
            content = point["content"]
            assert isinstance(content, str)
            return content
    raise AssertionError(category)


def test_constellation_appends_quest_suffix() -> None:
    base = "进入梦浮状态时，每点元素精通提供0.04%伤害加成。"
    points = parse_character_json(
        _char(
            {
                "1": {
                    "name": "缠忆君影梦相见",
                    "description": base,
                    "descriptionBuff": base + "\n此外，附近敌人的火水冰雷风抗性降低20%。",
                }
            }
        )
    )
    const = _content(points, "constellation")
    assert "缠忆君影梦相见" in const
    assert base in const
    assert "抗性降低20%" in const
    assert "完成对应任务或辉映变化后追加" in const


def test_rewritten_buff_keeps_full_text() -> None:
    points = parse_character_json(
        _char(
            {
                "0": {
                    "name": "宿雾若水遥",
                    "description": "扩散伤害提升。",
                    "descriptionBuff": "星扩散伤害提升，并额外造成一次攻击。",
                }
            }
        )
    )
    const = _content(points, "constellation")
    assert "完成对应任务或辉映变化后的完整效果" in const
    assert "额外造成一次攻击" in const


def test_same_buff_is_omitted() -> None:
    text = "只有基础效果。"
    points = parse_character_json(_char({"0": {"name": "测试", "description": text, "descriptionBuff": text}}))
    const = _content(points, "constellation")
    assert "变化后" not in const
    assert text in const


def test_talent_buff_is_included() -> None:
    base = "召唤寒病鬼差。"
    points = parse_character_json(
        _char(
            {},
            {
                "1": {
                    "name": "仙法·寒病鬼差",
                    "description": base,
                    "descriptionBuff": base + "\n辉映·星烁：攻击力提升50%。",
                }
            },
        )
    )
    skill = _content(points, "skill")
    assert "仙法·寒病鬼差" in skill
    assert "辉映·星烁" in skill
