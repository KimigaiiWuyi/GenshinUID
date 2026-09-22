"""把 gs_data 里还没有条目的四星、五星角色补进 char_alias.json。

已有条目不改。新键先只放正式名，调用方再补错字和称呼。
旅行者元素形态等额外键保留，不删除。
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CHAR_DIR = _ROOT / "tools" / "gs_data" / "char"
_OUT = _ROOT / "utils" / "map" / "data" / "char_alias.json"


def _playable_names() -> list[str]:
    found: list[tuple[int, str]] = []
    seen: set[str] = set()
    for path in sorted(_CHAR_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        if "name" not in data or "rank" not in data:
            continue
        name = data["name"]
        rank = data["rank"]
        if not isinstance(name, str) or not name or name in seen:
            continue
        if rank not in (4, 5):
            continue
        seen.add(name)
        release = data["release"] if "release" in data and isinstance(data["release"], int) else 0
        found.append((release, name))
    found.sort()
    return [name for _release, name in found]


def missing_names(alias: dict[str, list[str]]) -> list[str]:
    return [name for name in _playable_names() if name not in alias]


def sync_char_alias() -> list[str]:
    raw = json.loads(_OUT.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SystemExit(f"不是对象：{_OUT}")
    alias: dict[str, list[str]] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, list):
            alias[key] = [item for item in value if isinstance(item, str)]
    added = missing_names(alias)
    for name in added:
        alias[name] = [name]
    if added:
        _OUT.write_text(json.dumps(alias, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return added


def main() -> None:
    added = sync_char_alias()
    if not added:
        print("char_alias.json 已包含全部四星、五星角色")
        return
    print("以下角色只有正式名，需要补错字和称呼：")
    for name in added:
        print(name)


if __name__ == "__main__":
    main()
