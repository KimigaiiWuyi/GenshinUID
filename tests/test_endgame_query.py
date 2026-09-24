"""深渊 / 剧诗 / 幽境的日期与层数解析。不访问网络。"""

import datetime
import importlib.util
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "GenshinUID/genshinuid_guide/endgame_query.py"
_spec = importlib.util.spec_from_file_location("endgame_query_under_test", _PATH)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


def test_abyss_floor_and_date() -> None:
    floor, when, schedule_id = _mod.parse_abyss_args("11 2026.8.10")
    assert floor == 11
    assert when == datetime.date(2026, 8, 10)
    assert schedule_id == ""
    floor_only, day, sid = _mod.parse_abyss_args("11")
    assert (floor_only, day, sid) == (11, None, "")
    default_floor, dated, _sid = _mod.parse_abyss_args("2026-08-10")
    assert default_floor == 12
    assert dated == datetime.date(2026, 8, 10)
    _floor, _day, pinned = _mod.parse_abyss_args("20097")
    assert pinned == "20097"
    assert _floor == 12


def test_schedule_date_or_id() -> None:
    when, schedule_id = _mod.parse_schedule_args("2026.01.01")
    assert when == datetime.date(2026, 1, 1)
    assert schedule_id == ""
    _day, pinned = _mod.parse_schedule_args("5269012")
    assert pinned == "5269012"
    assert _day is None


def test_neighbor_is_previous_or_next_period() -> None:
    rows = [
        {"id": "20096", "begin": "2026-08-08 04:00:00", "end": "2026-08-25 03:59:59", "title": ""},
        {"id": "20097", "begin": "2026-08-25 04:00:00", "end": "2026-09-16 03:59:59", "title": ""},
        {"id": "20098", "begin": "2026-09-16 04:00:00", "end": "2026-10-07 03:59:59", "title": ""},
    ]
    today = datetime.date(2026, 9, 24)
    assert _mod.neighbor_id(rows, today, 0) == "20098"
    assert _mod.neighbor_id(rows, today, -1) == "20097"
    assert _mod.neighbor_id(rows, today, 1) == ""
    assert _mod.period_shift("下期危战信息", "") == 1
    assert _mod.period_shift("危战信息", "上期") == -1
    assert _mod.choose_id(rows, today=today, when=None, pinned="", shift=-1) == "20097"


def test_covering_id_uses_the_window() -> None:
    rows = [
        {"id": "20096", "begin": "2026-08-08 04:00:00", "end": "2026-08-25 03:59:59", "title": "辉卷"},
        {"id": "20097", "begin": "2026-08-25 04:00:00", "end": "2026-09-16 03:59:59", "title": "骇星"},
    ]
    assert _mod.covering_id(rows, datetime.date(2026, 8, 10)) == "20096"
    assert _mod.covering_id(rows, datetime.date(2026, 9, 1)) == "20097"
    assert _mod.covering_id(rows, datetime.date(2026, 1, 1)) == ""
    text = _mod.format_ranges("深渊", rows)
    assert "20096 2026-08-08~2026-08-25" in text
    assert "20097 2026-08-25~2026-09-16" in text
