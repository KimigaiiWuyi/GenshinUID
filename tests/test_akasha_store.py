from __future__ import annotations

import sys
import json
import types
import asyncio
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_ENKA = _ROOT / "GenshinUID" / "genshinuid_enka"
_CV = _ROOT / "GenshinUID" / "utils" / "api" / "cv"
_FIX = _ROOT / "test_output" / "gs_detail"

_fake = types.ModuleType("GenshinUID.genshinuid_enka")
_fake.__path__ = [str(_ENKA)]
sys.modules["GenshinUID.genshinuid_enka"] = _fake

_SIDE_SPEC = spec_from_file_location(
    "GenshinUID.genshinuid_enka.akasha_side",
    _ENKA / "akasha_side.py",
)
assert _SIDE_SPEC is not None and _SIDE_SPEC.loader is not None
_SIDE = module_from_spec(_SIDE_SPEC)
sys.modules["GenshinUID.genshinuid_enka.akasha_side"] = _SIDE
_SIDE_SPEC.loader.exec_module(_SIDE)

_STORE_SPEC = spec_from_file_location(
    "GenshinUID.genshinuid_enka.akasha_store",
    _ENKA / "akasha_store.py",
)
assert _STORE_SPEC is not None and _STORE_SPEC.loader is not None
_STORE = module_from_spec(_STORE_SPEC)
sys.modules["GenshinUID.genshinuid_enka.akasha_store"] = _STORE
_STORE_SPEC.loader.exec_module(_STORE)

akasha_char_path = _STORE.akasha_char_path
load_akasha_side = _STORE.load_akasha_side
dump_akasha_sides = _STORE.dump_akasha_sides


def test_load_missing(tmp_path: Path) -> None:
    assert load_akasha_side("0", "10000120", root=tmp_path) is None


def test_load_empty_payload(tmp_path: Path) -> None:
    path = akasha_char_path("u", "10000120", tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("{}", encoding="utf-8")
    assert load_akasha_side("u", "10000120", root=tmp_path) is None


def test_load_flins_fixtures(tmp_path: Path) -> None:
    payload = {
        "md5": "x",
        "time": "2026-09-11 12:00:00",
        "character_id": "10000120",
        "substat": json.loads((_FIX / "akasha_sp_10000120.json").read_text(encoding="utf-8")),
        "leaderboards": json.loads((_FIX / "akasha_lb_10000120.json").read_text(encoding="utf-8")),
        "damage": json.loads((_FIX / "akasha_dd_10000120.json").read_text(encoding="utf-8")),
        "global": json.loads((_FIX / "akasha_global_10000120.json").read_text(encoding="utf-8")),
    }
    path = akasha_char_path("u", "10000120", tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_akasha_side("u", "10000120", root=tmp_path)
    assert loaded is not None
    boards, rows, dists, ranks = loaded
    assert boards
    assert rows
    assert dists
    assert ranks
    assert ranks[0]["uid"] == "100740568"
    assert ranks[0]["rank"] > 1


class _FakeCv:
    def __init__(self, blobs: dict[str, object]) -> None:
        self.blobs = blobs
        self.urls: list[str] = []

    async def get_json(self, url: str, _params: dict[str, str] | None = None) -> object:
        self.urls.append(url)
        if "substatPriority" in url:
            return self.blobs["substat"]
        if "damageDistribution" in url:
            return self.blobs["damage"]
        if "/leaderboards/" in url:
            return self.blobs["leaderboards"]
        if "leaderboards" in url:
            return self.blobs["global"]
        return 1

    async def close(self) -> None:
        return None


def test_dump_then_load(tmp_path: Path) -> None:
    blobs = {
        "substat": json.loads((_FIX / "akasha_sp_10000120.json").read_text(encoding="utf-8")),
        "leaderboards": json.loads((_FIX / "akasha_lb_10000120.json").read_text(encoding="utf-8")),
        "damage": json.loads((_FIX / "akasha_dd_10000120.json").read_text(encoding="utf-8")),
        "global": json.loads((_FIX / "akasha_global_10000120.json").read_text(encoding="utf-8")),
    }
    api = _FakeCv(blobs)
    asyncio.run(
        dump_akasha_sides(
            "u",
            {"10000120": {"md5": "cf479527e2fa26599d5d4abddd32ea99", "time": "t"}},
            "2026-09-11 12:00:00",
            api=api,
            root=tmp_path,
        )
    )
    assert any("substatPriority" in u for u in api.urls)
    loaded = load_akasha_side("u", "10000120", root=tmp_path)
    assert loaded is not None
    boards, rows, dists, ranks = loaded
    assert boards
    assert rows
    assert dists
    assert ranks


def test_dump_skips_empty_md5(tmp_path: Path) -> None:
    api = _FakeCv({})
    asyncio.run(dump_akasha_sides("u", {"10000120": {"md5": "", "time": "t"}}, "now", api=api, root=tmp_path))
    assert api.urls == []
    assert load_akasha_side("u", "10000120", root=tmp_path) is None
