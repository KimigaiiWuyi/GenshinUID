"""原神伤害公式与两个代理的关键词归属。"""

import importlib.util
from pathlib import Path

from gsuid_core.ai_core.agent_node.registry import match_capability_node, unregister_agent_node

_ROOT = Path(__file__).resolve().parents[1] / "GenshinUID/genshinuid_ai_func"


def _load(module_name: str, filename: str):
    path = _ROOT / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_talent_hit_and_vaporize() -> None:
    damage = _load("genshin_damage_formula", "damage.py")
    plain = damage.calc_hit(
        scaling_stat=1000,
        motion_value=1,
        dmg_bonus=0,
        crit_rate=0,
        crit_dmg=0,
        char_level=90,
        enemy_level=90,
        def_reduction=0,
        enemy_resistance=0,
        em=0,
        reaction="none",
        reaction_bonus=0,
        custom_reaction_multiplier=0,
        hit_count=1,
    )
    assert plain.expected == 500
    vape = damage.calc_hit(
        scaling_stat=1000,
        motion_value=1,
        dmg_bonus=0,
        crit_rate=0,
        crit_dmg=0,
        char_level=90,
        enemy_level=90,
        def_reduction=0,
        enemy_resistance=0,
        em=0,
        reaction="vaporize_pyro",
        reaction_bonus=0,
        custom_reaction_multiplier=0,
        hit_count=1,
    )
    assert vape.expected == 750


def test_custom_reaction_requires_a_coefficient() -> None:
    damage = _load("genshin_damage_formula_custom", "damage.py")
    missing = damage.calc_hit(
        scaling_stat=1000,
        motion_value=1,
        dmg_bonus=0,
        crit_rate=0,
        crit_dmg=0,
        char_level=90,
        enemy_level=90,
        def_reduction=0,
        enemy_resistance=0,
        em=0,
        reaction="custom",
        reaction_bonus=0,
        custom_reaction_multiplier=0,
        hit_count=1,
    )
    assert isinstance(missing, str)
    lunar = damage.calc_hit(
        scaling_stat=1000,
        motion_value=1,
        dmg_bonus=0,
        crit_rate=0,
        crit_dmg=0,
        char_level=90,
        enemy_level=90,
        def_reduction=0,
        enemy_resistance=0,
        em=0,
        reaction="custom",
        reaction_bonus=0,
        custom_reaction_multiplier=1.2,
        hit_count=1,
    )
    assert lunar.expected == 600


def test_abyss_and_damage_keywords_do_not_steal_each_other() -> None:
    _load("genshin_agent_profiles", "agents.py")
    try:
        assert match_capability_node("深渊怎么打") == "genshin_abyss_agent"
        assert match_capability_node("深渊使用率") == "genshin_abyss_agent"
        assert match_capability_node("危战概览") == "genshin_abyss_agent"
        assert match_capability_node("0+1的沃雅妮莎对丝柯克队伍提升有多少") == "genshin_damage_agent"
        assert match_capability_node("完全无关的闲聊你好呀") == ""
    finally:
        unregister_agent_node("genshin_abyss_agent")
        unregister_agent_node("genshin_damage_agent")
