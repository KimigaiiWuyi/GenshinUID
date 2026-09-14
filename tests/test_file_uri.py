"""file:// URI 本机解析：存在则 path, 不存在则交给协议端。"""

from __future__ import annotations

import importlib.util
from typing import Callable
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[1] / "GenshinUID" / "tools.py"
_spec = importlib.util.spec_from_file_location("gscore_file_uri_tools", _TOOLS)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
file_uri_to_path: Callable[[str], str | None] = _mod.file_uri_to_path
existing_file_uri_path: Callable[[str], Path | None] = _mod.existing_file_uri_path


def test_file_uri_to_path_rejects_http() -> None:
    assert file_uri_to_path("https://example.com/a.jpg") is None


def test_file_uri_to_path_posix_absolute() -> None:
    got = file_uri_to_path("file:///tmp/a.jpg")
    assert got is not None
    assert Path(got).as_posix().endswith("tmp/a.jpg")


def test_file_uri_to_path_localhost() -> None:
    got = file_uri_to_path("file://localhost/tmp/a.jpg")
    assert got is not None
    assert "tmp" in Path(got).as_posix()


def test_existing_file_uri_path_missing() -> None:
    assert existing_file_uri_path("file:///definitely-missing-gsuid-test.jpg") is None


def test_existing_file_uri_path_present(tmp_path: Path) -> None:
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    uri = f.resolve().as_uri()
    got = existing_file_uri_path(uri)
    assert got is not None
    assert got.resolve() == f.resolve()
