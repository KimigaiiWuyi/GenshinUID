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

_DD_SPEC = spec_from_file_location(
    "akasha_cv.damage_distribution",
    _CV / "damage_distribution.py",
    submodule_search_locations=[str(_CV)],
)
assert _DD_SPEC is not None and _DD_SPEC.loader is not None
_DD = module_from_spec(_DD_SPEC)
sys.modules["akasha_cv.damage_distribution"] = _DD
_DD_SPEC.loader.exec_module(_DD)

board_calculation_id = _DD.board_calculation_id
part_total = _DD.part_total
pct_of_result = _DD.pct_of_result
parse_damage_distribution_payload = _DD.parse_damage_distribution_payload
list_visible_distributions = _DD.list_visible_distributions
find_damage_distribution = _DD.find_damage_distribution

_WEAPON = {
    "name": "Favonius Codex",
    "icon": "UI_EquipIcon_Catalyst_Zephyrus_Awaken",
    "substat": "Energy Recharge",
    "type": "Catalyst",
    "rarity": 4,
    "weaponId": "14401",
    "refinement": 5,
}

_LUNAR = {
    "id": "1000012514",
    "result": 538126.9165834138,
    "calculation": {
        "name": "Lunar-Crystallize Team, Avg DMG",
        "short": "LUNAR",
        "weapon": _WEAPON,
    },
    "additional": [
        {"name": "Elemental Burst DMG", "value": 22431.48075440597, "quantity": 1, "type": "Q"},
        {"name": "Elemental Skill Cast DMG", "value": 11635.146832804061, "quantity": 1, "type": "E"},
        {
            "name": "Gravity Ripple: Continuous DMG",
            "value": 6513.362927998287,
            "quantity": 9,
            "type": "E",
        },
        {
            "name": "Gravity Interference: Lunar-Crystallize DMG",
            "value": 128177.59596206436,
            "quantity": 3,
            "type": "LCR",
        },
        {
            "name": "Lunar-Crystallize (30%) Avg DMG",
            "value": 9136.068481798477,
            "quantity": 6,
            "type": "LCR",
        },
        {
            "name": "Lunar-Crystallize (5%) Avg DMG",
            "value": 1522.6780802997462,
            "quantity": 4,
            "type": "LCR",
        },
    ],
}

_HIDDEN = {
    "id": "1000012599",
    "result": 100.0,
    "calculation": {
        "name": "Hidden Team",
        "short": "X",
        "weapon": _WEAPON,
        "hidden": True,
    },
    "additional": [{"name": "EM Result", "value": 100.0, "quantity": 1, "type": "EM"}],
}

_TIME = {
    "id": "1000004700",
    "result": 50.0,
    "calculation": {
        "name": "Timed Team",
        "short": "DPS",
        "weapon": _WEAPON,
    },
    "additional": [
        {"name": "N1", "value": 400.0, "quantity": 2, "type": "N"},
        {"name": "Time", "value": 20.0, "quantity": 1, "type": "?"},
        {"name": "Q", "value": 200.0, "quantity": 1, "type": "Q"},
    ],
}

_PAYLOAD = {"ttl": 0, "data": [_LUNAR, _HIDDEN]}


def test_board_calculation_id_strips_variant() -> None:
    assert board_calculation_id("1000012514170er") == "1000012514"
    assert board_calculation_id("1000012514") == "1000012514"


def test_pct_of_result_and_part_total() -> None:
    total = part_total(6513.362927998287, 9)
    assert abs(total - 58620.26635198458) < 1e-6
    assert abs(pct_of_result(22431.48075440597, 538126.9165834138) - 4.168) < 0.01


def test_parse_columbina_lunar_board() -> None:
    parsed = parse_damage_distribution_payload(_PAYLOAD)
    assert parsed is not None
    board = find_damage_distribution(parsed, "1000012514170er")
    assert board is not None
    assert board["short"] == "LUNAR"
    assert board["weapon_name"] == "Favonius Codex"
    assert board["weapon_id"] == "14401"
    assert board["time_sec"] is None
    assert board["dps"] is None
    names = [p["name"] for p in board["parts"]]
    assert names[0] == "Elemental Burst DMG"
    ripple = [p for p in board["parts"] if p["type"] == "E" and p["quantity"] == 9][0]
    assert abs(ripple["total"] - 58620.26635198458) < 1e-6
    assert abs(ripple["pct"] - pct_of_result(ripple["total"], board["result"])) < 1e-9
    assert abs(sum(p["total"] for p in board["parts"]) - board["formula_sum"]) < 1e-6


def test_visible_skips_hidden() -> None:
    parsed = parse_damage_distribution_payload(_PAYLOAD)
    assert parsed is not None
    visible = list_visible_distributions(parsed)
    assert [b["calculation_id"] for b in visible] == ["1000012514"]
    all_boards = list_visible_distributions(parsed, include_hidden=True)
    assert len(all_boards) == 2


def test_time_row_becomes_dps() -> None:
    parsed = parse_damage_distribution_payload({"data": [_TIME]})
    assert parsed is not None
    board = parsed[0]
    assert board["time_sec"] == 20.0
    assert board["dps"] == 50.0
    assert board["formula_sum"] == 1000.0
    names = [p["name"] for p in board["parts"]]
    assert "Time" not in names
    assert names == ["N1", "Q"]
    n1 = board["parts"][0]
    assert n1["total"] == 800.0
    assert abs(n1["pct"] - 80.0) < 1e-9


def test_parse_rejects_bad_payload() -> None:
    assert parse_damage_distribution_payload("nope") is None
    assert parse_damage_distribution_payload({"data": {}}) is None
    assert parse_damage_distribution_payload({"data": [{"id": "x"}]}) is None
