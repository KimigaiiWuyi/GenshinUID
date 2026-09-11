from __future__ import annotations

from GenshinUID.utils.resource.element_icon import (
    element_zh,
    element_icon_path,
    open_element_icon,
)


def test_element_zh_en_and_zh() -> None:
    assert element_zh("Electro") == "雷"
    assert element_zh("Anemo") == "风"
    assert element_zh("雷") == "雷"
    assert element_zh("水元素伤害加成") == "水"
    assert element_zh("水伤") == "水"
    assert element_zh("百分比攻击力") == ""
    assert element_zh("") == ""


def test_element_icon_path_exists() -> None:
    path = element_icon_path("Electro")
    assert path is not None
    assert path.name == "雷.png"
    assert path.exists()
    assert element_icon_path("百分比攻击力") is None


def test_open_element_icon() -> None:
    img = open_element_icon("雷")
    assert img is not None
    assert img.mode == "RGBA"
    assert img.size[0] > 0
