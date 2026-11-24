"""GenshinUID 离线材料计算器、知识库降级与 ai_return 容错测试。"""

from __future__ import annotations

import asyncio

import httpx2
import pytest
from pydantic_ai import RunContext
from pydantic_ai.usage import RunUsage
from pydantic_ai.models.test import TestModel

from gsuid_core.bot import Bot, _Bot
from gsuid_core.models import Event
from gsuid_core.ai_core.models import ToolContext
from GenshinUID.genshinuid_ai_func import kb, user, materials
from gsuid_core.ai_core.trigger_bridge import _AI_CALL_CONTEXT
from GenshinUID.genshinuid_enka.draw_char_card import _ai_return_enka_char
from GenshinUID.genshinuid_enka.mono.Character import Character


def _make_ctx() -> RunContext[ToolContext]:
    ev = Event(
        bot_id="test",
        bot_self_id="100000000",
        msg_id="m1",
        user_type="group",
        group_id="group_1",
        user_id="100000001",
    )
    tc = ToolContext(bot=Bot(_Bot("test"), ev), ev=ev)
    return RunContext(deps=tc, model=TestModel(), usage=RunUsage())


def test_cumulative_exp_matches_official_table() -> None:
    expected = {
        1: 0,
        20: 120_175,
        40: 698_500,
        50: 1_277_600,
        60: 2_131_725,
        70: 3_327_650,
        80: 4_939_525,
        85: 6_161_850,
        90: 8_362_650,
    }
    for lv, exp in expected.items():
        assert materials._cumulative_exp(lv) == exp
    assert materials._cumulative_exp(0) == 0
    assert materials._cumulative_exp(99) == 8_362_650


def test_calc_ascension_gaps_aggregates_and_deducts_bag(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_box = [
        user.CharBoxItem("10000002", "神里绫华", 5, "冰", "单手剑", 70, 0, 10, "雾切"),
        user.CharBoxItem("10000003", "琴", 5, "风", "单手剑", 85, 1, 10, "西风剑"),
        user.CharBoxItem("10000073", "纳西妲", 5, "草", "法器", 90, 2, 10, "千夜浮梦"),
    ]

    async def _fake_box(uid: str) -> tuple[str, list[user.CharBoxItem]]:
        assert uid == "100000001"
        return "mys_index", sample_box

    async def _fake_bag(uid: str, targets: list[tuple[user.CharBoxItem, int]]) -> dict[str, int]:
        assert uid == "100000001"
        assert len(targets) == 2
        # 绯樱绣球 (101202) 已有 50、大英雄的经验 (104003) 已有 100
        return {"101202": 50, "104003": 100}

    async def _fake_need_uid(ctx: RunContext[ToolContext], raw_uid: str) -> tuple[str, str]:
        _ = ctx
        return raw_uid or "100000001", ""

    monkeypatch.setattr(materials, "_need_uid", _fake_need_uid)
    monkeypatch.setattr(materials, "collect_user_char_box", _fake_box)
    monkeypatch.setattr(materials, "_try_fetch_bag_inventory", _fake_bag)

    out = asyncio.run(materials.calc_genshin_char_ascension_gaps(_make_ctx(), uid="100000001"))

    # 神里绫华 70→90: 8,362,650 - 3,327,650 = 5,035,000; 琴 85→90: 8,362,650 - 6,161,850 = 2,200,800
    assert "总经验 7,235,800" in out
    assert "已满 Lv90：1 名｜未满 Lv90：2 名" in out
    assert "神里绫华(Lv70)" in out
    # 70→90 需 5阶(45)+6阶(60)=105 个绯樱绣球，背包已有 50 → 净缺 55
    assert "**绯樱绣球**：需 105｜已有 50｜净缺 55" in out
    assert "鸣神岛" in out
    # 琴 Lv85 已过 80 突破边界，仅需经验书
    assert "| 琴 | Lv85 | 无(仅经验) | 无 | 无 |" in out


def test_get_material_sources_resolves_material_char_and_fuzzy() -> None:
    out = asyncio.run(materials.get_genshin_material_sources(_make_ctx(), "绯樱绣球、神里绫华、刀镡"))
    assert "**绯樱绣球**（区域特产）" in out
    assert "鸣神岛" in out
    assert "### 神里绫华（稻妻）养成材料与来源" in out
    assert "恒常机关之心" in out
    assert "刀镡" in out


def test_kb_offline_fallback_and_bug_propagation(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise_connect(**kwargs: object) -> list[object]:
        _ = kwargs
        raise httpx2.ConnectError("connection refused")

    monkeypatch.setattr(kb, "query_knowledge", _raise_connect)
    res = asyncio.run(kb.search_genshin_kb(_make_ctx(), "绯樱绣球", limit=4))
    assert "向量库离线" in res
    assert "绯樱绣球" in res

    async def _raise_bug(**kwargs: object) -> list[object]:
        _ = kwargs
        raise TypeError("unexpected bug")

    monkeypatch.setattr(kb, "query_knowledge", _raise_bug)
    with pytest.raises(TypeError, match="unexpected bug"):
        asyncio.run(kb.search_genshin_kb(_make_ctx(), "绯樱绣球", limit=4))


def test_format_index_player_tolerates_missing_cryoculus() -> None:
    payload: dict[str, object] = {
        "role": {"nickname": "测试用户A", "level": 60, "region": "cn_gf01"},
        "stats": {
            "active_day_number": 500,
            "achievement_number": 1200,
            "avatar_number": 80,
            "full_fetter_avatar_num": 60,
            "spiral_abyss": "12-3",
            "anemoculus_number": 66,
            "pyroculus_number": 100,
        },
        "homes": [{"name": "翠黛峰", "level": 10, "comfort_num": 20000}],
    }
    text = user._format_index_player("100000001", payload)
    assert "测试用户A" in text
    assert "风66 火100" in text
    assert "冰" not in text


def test_ai_return_enka_char_survives_partial_card() -> None:
    buf: dict[str, list[object]] = {"texts": [], "images": []}
    token = _AI_CALL_CONTEXT.set(buf)
    try:
        char = Character.__new__(Character)
        char.char_name = "神里绫华"
        char.char_level = 90
        char.char_element = "冰"
        char.char_talent = 0
        char.char_fetter = "10"
        char.card_prop = {
            "weaponInfo": {"weaponName": "雾切之回光"},
            "equipList": [
                {"aritifactPieceName": "损坏件"},
                {
                    "aritifactPieceName": "生之花",
                    "aritifactSetsName": "冰风迷途的勇士",
                    "aritifactLevel": 20,
                    "reliquaryMainstat": {"statName": "生命值", "statValue": 4780},
                    "reliquarySubstats": [{"statName": "暴击伤害", "statValue": 21.0}],
                },
            ],
        }
        char.fight_prop = {}
        char.artifacts_all_score = 0.0
        char.percent = "0.0"
        _ai_return_enka_char(char)
    finally:
        _AI_CALL_CONTEXT.reset(token)

    emitted = [str(x) for x in buf["texts"]]
    assert len(emitted) == 1
    assert "神里绫华 角色面板" in emitted[0]
    assert "雾切之回光" in emitted[0]
    assert "生之花 冰风迷途的勇士 +20" in emitted[0]
