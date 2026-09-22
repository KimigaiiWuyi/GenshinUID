from __future__ import annotations

import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_ALIAS = _ROOT / "GenshinUID" / "utils" / "map" / "data" / "weapon_alias.json"
_WEAPON_DIR = _ROOT / "GenshinUID" / "tools" / "gs_data" / "weapon"
_SCRIPT = _ROOT / "GenshinUID" / "tools" / "build_weapon_alias.py"


def _load_builder():
    spec = spec_from_file_location("build_weapon_alias", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _weapon_names() -> set[str]:
    names: set[str] = set()
    for path in _WEAPON_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "name" in data and isinstance(data["name"], str):
            names.add(data["name"])
    return names


def test_weapon_alias_covers_every_weapon_without_collisions() -> None:
    raw = json.loads(_ALIAS.read_text(encoding="utf-8"))
    assert set(raw) == _weapon_names()
    seen: dict[str, str] = {}
    for name, aliases in raw.items():
        assert isinstance(aliases, list)
        for alias in aliases:
            assert isinstance(alias, str) and alias and alias != name
            assert alias not in seen, f"{alias} → {seen.get(alias)} / {name}"
            seen[alias] = name
    assert "银缸" in raw["银釭"]
    assert "胡桃专武" in raw["护摩之杖"]
    assert "琴专武" in raw["风鹰剑"]
    assert raw["幽夜华尔兹"] == ["菲谢尔专武"]
    assert "万叶专武" not in raw["苍古自由之誓"]
    assert "枫原万叶专武" in raw["苍古自由之誓"]
    assert "环穿之喙" in raw["鹮穿之喙"]


def test_playable_characters_have_alias_entries() -> None:
    alias = json.loads(
        (_ROOT / "GenshinUID" / "utils" / "map" / "data" / "char_alias.json").read_text(encoding="utf-8")
    )
    names: set[str] = set()
    for path in (_ROOT / "GenshinUID" / "tools" / "gs_data" / "char").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "name" not in data or "rank" not in data:
            continue
        if data["rank"] not in (4, 5) or not isinstance(data["name"], str):
            continue
        names.add(data["name"])
    missing = sorted(names - set(alias))
    assert missing == []
    assert "伊涅夫" in alias["伊涅芙"]
    assert "女高音" in alias["沃雅妮莎"]
    assert "风仙" in alias["薇斯纳"]


def test_signature_nickname_resolves_without_storing_it() -> None:
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("weapon_names", _ROOT / "GenshinUID" / "utils" / "map" / "weapon_names.py")
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    weapons = json.loads(_ALIAS.read_text(encoding="utf-8"))
    chars = json.loads(
        (_ROOT / "GenshinUID" / "utils" / "map" / "data" / "char_alias.json").read_text(encoding="utf-8")
    )
    assert module.resolve_weapon_name("皇女专武", weapons, chars) == "幽夜华尔兹"
    assert module.resolve_weapon_name("万叶专武", weapons, chars) == "苍古自由之誓"
    expanded = module.expand_signature_aliases(["菲谢尔专武"], {"菲谢尔": ["皇女", "Fischl"]})
    assert "皇女专武" in expanded
    assert "Fischl专武" not in expanded


def test_weapon_alias_json_matches_script() -> None:
    raw = json.loads(_ALIAS.read_text(encoding="utf-8"))
    built = _load_builder().build_alias_map()
    assert built == raw
    for aliases in raw.values():
        for alias in aliases:
            assert not any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in alias)
