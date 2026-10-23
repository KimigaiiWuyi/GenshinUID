from __future__ import annotations

import json
import asyncio
from pathlib import Path

import pytest

from GenshinUID.utils import ambr_to_minigg
from GenshinUID.utils.ambr_to_minigg import WEAPON_GROW_CURVE, convert_ambr_to_weapon


def _dump(directory: Path, weapon_id: str, raw: dict[str, object]) -> None:
    (directory / f"{weapon_id}.json").write_text(json.dumps(raw), encoding="utf-8")


def test_one_prop_weapon_has_no_substat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ambr_to_minigg, "WEAPON_DATA_PATH", tmp_path)
    _dump(
        tmp_path,
        "11101",
        {
            "name": "无锋剑",
            "type": "单手剑",
            "rank": 1,
            "affix": None,
            "upgrade": {
                "prop": [
                    {
                        "type": "GROW_CURVE_ATTACK_101",
                        "initValue": 23.245,
                        "propType": "FIGHT_PROP_BASE_ATTACK",
                    }
                ],
                "promote": [{"addProps": {"FIGHT_PROP_BASE_ATTACK": 46.7}}],
            },
        },
    )

    result = asyncio.run(convert_ambr_to_weapon(11101))

    assert result is not None
    assert result["mainStatText"] == "无副词条"
    assert result["specialized"] == 0.0
    assert result["effectName"] == "无特效"
    curve = WEAPON_GROW_CURVE["90"]["curveInfos"]["GROW_CURVE_ATTACK_101"]
    assert result["attack"] == curve * 23.245 + 46.7


def test_two_prop_weapon_keeps_substat(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ambr_to_minigg, "WEAPON_DATA_PATH", tmp_path)
    _dump(
        tmp_path,
        "11401",
        {
            "name": "西风剑",
            "type": "单手剑",
            "rank": 4,
            "affix": {"11401": {"name": "顺风而行", "upgrade": {"0": "施放元素战技时回复能量。"}}},
            "upgrade": {
                "prop": [
                    {
                        "propType": "FIGHT_PROP_BASE_ATTACK",
                        "initValue": 41.0671,
                        "type": "GROW_CURVE_ATTACK_204",
                    },
                    {
                        "propType": "FIGHT_PROP_CHARGE_EFFICIENCY",
                        "initValue": 0.133333,
                        "type": "GROW_CURVE_CRITICAL_201",
                    },
                ],
                "promote": [{"addProps": {"FIGHT_PROP_BASE_ATTACK": 155.6}}],
            },
        },
    )

    result = asyncio.run(convert_ambr_to_weapon(11401))

    assert result is not None
    assert result["mainStatText"] == "元素充能效率"
    atk_curve = WEAPON_GROW_CURVE["90"]["curveInfos"]["GROW_CURVE_ATTACK_204"]
    sp_curve = WEAPON_GROW_CURVE["90"]["curveInfos"]["GROW_CURVE_CRITICAL_201"]
    assert result["attack"] == atk_curve * 41.0671 + 155.6
    assert result["specialized"] == sp_curve * 0.133333
