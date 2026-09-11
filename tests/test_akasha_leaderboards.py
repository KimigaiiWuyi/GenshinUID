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

_LB_SPEC = spec_from_file_location(
    "akasha_cv.build_leaderboards",
    _CV / "build_leaderboards.py",
    submodule_search_locations=[str(_CV)],
)
assert _LB_SPEC is not None and _LB_SPEC.loader is not None
_LB = module_from_spec(_LB_SPEC)
sys.modules["akasha_cv.build_leaderboards"] = _LB
_LB_SPEC.loader.exec_module(_LB)

top_percentile = _LB.top_percentile
parse_build_leaderboards_payload = _LB.parse_build_leaderboards_payload
list_visible_leaderboards = _LB.list_visible_leaderboards
find_build_leaderboard = _LB.find_build_leaderboard
extract_build_md5 = _LB.extract_build_md5

_WEAPON = {
    "name": "Favonius Codex",
    "icon": "UI_EquipIcon_Catalyst_Zephyrus_Awaken",
    "substat": "Energy Recharge",
    "type": "Catalyst",
    "rarity": 4,
    "weaponId": "14401",
    "refinement": 5,
}

_TEAMMATES = [
    {
        "character": {
            "name": "Columbina",
            "element": "Hydro",
            "rarity": 5,
            "icon": "icon-c",
            "constellation": 0,
        },
        "weapon": {
            "name": "Favonius Codex",
            "icon": "icon-w",
            "rarity": 4,
            "refinement": 5,
            "weaponId": "14401",
        },
    },
    {
        "character": {
            "name": "Linnea",
            "element": "Geo",
            "rarity": 5,
            "icon": "icon-l",
            "artifactSetIcon": "https://enka.network/ui/undefined.png",
        },
    },
]

_FIT = {
    "calculationId": "1000012514",
    "short": "LUNAR",
    "name": "Lunar-Crystallize Team, Avg DMG",
    "ranking": 19955,
    "outOf": 610037,
    "result": 538126.9176401335,
    "hidden": False,
    "priority": 2,
    "variant": {"name": "170er", "displayName": "170% ER"},
    "weapon": _WEAPON,
    "teammates": _TEAMMATES,
}

_BASE = {
    "short": "LUNAR",
    "name": "Lunar-Crystallize Team, Avg DMG",
    "ranking": 53221,
    "outOf": 767938,
    "result": 538126.9176401335,
    "hidden": False,
    "priority": 2,
    "weapon": _WEAPON,
    "teammates": _TEAMMATES,
}

_HIDDEN = {
    "short": "ON-FIELD",
    "name": "On-Field Main DPS Team, Avg DMG",
    "ranking": 1,
    "outOf": 100,
    "result": 1.0,
    "hidden": True,
    "priority": 0,
    "label": "niche",
    "weapon": _WEAPON,
    "teammates": _TEAMMATES,
}

_PAYLOAD = {
    "ttl": 0,
    "data": {
        "calculations": {
            "1000012514170er": _FIT,
            "1000012514": _BASE,
            "hidden1": _HIDDEN,
        }
    },
}


def test_top_percentile_matches_akasha_card() -> None:
    assert top_percentile(19955, 610037) == 4.0
    assert abs(top_percentile(19955, 610037, decimals=1) - 3.3) < 1e-9
    assert top_percentile(1, 1) == 100.0


def test_parse_uses_dict_key_not_calculationId_field() -> None:
    parsed = parse_build_leaderboards_payload(_PAYLOAD)
    assert parsed is not None
    fit = find_build_leaderboard(parsed, "1000012514170er")
    assert fit is not None
    assert fit["calculation_id"] == "1000012514170er"
    assert fit["variant_name"] == "170er"
    assert fit["variant_display"] == "170% ER"
    assert fit["ranking"] == 19955
    assert fit["top_pct"] == 4.0
    assert fit["weapon"]["name"] == "Favonius Codex"
    assert fit["teammates"][1]["weapon"] is None
    assert fit["teammates"][1]["character"]["name"] == "Linnea"


def test_visible_list_skips_hidden_and_sorts_by_rank() -> None:
    parsed = parse_build_leaderboards_payload(_PAYLOAD)
    assert parsed is not None
    visible = list_visible_leaderboards(parsed)
    assert [row["calculation_id"] for row in visible] == ["1000012514170er", "1000012514"]
    all_rows = list_visible_leaderboards(parsed, include_hidden=True)
    assert all_rows[0]["calculation_id"] == "hidden1"
    assert all_rows[0]["label"] == "niche"


def test_parse_rank_tilde_and_int_weapon_id() -> None:
    weapon = {**_WEAPON, "weaponId": 11519}
    payload = {
        "data": {
            "calculations": {
                "x": {
                    "short": "LUNAR",
                    "name": "Team",
                    "ranking": "~12",
                    "outOf": 100,
                    "result": 9.0,
                    "weapon": weapon,
                    "teammates": [],
                }
            }
        }
    }
    parsed = parse_build_leaderboards_payload(payload)
    assert parsed is not None
    assert parsed[0]["ranking"] == 12
    assert parsed[0]["weapon"]["weaponId"] == "11519"
    assert parsed[0]["top_pct"] == 12.0


def test_parse_skips_stub_teammates_and_bad_rows() -> None:
    payload = {
        "data": {
            "calculations": {
                "good": {
                    "short": "SOLO",
                    "name": "Solo",
                    "ranking": 10,
                    "outOf": 100,
                    "result": 1.0,
                    "weapon": _WEAPON,
                    "teammates": [
                        {
                            "character": {
                                "name": "Xiao",
                                "element": "Anemo",
                                "rarity": 5,
                                "icon": "x.png",
                                "constellation": 0,
                            }
                        },
                        {"character": {"name": "x"}},
                    ],
                },
                "bad": {"short": 1},
            }
        }
    }
    parsed = parse_build_leaderboards_payload(payload)
    assert parsed is not None
    assert len(parsed) == 1
    assert parsed[0]["calculation_id"] == "good"
    assert len(parsed[0]["teammates"]) == 1
    assert parsed[0]["teammates"][0]["character"]["name"] == "Xiao"


def test_parse_rejects_bad_payload() -> None:
    assert parse_build_leaderboards_payload("nope") is None
    assert parse_build_leaderboards_payload({"data": []}) is None
    assert parse_build_leaderboards_payload({"data": {"calculations": {"a": {}}}}) == []


def test_extract_build_md5_current_then_fallback() -> None:
    raw = {
        "data": [
            {"characterId": 10000120, "type": "saved", "md5": "saved-md5"},
            {"characterId": "10000120", "type": "current", "md5": "cur-md5"},
            {"characterId": "10000033", "md5": "childe-md5"},
        ]
    }
    assert extract_build_md5(raw, "10000120") == "cur-md5"
    assert extract_build_md5(raw, "10000033") == "childe-md5"
    assert extract_build_md5({"data": []}, "10000120") is None
