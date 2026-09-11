from __future__ import annotations

import sys
import types
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_CV = _ROOT / "GenshinUID" / "utils" / "api" / "cv"

_MODELS_SPEC = spec_from_file_location("akasha_cv_models", _CV / "models.py")
assert _MODELS_SPEC is not None and _MODELS_SPEC.loader is not None
_MODELS = module_from_spec(_MODELS_SPEC)
sys.modules["akasha_cv_models"] = _MODELS
_MODELS_SPEC.loader.exec_module(_MODELS)

_pkg = types.ModuleType("akasha_cv")
_pkg.models = _MODELS
sys.modules["akasha_cv"] = _pkg
sys.modules["akasha_cv.models"] = _MODELS

_SP_SPEC = spec_from_file_location(
    "akasha_cv.substat_priority",
    _CV / "substat_priority.py",
    submodule_search_locations=[str(_CV)],
)
assert _SP_SPEC is not None and _SP_SPEC.loader is not None
_SP = module_from_spec(_SP_SPEC)
sys.modules["akasha_cv.substat_priority"] = _SP
_SP_SPEC.loader.exec_module(_SP)

pct_gain_over_base = _SP.pct_gain_over_base
dmg_gain_over_base = _SP.dmg_gain_over_base
should_show_substat = _SP.should_show_substat
parse_substat_priority_payload = _SP.parse_substat_priority_payload
compute_substat_priority_board = _SP.compute_substat_priority_board
compute_substat_priority_boards = _SP.compute_substat_priority_boards
find_substat_priority_board = _SP.find_substat_priority_board

_WEAPON = {
    "name": "Favonius Codex",
    "icon": "UI_EquipIcon_Catalyst_Zephyrus_Awaken",
    "substat": "Energy Recharge",
    "type": "Catalyst",
    "rarity": 4,
    "weaponId": "14401",
    "refinement": 5,
}

_BASE = 538126.9176401335
_OUT = 610005
_OLD = 19952

_ITEM = {
    "calculation": {
        "calculationId": "1000012514170er",
        "name": "Lunar-Crystallize Team, Avg DMG",
        "short": "LUNAR",
        "weapon": _WEAPON,
        "variant": "170% ER",
        "hidden": False,
    },
    "substats": {
        "Base": {
            "result": _BASE,
            "substatValue": 0,
            "newRank": _OLD,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "Flat HP": {
            "result": 541844.7,
            "substatValue": 298.75,
            "newRank": 17100,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "HP%": {
            "result": 548788.2,
            "substatValue": 5.83,
            "newRank": 12607,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "ATK%": {
            "result": _BASE,
            "substatValue": 5.83,
            "newRank": _OLD,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "Crit RATE": {
            "result": 540232.3,
            "substatValue": 3.89,
            "newRank": 18319,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "Crit DMG": {
            "result": 554445.8,
            "substatValue": 7.77,
            "newRank": 9655,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
        "Elemental Mastery": {
            "result": 545245.9,
            "substatValue": 23.31,
            "newRank": 14771,
            "oldRank": _OLD,
            "outOf": _OUT,
        },
    },
}


def test_pct_gain_over_base_matches_akasha_card() -> None:
    assert abs(pct_gain_over_base(554445.8, _BASE) - 3.033) < 0.01
    assert abs(pct_gain_over_base(548788.2, _BASE) - 1.981) < 0.01
    assert abs(pct_gain_over_base(540232.3, _BASE) - 0.391) < 0.01


def test_dmg_gain_over_base() -> None:
    assert abs(dmg_gain_over_base(554445.8, _BASE) - 16318.8823598665) < 0.01


def test_should_show_hides_zero_gain_except_crit() -> None:
    assert should_show_substat("ATK%", _BASE, _BASE) is False
    assert should_show_substat("Crit RATE", _BASE, _BASE) is True
    assert should_show_substat("Crit DMG", _BASE, _BASE) is True
    assert should_show_substat("HP%", 548788.2, _BASE) is True


def test_parse_and_compute_board() -> None:
    parsed = parse_substat_priority_payload({"ttl": 0, "data": [_ITEM]})
    assert parsed is not None
    assert len(parsed) == 1
    board = compute_substat_priority_board(parsed[0])
    assert board["calculation_id"] == "1000012514170er"
    assert board["weapon_name"] == "Favonius Codex"
    assert board["variant"] == "170% ER"
    names = [g["name"] for g in board["gains"]]
    assert "ATK%" not in names
    assert names == ["Flat HP", "HP%", "Crit RATE", "Crit DMG", "Elemental Mastery"]
    crit = [g for g in board["gains"] if g["name"] == "Crit DMG"][0]
    assert abs(crit["pct_gain"] - 3.033) < 0.01
    assert crit["rank_delta"] == _OLD - 9655
    assert crit["roll"] == 7.77


def test_compute_boards_skips_hidden() -> None:
    hidden = {
        "calculation": {**_ITEM["calculation"], "hidden": True, "calculationId": "hidden1"},
        "substats": _ITEM["substats"],
    }
    parsed = parse_substat_priority_payload({"data": [_ITEM, hidden]})
    assert parsed is not None
    boards = compute_substat_priority_boards(parsed)
    assert len(boards) == 1
    assert find_substat_priority_board(boards, "1000012514170er") is not None
    assert find_substat_priority_board(boards, "missing") is None
    all_boards = compute_substat_priority_boards(parsed, include_hidden=True)
    assert len(all_boards) == 2


def test_parse_rejects_bad_payload() -> None:
    assert parse_substat_priority_payload("nope") is None
    assert parse_substat_priority_payload({"data": "x"}) is None
    assert parse_substat_priority_payload({"data": [{"calculation": {}}]}) is None
