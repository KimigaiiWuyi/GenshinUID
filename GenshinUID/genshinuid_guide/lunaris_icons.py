"""怪物图标落到 data/GenshinUID/data/wiki。不是 PNG 的缓存会丢掉重下。"""

import asyncio
from pathlib import Path

import httpx
import aiofiles
from PIL import Image

from gsuid_core.pool import to_thread

from ..utils.resource.RESOURCE_PATH import (
    WIKI_DATA_PATH,
    MONSTER_ICON_PATH,
    WIKI_DATA_MONSTER_ICON,
)

_AMBR_MONSTER = "https://gi.yatta.moe/assets/UI/monster"
_ENKA_UI = "https://enka.network/ui"
_LUNARIS_MONSTER = "https://api.lunaris.moe/data/assets/monster"
_LEYLINE_ART = "https://api.lunaris.moe/data/assets/leyline"
_SPRITE_ART = "https://api.lunaris.moe/data/assets/icons"
_LEYLINE_DIR = WIKI_DATA_PATH / "leyline_icon"
_ART_DIR = WIKI_DATA_PATH / "leyline_art"
_SPRITE_DIR = WIKI_DATA_PATH / "lunaris_sprite"
_PNG = b"\x89PNG\r\n\x1a\n"
_GATE = asyncio.Semaphore(4)
_ART_ALPHA_MIN = 24
_ART_PAD_RATIO = 0.01
# alpha 二值化的查表。写 lambda 会被 PIL 的重载推成 ImagePointTransform 而标红。
_ALPHA_LUT: list[int] = [0] * _ART_ALPHA_MIN + [255] * (256 - _ART_ALPHA_MIN)


def _png_name(icon: str) -> str:
    return icon if icon.endswith(".png") else f"{icon}.png"


def _png_ok(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 32:
        return False
    with path.open("rb") as handle:
        return handle.read(8) == _PNG


async def _download(url: str, dest: Path) -> Path | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with _GATE:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
                response = await client.get(url)
    except httpx.HTTPError:
        return None
    if response.status_code != 200 or not response.content.startswith(_PNG):
        return None
    async with aiofiles.open(dest, "wb") as file:
        await file.write(response.content)
    return dest


async def _first_png(urls: list[str], dest: Path) -> Path | None:
    if _png_ok(dest):
        return dest
    if dest.exists():
        dest.unlink()
    for url in urls:
        saved = await _download(url, dest)
        if saved is not None:
            return saved
    return None


async def monster_icon_file(icon: str) -> Path | None:
    if not icon:
        return None
    name = _png_name(icon)
    cached = WIKI_DATA_MONSTER_ICON / name
    if _png_ok(cached):
        return cached
    bundled = MONSTER_ICON_PATH / name
    if _png_ok(bundled):
        cached.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(bundled, "rb") as src:
            data = await src.read()
        async with aiofiles.open(cached, "wb") as dst:
            await dst.write(data)
        return cached
    stem = icon[:-4] if icon.endswith(".png") else icon
    return await _first_png(
        [
            f"{_AMBR_MONSTER}/{stem}.png",
            f"{_LUNARIS_MONSTER}/{stem}.png",
            f"{_ENKA_UI}/{stem}.png",
        ],
        cached,
    )


async def leyline_icon_file(icon: str) -> Path | None:
    """危战立绘是 UI_Img_LeyLineChallenge_*，没有再退回怪物头像。"""
    if not icon:
        return None
    stem = icon[:-4] if icon.endswith(".png") else icon
    art = stem.replace("UI_MonsterIcon_", "UI_Img_LeyLineChallenge_")
    dest = _LEYLINE_DIR / f"{art}.png"
    saved = await _first_png([f"{_LEYLINE_ART}/{art}.png"], dest)
    if saved is not None:
        return saved
    return await monster_icon_file(icon)


@to_thread
def _trim_art(source: Path, dest: Path) -> bool:
    """把 1024 方形立绘裁到主体外接框。

    原图四周有一圈透明边（横向最多占 16%），不裁的话版式只能按整张方图定位，
    主体就会跟着卡的排版漂。裁完每张卡用同一个固定框，怪物落位才一致。
    """
    with Image.open(source) as raw:
        image = raw.convert("RGBA")
    box = image.getchannel("A").point(_ALPHA_LUT).getbbox()
    if box is None:
        return False
    pad = int(max(image.size) * _ART_PAD_RATIO)
    crop = (
        max(box[0] - pad, 0),
        max(box[1] - pad, 0),
        min(box[2] + pad, image.width),
        min(box[3] + pad, image.height),
    )
    if crop[2] - crop[0] < 8 or crop[3] - crop[1] < 8:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.crop(crop).save(dest, format="PNG")
    return True


async def leyline_art_file(icon: str) -> Path | None:
    """危战立绘的裁剪版。裁剪缓存比源图旧就重裁。"""
    source = await leyline_icon_file(icon)
    if source is None:
        return None
    dest = _ART_DIR / f"{source.stem}.png"
    if _png_ok(dest) and dest.stat().st_mtime >= source.stat().st_mtime:
        return dest
    if await _trim_art(source, dest):
        return dest
    return source


async def sprite_icon_file(preset_id: str) -> Path | None:
    if not preset_id.isdigit():
        return None
    dest = _SPRITE_DIR / f"{preset_id}.png"
    return await _first_png([f"{_SPRITE_ART}/{preset_id}.png"], dest)
