"""幽境危战的血量合计、近几期趋势与立绘裁剪。不访问网络。"""

from __future__ import annotations

import re
import asyncio
import importlib

from PIL import Image

_ley = importlib.import_module("GenshinUID.genshinuid_guide.lunaris_leyline")
_tower = importlib.import_module("GenshinUID.genshinuid_guide.lunaris_tower")
_icons = importlib.import_module("GenshinUID.genshinuid_guide.lunaris_icons")
_html = importlib.import_module("GenshinUID.genshinuid_guide.html_endgame")


def _lane(name: str, n5: float, n6: float) -> dict:
    hps: list[dict] = []
    if n5 > 0:
        hps.append({"label": "N5", "level": 105, "hp": n5})
    hps.append({"label": "N6", "level": 110, "hp": n6})
    return {
        "name": name,
        "icon": f"UI_MonsterIcon_{name}.png",
        "special": "",
        "mechs": [],
        "tips": [],
        "tags": [],
        "resists": [],
        "hps": hps,
    }


def _view(lanes: list[dict]) -> dict:
    return {
        "schedule_id": "5269012",
        "name": "7.1",
        "begin": "2026-08-11 10:00:00",
        "end": "2026-09-08 03:59:59",
        "monster_level": 110,
        "other_levels": [105],
        "lanes": lanes,
    }


def test_lane_totals_sums_n5_and_n6() -> None:
    view = _view([_lane("A", 10.0, 100.0), _lane("B", 20.0, 200.0), _lane("C", 30.0, 300.0)])
    assert _ley.lane_totals(view) == (60.0, 600.0)


def test_lane_totals_handles_missing_n5() -> None:
    """N5 不是每期都有，缺的那条不能当成 0 血。"""
    view = _view([_lane("A", 0.0, 100.0), _lane("B", 20.0, 200.0)])
    assert _ley.lane_totals(view) == (20.0, 300.0)


def _payload(hp: float) -> dict:
    """能过 parse_leyline 的最小危战正文：一个 N5 关卡 + 一个 N6 关卡。"""
    return {
        "scheduleId": 5269004,
        "scheduleStartTime": "2026-04-15 10:00:00",
        "scheduleEndTime": "2026-05-27 09:59:59",
        "challengeName": "6.5",
        "levels": [
            {
                "monsterLevel": 105,
                "levelConfigs": [
                    {
                        "chsLevelName": "A",
                        "specialMonsterIcon": "UI_MonsterIcon_A.png",
                        "monsterStats": {"hp": hp},
                    }
                ],
            },
            {
                "monsterLevel": 110,
                "levelConfigs": [
                    {
                        "chsLevelName": "A",
                        "specialMonsterIcon": "UI_MonsterIcon_A.png",
                        "monsterStats": {"hp": hp * 2},
                    }
                ],
            },
        ],
    }


def test_parse_leyline_feeds_lane_totals() -> None:
    parsed = _ley.parse_leyline(_payload(12_500_000.0))
    assert not isinstance(parsed, str)
    assert _ley.lane_totals(parsed) == (12_500_000.0, 25_000_000.0)


def test_trend_window_ends_at_current_and_skips_gaps() -> None:
    metas = [
        {
            "id": f"52690{n:02d}",
            "start": f"2026-0{n}-01 10:00:00",
            "end": f"2026-0{n}-20 03:59:59",
            "name": f"v{n}",
        }
        for n in range(1, 7)
    ]
    seen: list[str] = []

    async def fake_index() -> list[dict]:
        return metas

    async def fake_body(schedule_id: str) -> dict:
        seen.append(schedule_id)
        if schedule_id == "5269005":
            return None  # 这一期取不到，趋势里就该缺一个点
        return _payload(float(schedule_id[-2:]) * 1_000_000.0)

    saved: dict[str, tuple[float, float]] = {}

    async def fake_load() -> dict[str, tuple[float, float]]:
        return dict(saved)

    async def fake_save(rows: dict[str, tuple[float, float]]) -> None:
        saved.clear()
        saved.update(rows)

    original = (_ley._load_index, _ley._body, _ley._load_hp_cache, _ley._save_hp_cache)
    _ley._load_index, _ley._body = fake_index, fake_body
    _ley._load_hp_cache, _ley._save_hp_cache = fake_load, fake_save
    try:
        # 当期由调用方注入，不该出现在待下载列表里
        rows = asyncio.run(_ley.fetch_leyline_trend("5269006", (66.0, 88.0), count=3))
    finally:
        _ley._load_index, _ley._body = original[0], original[1]
        _ley._load_hp_cache, _ley._save_hp_cache = original[2], original[3]

    # 5269005 请求了但拿不到，趋势里就该空着，不能拿 0 顶替
    assert [row["id"] for row in rows] == ["5269004", "5269006"]
    assert rows[0]["n5"] == 4_000_000.0
    assert rows[0]["n6"] == 8_000_000.0
    assert rows[0]["current"] is False
    assert rows[-1] == _ley.LeyTrendRow(id="5269006", label="v6", n5=66.0, n6=88.0, current=True)
    # 当期走注入，历史才下载
    assert "5269006" not in seen
    assert seen == ["5269004", "5269005"]


