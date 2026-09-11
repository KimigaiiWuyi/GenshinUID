"""题头立绘合成与命座图标查找。无包副作用，供面板和单测共用。"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance


def hex_rgb(color: str) -> tuple[int, int, int]:
    h = color[1:] if color.startswith("#") else color
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lin_mask(w: int, h: int, a0: int, a1: int, vertical: bool) -> Image.Image:
    span = h if vertical else w
    strip = Image.new("L", (1, span) if vertical else (span, 1))
    last = max(1, span - 1)
    for i in range(span):
        val = int(a0 + (a1 - a0) * i / last)
        strip.putpixel((0, i) if vertical else (i, 0), max(0, min(255, val)))
    return strip.resize((w, h), Image.Resampling.BILINEAR)


def fade_mask(w: int, h: int, a0: int, a1: int, power: float) -> Image.Image:
    """横向遮罩；power>1 时左侧更亮，暗部集中在右侧，全程连续。"""
    strip = Image.new("L", (w, 1))
    last = max(1, w - 1)
    for i in range(w):
        t = (i / last) ** power
        strip.putpixel((i, 0), max(0, min(255, int(a0 + (a1 - a0) * t))))
    return strip.resize((w, h), Image.Resampling.BILINEAR)


def hero_frame(splash: Image.Image, w: int, h: int, art_w: int) -> Image.Image:
    """整幅铺满题头，角色锚在左侧 ``art_w``，避免人跑到属性底下。"""
    src = splash.convert("RGBA")
    iw, ih = src.size
    if iw <= 0 or ih <= 0:
        return Image.new("RGBA", (w, h), (12, 10, 22, 255))
    scale = max(w / iw, h / ih) * 1.22
    nw, nh = max(1, round(iw * scale)), max(1, round(ih * scale))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    cx = int(nw * 0.50)
    cy = int(nh * 0.48)
    # 角色落在左侧立绘区中部，留出圆角边，避免人贴死左缘
    left = min(max(0, cx - int(art_w * 0.60)), max(0, nw - w))
    top = min(max(0, cy - h // 2), max(0, nh - h))
    return resized.crop((left, top, left + w, top + h))


def hero_plates(splash: Image.Image, w: int, h: int, art_w: int) -> tuple[Image.Image, Image.Image]:
    full = hero_frame(splash, w, h, art_w)
    return full, full.crop((0, 0, art_w, h))


def _hmask(w: int, h: int, start: int, end: int, a0: int, a1: int) -> Image.Image:
    """横向渐变：``start`` 左为 ``a0``，``end`` 右为 ``a1``。"""
    mask = Image.new("L", (w, h), a1)
    if start > 0:
        mask.paste(Image.new("L", (start, h), a0), (0, 0))
    span = max(1, end - start)
    mask.paste(lin_mask(span, h, a0, a1, False), (start, 0))
    return mask


def _enlarged(src: Image.Image, w: int, h: int, zoom: float, focus_x: int) -> Image.Image:
    """同一帧放大，焦点落在输出左侧，右侧模糊底仍是人。"""
    zw, zh = max(w + 1, round(w * zoom)), max(h + 1, round(h * zoom))
    big = src.resize((zw, zh), Image.Resampling.LANCZOS)
    fx = int(focus_x * zw / max(1, src.size[0]))
    left = min(max(0, fx - int(w * 0.28)), zw - w)
    top = min(max(0, (zh - h) // 2), zh - h)
    return big.crop((left, top, left + w, top + h))


def compose_hero(
    splash: Image.Image,
    accent: str,
    scale: int,
    inner_w: int,
    hero_h: int,
    art_w: int,
    art_fade: int,
    txt_left: int,
) -> Image.Image:
    """整幅同一张立绘铺满题头；黑从最右淡到最左，不在属性列切开。"""
    w, h = inner_w * scale, hero_h * scale
    rgb = hex_rgb(accent)
    plate = art_w * scale
    sharp = hero_frame(splash, w, h, plate)
    cap = 78 if art_fade >= 120 else 96
    veil = Image.new("RGBA", (w, h), (max(12, rgb[0] // 8), max(14, rgb[1] // 8), max(20, rgb[2] // 8), 255))
    return Image.composite(veil, sharp, fade_mask(w, h, 0, cap, 1.85))


def compose_page_bg(
    splash: Image.Image,
    accent: str,
    scale: int,
    page_w: int,
    page_h: int,
) -> Image.Image:
    """整卡底：立绘放大模糊，再盖一层上下渐变遮罩。"""
    w, h = page_w * scale, page_h * scale
    rgb = hex_rgb(accent)
    src = splash.convert("RGBA")
    iw, ih = src.size
    if iw <= 0 or ih <= 0:
        return Image.new("RGBA", (w, h), (8, 10, 16, 255))
    # 先裁有人的一块再拉满，避免横图黑边被放大成整页黑
    seed = hero_frame(src, w, max(1, int(w * 0.88)), max(1, int(w * 0.52)))
    sw, sh = seed.size
    cover = max(w / sw, h / sh) * 1.28
    nw, nh = max(1, round(sw * cover)), max(1, round(sh * cover))
    big = seed.resize((nw, nh), Image.Resampling.LANCZOS)
    left = min(max(0, (nw - w) // 2), max(0, nw - w))
    top = min(max(0, (nh - h) // 6), max(0, nh - h))
    plate = big.crop((left, top, left + w, top + h))
    blur = plate.filter(ImageFilter.GaussianBlur(14 * scale))
    blur = ImageEnhance.Brightness(blur).enhance(0.72)
    blur = ImageEnhance.Color(blur).enhance(1.18)
    out = Image.alpha_composite(blur, Image.new("RGBA", (w, h), rgb + (38,)))
    veil = Image.new("RGBA", (w, h), (7, 9, 14, 255))
    return Image.composite(veil, out, lin_mask(w, h, 20, 78, True))


def con_arc_points(
    count: int,
    top: int,
    span: int,
    left: int,
    bow: int,
) -> list[tuple[int, int]]:
    """左侧命座弧：中间更靠左。返回每个图标的 ``(left, top)``。"""
    if count <= 1:
        return [(left, top)]
    out: list[tuple[int, int]] = []
    last = count - 1
    for i in range(count):
        t = i / last
        y = top + round(span * t)
        x = left + round(bow * (1 - math.sin(math.pi * t)))
        out.append((x, y))
    return out


def con_arc_svg_d(top: int, span: int, left: int, bow: int, size: int, steps: int = 24) -> str:
    """命座连线：与 ``con_arc_points`` 同一条正弦弧。"""
    rad = size // 2
    parts: list[str] = []
    for i in range(steps + 1):
        t = i / steps
        x = left + rad + round(bow * (1 - math.sin(math.pi * t)))
        y = top + rad + round(span * t)
        parts.append(("M" if i == 0 else "L") + f" {x} {y}")
    return " ".join(parts)


def draw_con_arc(
    scale: int,
    rail_w: int,
    hero_h: int,
    top: int,
    span: int,
    left: int,
    bow: int,
    size: int,
    accent: str,
) -> Image.Image:
    """命座弧线；节点处挖圆孔当凹槽，槽里不能看见线。"""
    w, h = max(1, rail_w * scale), max(1, hero_h * scale)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    rgb = hex_rgb(accent)
    steps = 56
    pts: list[tuple[int, int]] = []
    for i in range(steps + 1):
        t = i / steps
        x = (left + size // 2) * scale + round(bow * scale * (1 - math.sin(math.pi * t)))
        y = (top + size // 2) * scale + round(span * scale * t)
        pts.append((x, y))
    draw.line(pts, fill=rgb + (90,), width=max(8, 6 * scale))
    draw.line(pts, fill=rgb + (200,), width=max(4, 3 * scale))
    draw.line(pts, fill=(236, 240, 255, 230), width=max(2, scale + 1))

    hole = Image.new("L", (w, h), 0)
    hd = ImageDraw.Draw(hole)
    rad = (size // 2 + 10) * scale
    centers: list[tuple[int, int]] = []
    for x, y in con_arc_points(6, top, span, left, bow):
        cx = (x + size // 2) * scale
        cy = (y + size // 2) * scale
        centers.append((cx, cy))
        hd.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=255)
    img.paste((0, 0, 0, 0), (0, 0), hole)

    ring = rad - max(1, scale)
    for cx, cy in centers:
        draw.ellipse(
            (cx - ring, cy - ring, cx + ring, cy + ring),
            outline=rgb + (170,),
            width=max(2, scale),
        )
    return img


def split_dmg_label(name: str) -> tuple[str, str]:
    """拆 A/E/Q 前缀，伤害表做成按键字母。"""
    kind = name[:1]
    if kind in {"A", "E", "Q"}:
        rest = name[1:].lstrip()
        if rest:
            return kind, rest
    return "", name


def talent_unlocked(card: Mapping[str, object]) -> int:
    if "talentList" not in card or not isinstance(card["talentList"], list):
        return 0
    return min(6, len(card["talentList"]))


def radar_svg(
    axes: Sequence[tuple[str, str, str, float, float]],
    accent: str,
    size: int = 196,
) -> str:
    """七维雷达：实心=当前，虚线=Akasha 1% 均；轴外写名称、当前值、1%均值。"""
    n = len(axes)
    if n < 3:
        return ""
    rgb = hex_rgb(accent)
    fill = f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.32)"
    stroke = accent
    cx = cy = size / 2
    r = size * 0.24
    start = -math.pi / 2

    def pt(index: int, t: float) -> tuple[float, float]:
        ang = start + index * 2 * math.pi / n
        return cx + r * t * math.cos(ang), cy + r * t * math.sin(ang)

    def poly(ts: list[float]) -> str:
        pts = " ".join(f"{pt(i, t)[0]:.1f},{pt(i, t)[1]:.1f}" for i, t in enumerate(ts))
        return pts

    rings: list[str] = []
    for ring in (0.25, 0.5, 0.75, 1.0):
        rings.append(
            f'<polygon points="{poly([ring] * n)}" fill="none" stroke="rgba(242,245,251,0.14)" stroke-width="0.8"/>'
        )
    spokes: list[str] = []
    for i in range(n):
        x, y = pt(i, 1.0)
        spokes.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x:.1f}" y2="{y:.1f}" '
            f'stroke="rgba(242,245,251,0.16)" stroke-width="0.8"/>'
        )
    player = [max(0.0, min(1.0, a[3])) for a in axes]
    avg = [max(0.0, min(1.0, a[4])) for a in axes]
    labels: list[str] = []
    dots: list[str] = []
    for i, (name, mine, mean, pt_t, at_t) in enumerate(axes):
        ang = start + i * 2 * math.pi / n
        ux, uy = math.cos(ang), math.sin(ang)
        lx = cx + (r + 18) * ux
        ly = cy + (r + 18) * uy
        if abs(ux) < 0.35:
            anchor = "middle"
        elif ux > 0:
            anchor = "start"
        else:
            anchor = "end"
        if uy < -0.5:
            ly -= 2
        elif uy > 0.5:
            ly += 2
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'font-size="9" fill="#f2f5fb">{name}</text>'
            f'<text x="{lx:.1f}" y="{ly + 11:.1f}" text-anchor="{anchor}" '
            f'font-size="10" font-weight="700" fill="{stroke}">{mine}</text>'
            f'<text x="{lx:.1f}" y="{ly + 21:.1f}" text-anchor="{anchor}" '
            f'font-size="8" fill="rgba(234,198,131,0.92)">{mean}</text>'
        )
        px, py = pt(i, max(0.0, min(1.0, pt_t)))
        ax, ay = pt(i, max(0.0, min(1.0, at_t)))
        dots.append(f'<circle cx="{ax:.1f}" cy="{ay:.1f}" r="2.2" fill="#eac683"/>')
        dots.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="{stroke}"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}">'
        f"{''.join(rings)}{''.join(spokes)}"
        f'<polygon points="{poly(avg)}" fill="rgba(234,198,131,0.10)" '
        f'stroke="#eac683" stroke-width="1.2" stroke-dasharray="3 2"/>'
        f'<polygon points="{poly(player)}" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
        f"{''.join(dots)}{''.join(labels)}"
        "</svg>"
    )


def talent_icons(char_id: str, mapping: Mapping[str, list[str]], element: str = "") -> list[str]:
    """六命图标一律从地图取；是否点亮只看已解锁数量。"""
    keys = [char_id]
    suffix = element.lower()
    if suffix:
        keys.append(f"{char_id}-{suffix}")
    for key in keys:
        if key not in mapping:
            continue
        mapped = mapping[key]
        return [mapped[i] if i < len(mapped) else "" for i in range(6)]
    return [""] * 6
