from __future__ import annotations

import sys
import json
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

_GR_SPEC = spec_from_file_location(
    "akasha_cv.global_ranks",
    _CV / "global_ranks.py",
    submodule_search_locations=[str(_CV)],
)
assert _GR_SPEC is not None and _GR_SPEC.loader is not None
_GR = module_from_spec(_GR_SPEC)
sys.modules["akasha_cv.global_ranks"] = _GR
_GR_SPEC.loader.exec_module(_GR)

parse_global_ranks_payload = _GR.parse_global_ranks_payload


def test_parse_flins_global_ranks() -> None:
    raw = json.loads((_ROOT / "test_output" / "gs_detail" / "akasha_global_10000120.json").read_text(encoding="utf-8"))
    parsed = parse_global_ranks_payload(raw, 600000)
    assert parsed is not None
    assert len(parsed) == 5
    first = parsed[0]
    assert first["uid"] == "100740568"
    assert first["rank"] > 1
    assert first["out_of"] == 600000
    assert first["nickname"]
    assert first["weapon_id"]
    assert first["result"] > 0
    assert first["hp"] > 0
    assert first["atk"] > 0
    assert first["cv"] > 0
    assert first["character_id"]


def test_parse_rejects_bad_payload() -> None:
    assert parse_global_ranks_payload("nope", 10) is None
    assert parse_global_ranks_payload({"data": {}}, 10) is None
    assert parse_global_ranks_payload({"data": []}, 0) is None
