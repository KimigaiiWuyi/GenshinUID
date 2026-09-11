from __future__ import annotations

import sys
import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

from PIL import Image

_ROOT = Path(__file__).resolve().parents[1]
_MOD_PATH = _ROOT / "GenshinUID" / "genshinuid_enka" / "hero_art.py"
_MAP = sorted((_ROOT / "GenshinUID" / "utils" / "map" / "data").glob("CharId2TalentIcon_mapping_*.json"))[-1]

_SPEC = spec_from_file_location("hero_art", _MOD_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = module_from_spec(_SPEC)
sys.modules["hero_art"] = _MOD
_SPEC.loader.exec_module(_MOD)

compose_hero = _MOD.compose_hero
compose_page_bg = _MOD.compose_page_bg
con_arc_points = _MOD.con_arc_points
con_arc_svg_d = _MOD.con_arc_svg_d
draw_con_arc = _MOD.draw_con_arc
fade_mask = _MOD.fade_mask
hero_frame = _MOD.hero_frame
radar_svg = _MOD.radar_svg
hero_plates = _MOD.hero_plates
split_dmg_label = _MOD.split_dmg_label
talent_icons = _MOD.talent_icons
talent_unlocked = _MOD.talent_unlocked

SCALE = 4
INNER_W = 616
HERO_H = 470
ART_W = 332
ART_FADE = 140
TXT_L = 314


def _flins_map() -> dict[str, list[str]]:
    raw = json.loads(_MAP.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    out: dict[str, list[str]] = {}
    for key, val in raw.items():
        if isinstance(key, str) and isinstance(val, list) and all(isinstance(x, str) for x in val):
            out[key] = val
    return out


def test_talent_icons_always_six_for_flins() -> None:
    icons = talent_icons("10000120", _flins_map(), "Electro")
    assert len(icons) == 6
    assert icons[0] == "UI_Talent_S_Flins_01"
    assert all(name.startswith("UI_Talent_") for name in icons)


def test_talent_unlocked_c0_is_zero() -> None:
    assert talent_unlocked({"talentList": []}) == 0
    assert talent_unlocked({}) == 0
    assert talent_unlocked({"talentList": [{}, {}, {}]}) == 3


def test_con_arc_bows_left() -> None:
    pts = con_arc_points(6, 50, 340, 6, 96)
    assert len(pts) == 6
    assert pts[0][0] > pts[2][0]
    assert pts[5][0] > pts[2][0]
    assert pts[0][0] - pts[2][0] >= 80
    assert pts[5][1] - pts[0][1] == 340
    d = con_arc_svg_d(50, 340, 6, 96, 52)
    assert d.startswith("M ")
    assert " L " in d


def test_draw_con_arc_paints_pixels() -> None:
    img = draw_con_arc(4, 164, 470, 50, 340, 6, 96, 52, "#b98cf5")
    assert img.size == (656, 1880)
    assert img.getextrema()[3][1] > 0


def test_draw_con_arc_cuts_sockets() -> None:
    img = draw_con_arc(4, 164, 470, 50, 340, 6, 96, 52, "#b98cf5")
    pts = con_arc_points(6, 50, 340, 6, 96)
    cx = (pts[2][0] + 26) * 4
    cy = (pts[2][1] + 26) * 4
    assert img.getpixel((cx, cy))[3] == 0
    mx = (pts[0][0] + pts[1][0]) // 2 + 26
    my = (pts[0][1] + pts[1][1]) // 2 + 26
    assert img.getpixel((mx * 4, my * 4))[3] > 80


def test_split_dmg_label_strips_aeq() -> None:
    assert split_dmg_label("A一段伤害") == ("A", "一段伤害")
    assert split_dmg_label("E一段伤害(月感电)") == ("E", "一段伤害(月感电)")
    assert split_dmg_label("Q雷霆交响伤害") == ("Q", "雷霆交响伤害")
    assert split_dmg_label("高空下落伤害") == ("", "高空下落伤害")


def test_hero_frame_pins_character_to_left() -> None:
    splash = Image.new("RGBA", (2048, 1024), (12, 10, 22, 255))
    splash.paste(Image.new("RGBA", (240, 480), (240, 220, 80, 255)), (904, 272))
    w, h, art_w = INNER_W * SCALE, HERO_H * SCALE, ART_W * SCALE
    frame = hero_frame(splash, w, h, art_w)
    pin = frame.getpixel((int(art_w * 0.60), h // 2))
    right = frame.getpixel((w - 24, h // 2))
    assert pin[0] > 180
    assert right[0] < 80


def test_hero_plates_share_left_pixels() -> None:
    splash = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    splash.paste(Image.new("RGBA", (1024, 40), (240, 80, 40, 255)), (0, 200))
    w, h, art_w = INNER_W * SCALE, HERO_H * SCALE, ART_W * SCALE
    full, art = hero_plates(splash, w, h, art_w)
    assert art.size == (art_w, h)
    assert full.crop((0, 0, art_w, h)).tobytes() == art.tobytes()


def test_compose_hero_art_reaches_bottom() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    hero = compose_hero(splash, "#b98cf5", SCALE, INNER_W, HERO_H, ART_W, ART_FADE, TXT_L)
    x = 80 * SCALE
    mid = hero.getpixel((x, hero.size[1] // 2))
    bot = hero.getpixel((x, hero.size[1] - 6))
    assert mid[0] > 140
    assert bot[0] > 140
    assert abs(mid[0] - bot[0]) < 36


def test_compose_hero_no_vertical_cliff_at_text() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    hero = compose_hero(splash, "#b98cf5", SCALE, INNER_W, HERO_H, ART_W, ART_FADE, TXT_L)
    y = hero.size[1] // 2
    x = TXT_L * SCALE

    def step(col: int) -> int:
        a = hero.getpixel((col, y))
        b = hero.getpixel((col + 1, y))
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])

    assert step(x) < 12
    assert step(x - 8) < 12
    assert step(x + 8) < 12


def test_compose_hero_fade_runs_full_width() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    hero = compose_hero(splash, "#b98cf5", SCALE, INNER_W, HERO_H, ART_W, ART_FADE, TXT_L)
    y = hero.size[1] // 2
    w = hero.size[0]

    def lum(col: int) -> int:
        px = hero.getpixel((col, y))
        return px[0] + px[1] + px[2]

    assert lum(24) > lum(w // 2) > lum(w - 24)


def test_text_column_keeps_splash_color() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    hero = compose_hero(splash, "#b98cf5", SCALE, INNER_W, HERO_H, ART_W, ART_FADE, TXT_L)
    y = hero.size[1] // 2
    right = hero.getpixel((TXT_L * SCALE + 80, y))
    assert right[0] > 80
    assert right[0] >= right[2]


def test_compose_hero_left_stays_bright() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    hero = compose_hero(splash, "#b98cf5", SCALE, INNER_W, HERO_H, ART_W, ART_FADE, TXT_L)
    y = hero.size[1] // 2
    left = hero.getpixel((24, y))
    right = hero.getpixel((hero.size[0] - 24, y))
    assert left[0] > 180
    assert right[0] > 80
    assert left[0] > right[0]


def test_radar_svg_empty_when_few_axes() -> None:
    assert radar_svg([("生命", "1", "1", 0.5, 0.4)], "#b98cf5") == ""


def test_radar_svg_writes_values_and_two_polygons() -> None:
    axes = [
        ("生命", "17271", "18110", 0.85, 0.90),
        ("攻击", "3082", "2612", 0.95, 0.80),
        ("防御", "987", "875", 0.88, 0.78),
        ("精通", "152", "306", 0.44, 0.90),
        ("充能", "106.5%", "110.3%", 0.86, 0.90),
        ("暴击", "66.4%", "69.5%", 0.85, 0.89),
        ("爆伤", "152.9%", "245.2%", 0.55, 0.88),
    ]
    svg = radar_svg(axes, "#b98cf5")
    assert svg.startswith("<svg")
    assert svg.count("<polygon") >= 6
    assert "17271" in svg
    assert "18110" in svg
    assert "生命" in svg
    assert "爆伤" in svg


def test_fade_mask_eases_right() -> None:
    mask = fade_mask(640, 8, 0, 100, 1.75)
    assert mask.getpixel((0, 4)) == 0
    assert mask.getpixel((639, 4)) == 100
    assert mask.getpixel((320, 4)) < 45


def test_compose_page_bg_keeps_splash_tint() -> None:
    splash = Image.new("RGBA", (1024, 1024), (210, 90, 50, 255))
    bg = compose_page_bg(splash, "#b98cf5", SCALE, 640, 1560)
    assert bg.size == (640 * SCALE, 1560 * SCALE)
    mid = bg.getpixel((320 * SCALE, 780 * SCALE))
    assert mid[0] + mid[1] + mid[2] > 90
    assert mid[0] >= mid[2]
