"""元素图标：``texture2d/element/{风雷…}.png``。英文/中文/「雷元素伤害加成」都能解析。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from .RESOURCE_PATH import ELEMENT_ICON_PATH

_EN_TO_ZH: dict[str, str] = {
    "Anemo": "风",
    "Cryo": "冰",
    "Dendro": "草",
    "Electro": "雷",
    "Geo": "岩",
    "Hydro": "水",
    "Pyro": "火",
}
_ZH: tuple[str, ...] = ("风", "雷", "水", "火", "冰", "岩", "草")


def element_zh(token: str) -> str:
    if not token:
        return ""
    if token in _EN_TO_ZH:
        return _EN_TO_ZH[token]
    for zh in _ZH:
        if token == zh or token.startswith(zh):
            return zh
    return ""


def element_icon_path(token: str) -> Path | None:
    zh = element_zh(token)
    if not zh:
        return None
    path = ELEMENT_ICON_PATH / f"{zh}.png"
    if not path.exists():
        return None
    return path


def open_element_icon(token: str) -> Image.Image | None:
    path = element_icon_path(token)
    if path is None:
        return None
    return Image.open(path).convert("RGBA")