def test_trend_returns_empty_for_unknown_period() -> None:
    async def fake_index() -> list[dict]:
        return [{"id": "5269001", "start": "2026-01-01 10:00:00", "end": "2026-02-01 03:59:59", "name": "v1"}]

    original = _ley._load_index
    _ley._load_index = fake_index
    try:
        assert asyncio.run(_ley.fetch_leyline_trend("5269999", (1.0, 2.0))) == []
    finally:
        _ley._load_index = original


def test_trend_chart_needs_two_points_and_marks_current() -> None:
    assert _html._ley_trend_block([]) == ""
    one = [_ley.LeyTrendRow(id="1", label="7.0", n5=1.0, n6=2.0, current=True)]
    assert _html._ley_trend_block(one) == ""
    rows = [
        _ley.LeyTrendRow(id="a", label="7.0", n5=31_932_176.0, n6=66_782_411.0, current=False),
        _ley.LeyTrendRow(id="b", label="7.1", n5=31_769_614.0, n6=69_348_260.0, current=True),
    ]
    svg = _html._ley_trend_block(rows)
    assert svg.count("<polyline") == 2
    assert "近 2 期" in svg
    # 本期两条线的合计直接标在图下
    assert "HP 3177万" in svg
    assert "HP 6934.8万" in svg
    # 共用 0 起的纵轴，N6 明显更高，两条线不能画成同一条
    shapes = re.findall(r'<polyline points="([^"]+)"', svg)
    assert len(shapes) == 2
    assert shapes[0] != shapes[1]


def test_trim_art_crops_transparent_border(tmp_path) -> None:
    src = tmp_path / "src.png"
    dest = tmp_path / "dst.png"
    image = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    image.paste((255, 0, 0, 255), (200, 150, 824, 861))  # 624x711 的实心主体
    image.save(src)
    assert asyncio.run(_icons._trim_art(src, dest)) is True
    trimmed = Image.open(dest)
    # 1% padding 按 1024 的长边算，约 10px
    assert 640 <= trimmed.width <= 650
    assert 725 <= trimmed.height <= 735
    assert trimmed.convert("RGBA").getchannel("A").getbbox() is not None


def test_trim_art_rejects_blank_image(tmp_path) -> None:
    src = tmp_path / "blank.png"
    dest = tmp_path / "blank_dst.png"
    Image.new("RGBA", (256, 256), (0, 0, 0, 0)).save(src)
    assert asyncio.run(_icons._trim_art(src, dest)) is False
    assert not dest.exists()


def _mon(name: str, count: int, hp: int) -> dict:
    return {"name": name, "icon": f"UI_MonsterIcon_{name}.png", "count": count, "hp": hp}


def _abyss_view() -> dict:
    chamber = {
        "name": "12-1",
        "level": 100,
        "upper": [_mon("丘丘人", 3, 1_000_000)],
        "lower": [_mon("丘丘游侠", 2, 500_000)],
        "upper_buff": "",
        "lower_buff": "",
    }
    return {
        "floor": 12,
        "schedule_id": "20097",
        "buff_name": "骇星之月",
        "buff_desc": "",
        "open_time": "2026-08-25 04:00:00",
        "close_time": "2026-09-16 03:59:59",
        "chambers": [chamber],
    }


def test_abyss_totals_multiply_by_count() -> None:
    """总血量必须按只数算。同名 3 只和 1 只不是一个量级。"""
    view = _abyss_view()
    assert _tower.floor_totals(view) == (3_000_000.0, 1_000_000.0)
    rows = _tower.chamber_hps(view)
    assert rows == [_tower.TowerChamberHp(name="12-1", upper=3_000_000.0, lower=1_000_000.0)]


def test_abyss_trend_block_shows_line_and_bars() -> None:
    view = _abyss_view()
    trend = [
        _tower.TowerTrendRow(id="20096", label="辉卷", upper=20_000_000.0, lower=18_000_000.0, current=False),
        _tower.TowerTrendRow(id="20097", label="骇星", upper=30_000_000.0, lower=12_000_000.0, current=True),
    ]
    bars = [(item["name"], item["upper"], item["lower"]) for item in _tower.chamber_hps(view)]
    block = _html._abyss_trend_block(trend, bars)
    assert "上半" in block and "下半" in block
    assert "HP 3000万" in block
    assert "HP 1200万" in block
    # 当期逐间：两个半区各一根条
    assert block.count('class="hpbar"') == 2
    short = _html._abyss_trend_block(trend[:1], bars)
    assert 'class="hpbar"' in short and "<polyline" not in short  # 折线不够两点就只出条
    assert _html._abyss_trend_block([], []) == ""


def test_abyss_line_chart_area_follows_the_taller_series() -> None:
    """面积填充要铺在更高的那条线下面，不能拿低的那条。"""
    svg = _html._hp_line_chart(["a", "b"], [1], [([1.0, 2.0], "#111", "#aaa"), ([9.0, 8.0], "#222", "#bbb")], "#222")
    assert svg != ""
    assert "HP" not in svg  # 纯图表，不带文案
    assert svg.count("<polyline") == 2
    assert _html._hp_line_chart(["a"], [], [([1.0], "#111", "#aaa")], "#111") == ""
