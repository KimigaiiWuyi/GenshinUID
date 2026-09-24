"""Lunaris 深渊期选择与楼层解析。不访问网络。"""

import datetime
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "GenshinUID/genshinuid_guide/lunaris_tower.py"
_spec = importlib.util.spec_from_file_location("lunaris_tower_under_test", _PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_pick_open_window_else_latest() -> None:
    listing = {
        "20096": {
            "openTime": "2026-08-08 04:00:00",
            "closeTime": "2026-08-25 03:59:59",
            "chsBuffName": "辉卷之月",
        },
        "20097": {
            "openTime": "2026-08-25 04:00:00",
            "closeTime": "2026-09-16 03:59:59",
            "chsBuffName": "骇星之月",
        },
    }
    inside = datetime.datetime(2026, 8, 20, 12, 0, 0)
    after = datetime.datetime(2026, 9, 24, 12, 0, 0)
    assert _mod.pick_schedule_id(listing, inside) == "20096"
    assert _mod.pick_schedule_id(listing, after) == "20097"


def test_parse_floor_strips_markup_and_counts() -> None:
    payload = {
        "buffName": "骇星之月",
        "monthlyBuff": {"description": "造成<color=#F39000>星扩散</color>伤害。"},
        "floors": [
            {
                "floorIndex": 12,
                "firstHalfBuff": {"description": "上半增伤"},
                "secondHalfBuff": None,
                "chambers": [
                    {
                        "monsterLevel": 100,
                        "firstHalfMonsters": [
                            {"name": "矮灵雕刻师", "icon": "UI_A", "hp": 1165335},
                            {"name": "矮灵雕刻师", "icon": "UI_A", "hp": 1165335},
                        ],
                        "secondHalfMonsters": [{"name": "执灯人", "icon": "UI_B"}],
                    }
                ],
            }
        ],
    }
    schedule = {
        "openTime": "2026-08-25 04:00:00",
        "closeTime": "2026-09-16 03:59:59",
        "chsBuffName": "骇星之月",
    }
    viewed = _mod.parse_tower_floor(payload, 12, "20097", schedule)
    assert not isinstance(viewed, str)
    assert viewed["buff_desc"] == "造成星扩散伤害。"
    assert viewed["chambers"][0]["upper"][0]["count"] == 2
    assert viewed["chambers"][0]["upper"][0]["hp"] == 1165335
    assert viewed["chambers"][0]["lower"][0]["name"] == "执灯人"
    missing = _mod.parse_tower_floor(payload, 9, "20097", schedule)
    assert missing == "Lunaris 本期没有第 9 层。"


def test_align_dates_to_sixteenth_after_ruijin() -> None:
    listing = {
        "95": {
            "openTime": "2024-06-01 04:00:00",
            "closeTime": "2024-06-16 03:59:59",
            "chsBuffName": "得策之月",
        },
        "96": {
            "openTime": "2024-06-16 04:00:00",
            "closeTime": "2024-07-16 03:59:59",
            "chsBuffName": "锐进之月",
        },
        "121": {
            "openTime": "2026-07-16 04:00:00",
            "closeTime": "2026-08-06 03:59:59",
            "chsBuffName": "冰迸之月",
        },
        "122": {
            "openTime": "2026-08-06 04:00:00",
            "closeTime": "2026-08-07 03:59:59",
            "chsBuffName": "攻辉之月",
        },
        "20096": {
            "openTime": "2026-08-08 04:00:00",
            "closeTime": "2026-08-25 03:59:59",
            "chsBuffName": "辉卷之月",
        },
        "20097": {
            "openTime": "2026-08-25 04:00:00",
            "closeTime": "2026-09-16 03:59:59",
            "chsBuffName": "骇星之月",
        },
    }
    aligned = _mod._align_sixteenth(listing)
    assert aligned["95"]["openTime"].startswith("2024-06-01")
    assert aligned["96"]["openTime"].startswith("2024-06-16")
    assert "122" not in aligned
    assert aligned["121"]["closeTime"].startswith("2026-08-16")
    assert aligned["20096"]["openTime"].startswith("2026-08-16")
    assert aligned["20096"]["closeTime"].startswith("2026-09-16")
    assert aligned["20097"]["openTime"].startswith("2026-09-16")
    assert aligned["20097"]["closeTime"].startswith("2026-10-16")
