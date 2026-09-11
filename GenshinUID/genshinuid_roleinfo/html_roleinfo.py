from __future__ import annotations

import html
import math
import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from gsuid_core.pool import to_thread
from gsuid_core.utils.html_render import _ensure_renderer, render_html_to_bytes
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.mys.models import Stats, Offering, IndexData, MihoyoAvatar, WorldExploration
from gsuid_core.utils.download_resource.download_image import get_image

from .char_score import CHAR_SCORE_FLOOR, char_total_score
from ..utils.colors import get_color
from .draw_all_char import (
    TEXT_PATH as CHAR_TEXT,
    CHAR_DIV_Y,
    CHAR_GAP_X,
    CHAR_CARD_H,
    _char_grid_metrics,
)
from ..utils.image.image_tools import TEXT_PATH as IMG_TEXT, get_v4_bg, shift_image_hue
from ..utils.fonts.genshin_fonts import FONT_ORIGIN_PATH
from ..genshinuid_collection.const import max_data, expmax_data
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    ICON_PATH,
    WEAPON_PATH,
    HG_ICON_PATH,
    MZ_ICON_PATH,
    CHAR_NAMECARDPIC_PATH,
)
from ..genshinuid_collection.draw_collection_card import TEXT_PATH as COLLECT_TEXT
from ..genshinuid_collection.draw_new_collection_card import CMAP, DMAP, STCMAP

WorldPacked = list[list[tuple[WorldExploration, list[WorldExploration], int]]]

CHAR_SIDE_MIN = 21
SIDE_CHAR_COLS = 6
TITLE_TO_EXPLORE_Y = 650
TITLE_W = 1680
TITLE_H = 700
AVATAR_SIZE = 377
FOOTER_W = 1100
FOOTER_H = 40
FOOTER_PAD = 20

EXPLORE_W = 1680
EXPLORE_LINE = 390
EXPLORE_TITLE_OFFER = 50
EXPLORE_DIV_H = 70
EXPLORE_FOOT = 80
EXPLORE_SECTION_GAP = 80
EXPLORE_COLS = 6
EXPLORE_CARD_STEP = 255
EXPLORE_CARD_W = 300
EXPLORE_CARD_H = 450
EXPLORE_OFFER_X = 52

# 地区探索：变高两列卡。上栏地区图，下栏大图标+条+供奉/子区域
WORLD_COLS = 2
WORLD_ROW_GAP = 20
WORLD_PAD_LEFT = 65
WORLD_PAD_RIGHT = 62
WORLD_GAP_X = 12
WORLD_PAD_Y = 32
WORLD_COL_W = (EXPLORE_W - WORLD_PAD_LEFT - WORLD_PAD_RIGHT - WORLD_GAP_X * (WORLD_COLS - 1)) // WORLD_COLS
WORLD_PAD = 14
WORLD_GAP = 16
WORLD_ICON = 70
WORLD_ICON_X = 36
WORLD_TEXT_X = 36
WORLD_TITLE_H = 20
WORLD_TITLE_GAP = 4
WORLD_HEAD_PAD = 24
WORLD_HEAD_H = 88
WORLD_BODY_H = 88
WORLD_REP_W = 96
WORLD_PCT_W = 78
WORLD_BAR_X = 168
WORLD_BAR_H = 22
WORLD_BAR_W = WORLD_COL_W - WORLD_BAR_X - WORLD_PCT_W - 16
WORLD_SUB_LABEL_W = 122
WORLD_SUB_BAR_X = WORLD_BAR_X + WORLD_SUB_LABEL_W + 8
WORLD_SUB_BAR_W = WORLD_COL_W - WORLD_SUB_BAR_X - WORLD_PCT_W - 16
WORLD_CARD_PAD_BOT = 14
WORLD_SUB_ICON = 28
WORLD_TIP_W = 3
WORLD_TIP_OVER = 6
WORLD_TIP_CAP = 10
WORLD_TIP_CAP_H = 3
WORLD_TIP_OL = 2
WORLD_BADGE_H = 32
WORLD_OFFER_ICON = 26
WORLD_OFFER_COLS = 2
WORLD_OFFER_ROW = 40
WORLD_OFFER_PAD = 12
WORLD_OFFER_GAP = 20
WORLD_CHIP_W = (WORLD_BAR_W - WORLD_OFFER_GAP) // WORLD_OFFER_COLS - 14
WORLD_PCT_X = WORLD_COL_W - WORLD_HEAD_PAD
WORLD_REP_BAR_W = 72
WORLD_SUB_H = 40
WORLD_SUB_BAR_H = 16
WORLD_SUB_PAD = 8
WORLD_BADGE_FG = "#10141c"
WORLD_OFFER_BG = "rgba(255,255,255,0.10)"
WORLD_OFFER_FG = "#ffffff"
WORLD_OFFER_EDGE = "rgba(255,255,255,0.22)"
WORLD_I_DARK = "#0b1018"
WORLD_TRACK_BG = "#0b1018"
WORLD_HEAD_DEFAULT = "#243044"
WORLD_ACCENT_DEFAULT = "#5b8def"
WORLD_BG_DIR = Path(__file__).parent / "texture2d" / "world_bg"

_HEADER_BG: dict[str, str] = {
    "蒙德": "#0e3a3e",
    "璃月": "#3d2a10",
    "龙脊雪山": "#0e3a3e",
    "稻妻": "#2a1548",
    "渊下宫": "#221448",
    "层岩巨渊": "#3d2a10",
    "地下矿区": "#3d2a10",
    "须弥": "#0e3824",
    "枫丹": "#0e3848",
    "沉玉谷": "#3d2a10",
    "来歆山": "#3d2a10",
    "南陵": "#3d2a10",
    "上谷": "#3d2a10",
    "纳塔": "#3a1210",
    "挪德卡莱": "#1a3048",
    "至冬": "#163048",
    "空之神殿": "#1a1840",
    "远古圣山": "#3a1210",
    "风息山": "#0e3a3e",
    "旧日之海": "#0e3848",
}
_HEADER_ACCENT: dict[str, str] = {
    "蒙德": "#2fd0d4",
    "璃月": "#e8a428",
    "龙脊雪山": "#2fd0d4",
    "稻妻": "#b06ae8",
    "渊下宫": "#9a6ae0",
    "层岩巨渊": "#e8a428",
    "地下矿区": "#e8a428",
    "须弥": "#6ee09a",
    "枫丹": "#3cc4e0",
    "沉玉谷": "#e8a428",
    "来歆山": "#e8a428",
    "南陵": "#e8a428",
    "上谷": "#e8a428",
    "纳塔": "#e03830",
    "挪德卡莱": "#8ec8f0",
    "至冬": "#9ed8f5",
    "空之神殿": "#5a62c8",
    "远古圣山": "#e03830",
    "风息山": "#2fd0d4",
    "旧日之海": "#3cc4e0",
}

CHAR_NATIVE_W = 624
CHAR_NATIVE_H = 325
CHAR_ICON_SIZE = 256
WEAPON_ICON_SIZE = 174
WEAPON_BG_SIZE = 220
NAMECARD_W = 560
NAMECARD_H = 268
TALENT_W = 72
TALENT_H = 73
FETTER_W = 71
FETTER_H = 61

HALF_WHITE = "rgba(255,255,255,0.47)"
WHITE = "#ffffff"
BLACK = "rgb(2,2,2)"
FONT_CSS = "'YuanShen','MiSans',sans-serif"

_WORLD_ICON_FIX: dict[str, str] = {
    "远古圣山": "https://webstatic.mihoyo.com/app/community-game-records/images/world-logo-16.1c751ac9.png",
    "挪德卡莱": "https://webstatic.mihoyo.com/app/community-game-records/images/world-logo-17.dadac5bf.png",
    "风息山": "https://webstatic.mihoyo.com/app/community-game-records/images/world-logo-1.20b81b5f.png",
    "空之神殿": "https://webstatic.mihoyo.com/app/community-game-records/images/world-logo-19.a9df3078.png",
}

_WORLD_BG_FILE: dict[str, str] = {
    "蒙德": "MengDe.png",
    "璃月": "Liyue.png",
    "稻妻": "Daoqi.png",
    "须弥": "Xumi.png",
    "枫丹": "FengDan.png",
    "纳塔": "Nata.png",
    "挪德卡莱": "Nodekalai.png",
    "至冬": "ZhiDong.png",
    "空之神殿": "KongZhiShenDian.png",
}

# 官方战绩把子区域归进大国；API 的 parent_id 并不完整
_NEST_UNDER: dict[str, str] = {
    "龙脊雪山": "蒙德",
    "风息山": "蒙德",
    "层岩巨渊": "璃月",
    "层岩巨渊·地下矿区": "璃月",
    "沉玉谷": "璃月",
    "沉玉谷·南陵": "璃月",
    "沉玉谷·上谷": "璃月",
    "来歆山": "璃月",
    "渊下宫": "稻妻",
    "旧日之海": "枫丹",
    "远古圣山": "纳塔",
}

_LEVEL_MAX: dict[str, int] = {
    "甘露池": 10,
    "煅石之火": 40,
    "祀珑典仪": 10,
    "摹忆中枢": 9,
    "空之神殿·摹忆中枢": 9,
    "露景泉": 30,
    "纳塔": 10,
    "挪德卡莱": 10,
    "至冬": 10,
    "空之神殿": 9,
    "神像": 10,
}

_CHILD_RANK: dict[str, int] = {
    "层岩巨渊": 0,
    "层岩巨渊·地下矿区": 1,
    "沉玉谷·南陵": 2,
    "沉玉谷·上谷": 3,
    "来歆山": 4,
    "龙脊雪山": 0,
    "风息山": 1,
    "渊下宫": 0,
    "旧日之海": 0,
    "远古圣山": 0,
}

_CHEST_ORDER: tuple[str, ...] = (
    "普通的宝箱",
    "精致的宝箱",
    "珍贵的宝箱",
    "华丽的宝箱",
    "奇馈宝箱",
)

_URI: dict[str, str] = {}
_YS_READY = False


def _ensure_ys_font() -> None:
    global _YS_READY
    if _YS_READY:
        return
    _ensure_renderer(force=True, extra_fonts=[(FONT_ORIGIN_PATH.read_bytes(), "YuanShen")])
    _YS_READY = True


def _png_uri(img: Image.Image) -> str:
    buf = BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def _jpeg_uri(img: Image.Image, quality: int = 82) -> str:
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def _file_uri(path: Path) -> str:
    key = f"file:{path}"
    if key in _URI:
        return _URI[key]
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif suffix == ".webp":
        mime = "image/webp"
    uri = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    _URI[key] = uri
    return uri


def _path_png_uri(path: Path, size: tuple[int, int] | None = None) -> str:
    if not path.exists():
        return ""
    if size is None:
        return _file_uri(path)
    key = f"resize:{path}:{size[0]}x{size[1]}"
    if key in _URI:
        return _URI[key]
    img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


def _cmap_steps(name: str) -> list[int]:
    if name in CMAP:
        return list(CMAP[name])
    return [10, 8, 6, 4, 2]


def _level_cap(name: str) -> int:
    if name in _LEVEL_MAX:
        return _LEVEL_MAX[name]
    if name in CMAP and CMAP[name][0] > 0:
        return CMAP[name][0]
    short = name.split("·")[-1] if "·" in name else name
    if short in _LEVEL_MAX:
        return _LEVEL_MAX[short]
    if short in CMAP and CMAP[short][0] > 0:
        return CMAP[short][0]
    if name.startswith("聚所") or short.startswith("聚所"):
        return 5
    return 0


def _is_maxed(name: str, level: int) -> bool:
    cap = _level_cap(name)
    return cap > 0 and level >= cap


def _dmap_shift(name: str) -> int:
    if name in DMAP:
        return DMAP[name]
    return 5


def _css_rgb(color: tuple[int, int, int]) -> str:
    return f"rgb({color[0]},{color[1]},{color[2]})"


def _world_statue(world: WorldExploration) -> int:
    if "seven_statue_level" in world:
        return world["seven_statue_level"]
    return 0


def _world_icon_url(world: WorldExploration) -> str:
    name = world["name"]
    if name in _WORLD_ICON_FIX:
        return _WORLD_ICON_FIX[name]
    return world["icon"]


def _top_parent_name(world: WorldExploration, by_id: dict[int, WorldExploration]) -> str:
    name = world["name"]
    if name in _NEST_UNDER:
        return _NEST_UNDER[name]
    pid = world["parent_id"]
    if pid != 0 and pid in by_id:
        parent = by_id[pid]
        top = _top_parent_name(parent, by_id)
        if top != parent["name"]:
            return top
        if parent["name"] in _NEST_UNDER:
            return _NEST_UNDER[parent["name"]]
        return parent["name"]
    return name


def _group_worlds(worlds: list[WorldExploration]) -> list[tuple[WorldExploration, list[WorldExploration]]]:
    by_id = {w["id"]: w for w in worlds}
    by_name = {w["name"]: w for w in worlds}
    nested: set[int] = set()
    children_map: dict[int, list[WorldExploration]] = {}
    for world in worlds:
        top = _top_parent_name(world, by_id)
        if top == world["name"] or top not in by_name:
            continue
        parent = by_name[top]
        if parent["id"] not in children_map:
            children_map[parent["id"]] = []
        children_map[parent["id"]].append(world)
        nested.add(world["id"])
    groups: list[tuple[WorldExploration, list[WorldExploration]]] = []
    for world in worlds:
        if world["id"] in nested:
            continue
        kids = children_map[world["id"]] if world["id"] in children_map else []
        kids = sorted(
            kids,
            key=lambda w: _CHILD_RANK[w["name"]] if w["name"] in _CHILD_RANK else w["id"],
        )
        groups.append((world, kids))
    return groups


def _merged_offers(world: WorldExploration, children: list[WorldExploration]) -> list[Offering]:
    seen: set[str] = set()
    out: list[Offering] = []
    for src in (world, *children):
        for offer in src["offerings"]:
            if offer["name"] in seen:
                continue
            seen.add(offer["name"])
            out.append(offer)
    return out


def _offer_grid(n: int) -> tuple[int, int]:
    if n <= 0:
        return 0, WORLD_CHIP_W
    rows = (n + WORLD_OFFER_COLS - 1) // WORLD_OFFER_COLS
    return rows, WORLD_CHIP_W


def _visible_children(children: list[WorldExploration]) -> list[WorldExploration]:
    return [child for child in children if child["exploration_percentage"] > 0]


def _rep_label(world: WorldExploration, merged: list[Offering]) -> tuple[str, int] | None:
    level = world["level"]
    if level <= 0:
        return None
    if world["type"] == "Reputation":
        return "声望", level
    if world["type"] == "Offering" and not merged:
        return "等阶", level
    return None


def _left_block_h(has_rep: bool) -> int:
    h = WORLD_ICON + WORLD_TITLE_GAP + WORLD_TITLE_H
    if has_rep:
        h += WORLD_GAP + WORLD_BADGE_H
    return h


def _world_frame(
    world: WorldExploration,
    children: list[WorldExploration],
) -> tuple[int, int, int, int, int, int, list[Offering], list[WorldExploration]]:
    merged = _merged_offers(world, children)
    vis = _visible_children(children)
    n_badge, _cell_w = _offer_grid(len(merged))
    if n_badge == 0 and _world_statue(world) > 0:
        n_badge = 1
    has_rep = _rep_label(world, merged) is not None
    rel_after = WORLD_BAR_H + WORLD_GAP
    rel_sub_y = rel_after
    rel_last = WORLD_BAR_H
    if vis:
        rel_last = rel_sub_y + len(vis) * WORLD_SUB_H
    if n_badge > 0:
        rel_offer_y = (rel_last + WORLD_GAP) if vis else rel_after
        rel_last = rel_offer_y + (n_badge - 1) * WORLD_OFFER_ROW + WORLD_BADGE_H
    else:
        rel_offer_y = rel_after
    tip = WORLD_TIP_OVER + WORLD_TIP_OL
    rel_y = tip + rel_last
    left_h = _left_block_h(has_rep)
    inner_h = max(rel_y, left_h) + WORLD_PAD * 2
    right_y0 = (inner_h - rel_y) // 2
    bar_y0 = right_y0 + tip
    if left_h < rel_last and rel_last - left_h < WORLD_SUB_H * 2:
        icon_y = bar_y0
    else:
        icon_y = (inner_h - left_h) // 2
    bar_y = bar_y0
    sub_y = bar_y0 + rel_sub_y
    offer_y = bar_y0 + rel_offer_y
    title_top = icon_y + WORLD_ICON + WORLD_TITLE_GAP
    return inner_h, icon_y, title_top, bar_y, offer_y, sub_y, merged, vis


def _world_card_inner_h(world: WorldExploration, children: list[WorldExploration]) -> int:
    return _world_frame(world, children)[0]


def _pack_world_cols(
    groups: list[tuple[WorldExploration, list[WorldExploration]]],
) -> list[list[tuple[WorldExploration, list[WorldExploration], int]]]:
    cols: list[list[tuple[WorldExploration, list[WorldExploration], int]]] = [[] for _ in range(WORLD_COLS)]
    heights = [0] * WORLD_COLS
    for world, children in groups:
        card_h = _world_card_inner_h(world, children)
        ci = 0
        for i in range(1, WORLD_COLS):
            if heights[i] < heights[ci]:
                ci = i
        cols[ci].append((world, children, card_h))
        heights[ci] += card_h + WORLD_ROW_GAP
    return cols


def _world_block_height(
    cols: list[list[tuple[WorldExploration, list[WorldExploration], int]]],
) -> int:
    tallest = 0
    for col in cols:
        h = WORLD_PAD_Y
        for _world, _children, card_h in col:
            h += card_h + WORLD_ROW_GAP
        if col:
            h += WORLD_PAD_Y - WORLD_ROW_GAP
        if h > tallest:
            tallest = h
    if tallest <= 0:
        return WORLD_PAD_Y
    return tallest


def _explore_height(culus_n: int, world_block_h: int) -> int:
    culus_rows = ((culus_n - 1) // EXPLORE_COLS) + 1
    return (
        EXPLORE_LINE * (culus_rows + 1)
        + world_block_h
        + EXPLORE_TITLE_OFFER
        + EXPLORE_DIV_H * 3
        + EXPLORE_SECTION_GAP * 2
        + EXPLORE_FOOT
    )


def _culus_pairs(stats: Stats) -> list[tuple[str, int]]:
    pairs: list[tuple[str, int]] = []
    for key, value in dict(stats).items():
        if key.endswith("culus_number") and isinstance(value, int):
            pairs.append((key, value))
    return pairs


def _world_short_name(name: str) -> str:
    if "·" in name:
        return name.split("·")[-1]
    return name


def _abs_img(src: str, left: int, top: int, width: int, height: int) -> str:
    if not src:
        return ""
    return f'<img src="{src}" style="position:absolute;left:{left}px;top:{top}px;width:{width}px;height:{height}px"/>'


def _label(
    text: str,
    x: int,
    y: int,
    size: int,
    box_w: int,
    *,
    align: str = "center",
    color: str = WHITE,
) -> str:
    top = y - size // 2
    if align == "center":
        left = x - box_w // 2
        jc = "center"
    elif align == "right":
        left = x - box_w
        jc = "flex-end"
    else:
        left = x
        jc = "flex-start"
    return (
        f'<div style="position:absolute;left:{left}px;top:{top}px;width:{box_w}px;height:{size}px;'
        f"display:flex;align-items:center;justify-content:{jc};color:{color};"
        f"font-size:{size}px;font-family:{FONT_CSS};line-height:1;white-space:nowrap;"
        f'overflow:hidden">'
        f"{html.escape(text)}</div>"
    )


def _pill(
    left: int,
    top: int,
    width: int,
    height: int,
    bg: str,
    text: str,
    size: int,
    radius: int,
    color: str = WHITE,
) -> str:
    return (
        f'<div style="position:absolute;left:{left}px;top:{top}px;width:{width}px;height:{height}px;'
        f"border-radius:{radius}px;background:{bg};display:flex;align-items:center;"
        f"justify-content:center;color:{color};font-size:{size}px;font-family:{FONT_CSS};"
        f'line-height:1">{html.escape(text)}</div>'
    )


def _rect_badge(
    left: int,
    top: int,
    width: int,
    height: int,
    bg: str,
    text: str,
    *,
    size: int = 15,
    color: str = WHITE,
    icon_uri: str = "",
    icon: int = 22,
    align: str = "center",
) -> str:
    icon_html = ""
    if icon_uri:
        icon_html = (
            f'<img src="{icon_uri}" style="width:{icon}px;height:{icon}px;flex:none;margin-right:6px;display:block"/>'
        )
    jc = "flex-start" if align == "left" else "center"
    return (
        f'<div style="position:absolute;left:{left}px;top:{top}px;width:{width}px;height:{height}px;'
        f"background:{bg};display:flex;align-items:center;justify-content:{jc};"
        f"color:{color};font-size:{size}px;font-family:{FONT_CSS};line-height:1;"
        f'white-space:nowrap;overflow:hidden">'
        f"{icon_html}{html.escape(text)}</div>"
    )


def _i_rect(left: int, top: int, width: int, height: int, color: str) -> str:
    return (
        f'<div style="position:absolute;left:{left}px;top:{top}px;'
        f'width:{width}px;height:{height}px;background:{color}"></div>'
    )


def _bar_i_html(cx: int, bar_top: int, bar_h: int) -> str:
    over = WORLD_TIP_OVER
    stem_w = WORLD_TIP_W
    cap_w = WORLD_TIP_CAP
    cap_h = WORLD_TIP_CAP_H
    ol = WORLD_TIP_OL
    stem_h = bar_h + over * 2
    stem_left = cx - stem_w // 2
    stem_top = bar_top - over
    cap_left = cx - cap_w // 2
    cap_bot = stem_top + stem_h - cap_h
    dark = WORLD_I_DARK
    white = "#ffffff"
    return (
        _i_rect(stem_left - ol, stem_top - ol, stem_w + ol * 2, stem_h + ol * 2, dark)
        + _i_rect(cap_left - ol, stem_top - ol, cap_w + ol * 2, cap_h + ol * 2, dark)
        + _i_rect(cap_left - ol, cap_bot - ol, cap_w + ol * 2, cap_h + ol * 2, dark)
        + _i_rect(stem_left, stem_top, stem_w, stem_h, white)
        + _i_rect(cap_left, stem_top, cap_w, cap_h, white)
        + _i_rect(cap_left, cap_bot, cap_w, cap_h, white)
    )


async def _area_bg_uri(shift: int) -> str:
    key = f"areabg:{shift}"
    if key in _URI:
        return _URI[key]
    img = Image.open(COLLECT_TEXT / "area_bg.png").convert("RGBA")
    img = await shift_image_hue(img, shift)
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


def _namecard_uri(char_id: int) -> str:
    key = f"namecard:{char_id}"
    if key in _URI:
        return _URI[key]
    path = CHAR_NAMECARDPIC_PATH / f"{char_id}.png"
    if not path.exists():
        _URI[key] = ""
        return ""
    card = Image.open(path).convert("RGBA").resize((NAMECARD_W, NAMECARD_H), Image.Resampling.LANCZOS)
    mask = Image.open(CHAR_TEXT / "charcard_mask.png").convert("L")
    if mask.size != (NAMECARD_W, NAMECARD_H):
        mask = mask.resize((NAMECARD_W, NAMECARD_H), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (NAMECARD_W, NAMECARD_H), (0, 0, 0, 0))
    out.paste(card, (0, 0), mask)
    uri = _png_uri(out)
    _URI[key] = uri
    return uri


def _blank_uri(size: tuple[int, int]) -> str:
    key = f"blank:{size[0]}x{size[1]}"
    if key in _URI:
        return _URI[key]
    uri = _png_uri(Image.new("RGBA", size, (0, 0, 0, 0)))
    _URI[key] = uri
    return uri


async def _icon_uri(url: str, size: tuple[int, int]) -> str:
    if not url:
        return _blank_uri(size)
    key = f"icon:{url}:{size[0]}x{size[1]}"
    if key in _URI:
        return _URI[key]
    img = await get_image(url, ICON_PATH, size=size)
    img = img.convert("RGBA")
    extrema = img.getextrema()
    if len(extrema) >= 4 and extrema[3][1] == 0:
        _URI[key] = ""
        return ""
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


async def _offer_icon_uri(offer: Offering) -> str:
    if not offer["icon"]:
        return ""
    return await _icon_uri(offer["icon"], (WORLD_OFFER_ICON, WORLD_OFFER_ICON))


@to_thread
def _encode_bg_jpeg(w: int, h: int) -> str:
    return _jpeg_uri(get_v4_bg(w, h))


async def _bg_jpeg_uri(w: int, h: int) -> str:
    key = f"bg:{w}x{h}"
    if key in _URI:
        return _URI[key]
    uri = await _encode_bg_jpeg(w, h)
    _URI[key] = uri
    return uri


async def _area_card_html(
    *,
    icon_uri: str,
    icon_pos: tuple[int, int],
    icon_size: tuple[int, int],
    percent: float,
    sub_text: str,
    com_text: str,
    name: str,
    level: int,
    level_name: str,
    offerings: list[Offering],
    offer: int,
    left: int,
    top: int,
) -> str:
    shift = _dmap_shift(name)
    bg_uri = await _area_bg_uri(shift)
    main_color = _css_rgb(get_color(level, _cmap_steps(name)))
    completion = f"{com_text}: {percent:.1f}%"
    fill_w = min(182, max(0, round(percent * 1820 / 1000)))
    ix, iy = icon_pos
    iw, ih = icon_size
    parts: list[str] = [
        f'<div style="position:absolute;left:{left}px;top:{top}px;width:{EXPLORE_CARD_W}px;height:{EXPLORE_CARD_H}px">',
        _abs_img(bg_uri, 0, 0, EXPLORE_CARD_W, EXPLORE_CARD_H),
        _abs_img(icon_uri, ix, iy, iw, ih),
        _label(name, 150, 216 + offer, 32, 280),
        _pill(98, 240 + offer, 103, 30, main_color, level_name, 24, 20),
        (
            f'<div style="position:absolute;left:59px;top:{283 + offer}px;width:182px;height:12px;'
            f'border-radius:20px;background:{HALF_WHITE}">'
            f'<div style="width:{fill_w}px;height:12px;border-radius:20px;background:{WHITE}"></div>'
            f"</div>"
        ),
        _label(completion, 150, 320 + offer, 20, 260),
    ]
    if sub_text:
        parts.append(_label(sub_text, 150, 350 + offer, 20, 260))
    if offerings:
        odata = offerings[0]
        oicon = await _icon_uri(odata["icon"], (38, 38))
        oname = odata["name"]
        orank = f"等阶{odata['level']}"
        sub_color = _css_rgb(get_color(odata["level"], _cmap_steps(oname)))
        parts.append(
            f'<div style="position:absolute;left:59px;top:{340 + offer}px;width:182px;height:47px;'
            f'border-radius:5px;background:{HALF_WHITE}"></div>'
        )
        parts.append(_abs_img(oicon, 63, 343 + offer, 38, 38))
        parts.append(_label(oname, 107, 352 + offer, 20, 130, align="left", color=BLACK))
        parts.append(_pill(107, 364 + offer, 66, 20, sub_color, orank, 15, 20))
    parts.append("</div>")
    return "".join(parts)


def _clip_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _offer_short(name: str) -> str:
    short = name.split("·")[-1] if "·" in name else name
    return _clip_text(short, 6)


def _header_bg(name: str) -> str:
    if name in _HEADER_BG:
        return _HEADER_BG[name]
    return WORLD_HEAD_DEFAULT


def _header_accent(name: str) -> str:
    if name in _HEADER_ACCENT:
        return _HEADER_ACCENT[name]
    return WORLD_ACCENT_DEFAULT


def _hex_rgb(color: str) -> tuple[int, int, int]:
    h = color[1:] if color.startswith("#") else color
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _card_art_uri(name: str, height: int) -> str:
    if name not in _WORLD_BG_FILE:
        return ""
    path = WORLD_BG_DIR / _WORLD_BG_FILE[name]
    if not path.exists():
        return ""
    key = f"worldbg:{name}:{WORLD_COL_W}x{height}"
    if key in _URI:
        return _URI[key]
    src = Image.open(path).convert("RGBA")
    iw, ih = src.size
    scale = max(WORLD_COL_W / iw, height / ih)
    nw, nh = max(1, round(iw * scale)), max(1, round(ih * scale))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, nw - WORLD_COL_W)
    top = max(0, (nh - height) // 2)
    crop = resized.crop((left, top, left + WORLD_COL_W, top + height))
    crop = Image.alpha_composite(crop, Image.new("RGBA", (WORLD_COL_W, height), (8, 12, 20, 40)))
    vfade = Image.new("RGBA", (1, height), (0, 0, 0, 0))
    vpx = vfade.load()
    for y in range(height):
        t = y / max(1, height - 1)
        vpx[0, y] = (6, 10, 18, round(36 + 150 * (t**1.05)))
    crop = Image.alpha_composite(crop, vfade.resize((WORLD_COL_W, height), Image.Resampling.BILINEAR))
    hfade = Image.new("RGBA", (WORLD_COL_W, 1), (0, 0, 0, 0))
    hpx = hfade.load()
    span = max(1, int(WORLD_COL_W * 0.42))
    for x in range(WORLD_COL_W):
        alpha = 0 if x >= span else round(110 * (1 - x / span))
        hpx[x, 0] = (6, 10, 18, alpha)
    crop = Image.alpha_composite(crop, hfade.resize((WORLD_COL_W, height), Image.Resampling.BILINEAR))
    uri = _png_uri(crop)
    _URI[key] = uri
    return uri


def _lighten_hex(color: str, factor: float) -> str:
    r, g, b = _hex_rgb(color)
    return f"rgb({round(r + (255 - r) * factor)},{round(g + (255 - g) * factor)},{round(b + (255 - b) * factor)})"


def _pct_fill_css(accent: str) -> str:
    return f"linear-gradient(90deg,{_mix_hex(accent, 0.42)} 0%,{accent} 55%,{_lighten_hex(accent, 0.55)} 100%)"


def _flat_bar_html(left: int, top: int, width: int, height: int, fill_w: int, fill_css: str) -> str:
    parts: list[str] = [
        (
            f'<div style="position:absolute;left:{left}px;top:{top}px;width:{width}px;height:{height}px;'
            f'background:{WORLD_TRACK_BG}">'
        )
    ]
    if fill_w > 0:
        parts.append(
            f'<div style="position:absolute;left:0;top:0;width:{fill_w}px;height:{height}px;'
            f'background:{fill_css}"></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def _progress_row_html(
    bar_x: int,
    bar_y: int,
    bar_h: int,
    percent: float,
    accent: str,
    pct_size: int = 18,
    *,
    bar_w: int | None = None,
) -> str:
    width = WORLD_BAR_W if bar_w is None else bar_w
    fill = _pct_fill_css(accent)
    fill_w = min(width, max(0, round(percent * width / 100)))
    parts = [
        _flat_bar_html(bar_x, bar_y, width, bar_h, fill_w, fill),
        _label(f"{percent:.1f}%", WORLD_PCT_X, bar_y + bar_h // 2, pct_size, WORLD_PCT_W, align="right"),
    ]
    if fill_w > 0:
        parts.append(_bar_i_html(bar_x + fill_w, bar_y, bar_h))
    return "".join(parts)


def _mix_hex(color: str, factor: float) -> str:
    r, g, b = _hex_rgb(color)
    return f"rgb({round(r * factor)},{round(g * factor)},{round(b * factor)})"


def _accent_fill_css(accent: str, maxed: bool) -> str:
    return _mix_hex(accent, 0.52 if maxed else 0.38)


async def _offer_badge_html(
    left: int,
    top: int,
    offer: Offering,
    *,
    width: int,
    accent: str,
    fallback_icon: str,
) -> str:
    name = _offer_short(offer["name"])
    level = offer["level"]
    cap = _level_cap(offer["name"])
    maxed = cap > 0 and level >= cap
    ratio = min(1.0, level / cap) if cap > 0 else 0.0
    if cap > 0:
        left_text = f"{name} 等级{level}"
        right_text = f"{round(ratio * 100)}%"
    else:
        left_text = name
        right_text = f"等级{level}"
    icon_uri = await _offer_icon_uri(offer)
    if not icon_uri:
        icon_uri = fallback_icon
    track = _mix_hex(accent, 0.18)
    fill_w = min(width - 2, max(0, round((width - 2) * ratio))) if cap > 0 else 0
    cy = top + WORLD_BADGE_H // 2
    parts = [
        _i_rect(left, top, width, WORLD_BADGE_H, _mix_hex(accent, 0.42)),
        _i_rect(left + 1, top + 1, width - 2, WORLD_BADGE_H - 2, track),
    ]
    if fill_w > 0:
        parts.append(
            f'<div style="position:absolute;left:{left + 1}px;top:{top + 1}px;'
            f"width:{fill_w}px;height:{WORLD_BADGE_H - 2}px;"
            f'background:{_accent_fill_css(accent, maxed)}"></div>'
        )
    tx = left + 8
    if icon_uri:
        iy = top + (WORLD_BADGE_H - WORLD_OFFER_ICON) // 2
        parts.append(_abs_img(icon_uri, tx, iy, WORLD_OFFER_ICON, WORLD_OFFER_ICON))
        tx += WORLD_OFFER_ICON + 6
    right_box = 64
    tw = max(40, width - (tx - left) - right_box - 8)
    parts.append(_label(left_text, tx, cy, 15, tw, align="left", color=WHITE))
    parts.append(_label(right_text, left + width - 8, cy, 15, right_box, align="right", color=WHITE))
    return "".join(parts)


def _rep_badge_html(left: int, top: int, width: int, accent: str, kind: str, level: int, cap_name: str) -> str:
    cap = _level_cap(cap_name)
    maxed = cap > 0 and level >= cap
    ratio = min(1.0, level / cap) if cap > 0 else 0.0
    track = _mix_hex(accent, 0.18)
    fill_w = min(width - 2, max(0, round((width - 2) * ratio))) if cap > 0 else 0
    cy = top + WORLD_BADGE_H // 2
    parts = [
        _i_rect(left, top, width, WORLD_BADGE_H, _mix_hex(accent, 0.42)),
        _i_rect(left + 1, top + 1, width - 2, WORLD_BADGE_H - 2, track),
    ]
    if fill_w > 0:
        parts.append(
            f'<div style="position:absolute;left:{left + 1}px;top:{top + 1}px;'
            f"width:{fill_w}px;height:{WORLD_BADGE_H - 2}px;"
            f'background:{_accent_fill_css(accent, maxed)}"></div>'
        )
    parts.append(_label(f"{kind}{level}", left + width // 2, cy, 14, width, align="center", color=WHITE))
    return "".join(parts)


async def _world_card_html(
    world: WorldExploration,
    children: list[WorldExploration],
    left: int,
    top: int,
    inner_h: int,
) -> str:
    name = _world_short_name(world["name"])
    percent = world["exploration_percentage"] / 10
    (
        _h,
        icon_y,
        title_top,
        bar_y,
        offer_y,
        sub_y,
        merged,
        vis_children,
    ) = _world_frame(world, children)
    icon_uri = await _icon_uri(_world_icon_url(world), (WORLD_ICON, WORLD_ICON))
    art_uri = _card_art_uri(name, inner_h)
    head_bg = _header_bg(name)
    accent = _header_accent(name)
    name_w = max(len(name) * WORLD_TITLE_H + 8, WORLD_ICON)
    offer_icon_fb = await _icon_uri(_world_icon_url(world), (WORLD_OFFER_ICON, WORLD_OFFER_ICON))
    parts: list[str] = [
        (
            f'<div style="position:absolute;left:{left}px;top:{top}px;'
            f"width:{WORLD_COL_W}px;height:{inner_h}px;border-radius:8px;"
            f'background:{head_bg};overflow:hidden">'
        ),
    ]
    if art_uri:
        parts.append(_abs_img(art_uri, 0, 0, WORLD_COL_W, inner_h))
    parts.append(f'<div style="position:absolute;left:0;top:0;width:4px;height:{inner_h}px;background:{accent}"></div>')
    parts.append(_abs_img(icon_uri, WORLD_ICON_X, icon_y, WORLD_ICON, WORLD_ICON))
    parts.append(
        _label(
            name,
            WORLD_ICON_X + WORLD_ICON // 2,
            title_top + WORLD_TITLE_H // 2,
            WORLD_TITLE_H,
            name_w,
            align="center",
        )
    )
    parts.append(_progress_row_html(WORLD_BAR_X, bar_y, WORLD_BAR_H, percent, accent))
    rep = _rep_label(world, merged)
    if rep is not None:
        kind, rep_lv = rep
        rep_left = WORLD_ICON_X + (WORLD_ICON - WORLD_REP_BAR_W) // 2
        rep_top = title_top + WORLD_TITLE_H + WORLD_GAP
        parts.append(
            _rep_badge_html(
                rep_left,
                rep_top,
                WORLD_REP_BAR_W,
                accent,
                kind,
                rep_lv,
                name,
            )
        )

    if merged:
        rows, cell_w = _offer_grid(len(merged))
        for i, offer in enumerate(merged):
            ox = WORLD_BAR_X + (i % WORLD_OFFER_COLS) * (cell_w + WORLD_OFFER_GAP)
            oy = offer_y + (i // WORLD_OFFER_COLS) * WORLD_OFFER_ROW
            parts.append(
                await _offer_badge_html(
                    ox,
                    oy,
                    offer,
                    width=cell_w,
                    accent=accent,
                    fallback_icon=offer_icon_fb,
                )
            )
    statue = _world_statue(world)
    if statue > 0:
        rows, _cell_w = _offer_grid(len(merged))
        last_y = offer_y if rows <= 1 else offer_y + (rows - 1) * WORLD_OFFER_ROW
        parts.append(
            _rep_badge_html(
                WORLD_PCT_X - WORLD_REP_BAR_W,
                last_y,
                WORLD_REP_BAR_W,
                accent,
                "神像",
                statue,
                "神像",
            )
        )

    if vis_children:
        y = sub_y
        for child in vis_children:
            cy = y + (WORLD_SUB_H - WORLD_SUB_BAR_H) // 2
            cname = child["name"] if child["name"].startswith("沉玉谷·") else _world_short_name(child["name"])
            child_icon = await _icon_uri(_world_icon_url(child), (WORLD_SUB_ICON, WORLD_SUB_ICON))
            iy = y + (WORLD_SUB_H - WORLD_SUB_ICON) // 2
            parts.append(_abs_img(child_icon, WORLD_BAR_X, iy, WORLD_SUB_ICON, WORLD_SUB_ICON))
            nx = WORLD_BAR_X + WORLD_SUB_ICON + 6
            cw = WORLD_SUB_LABEL_W - WORLD_SUB_ICON - 6
            parts.append(_label(cname, nx, y + WORLD_SUB_H // 2, 14, cw, align="left"))
            child_accent = _header_accent(_world_short_name(child["name"]))
            parts.append(
                _progress_row_html(
                    WORLD_SUB_BAR_X,
                    cy,
                    WORLD_SUB_BAR_H,
                    child["exploration_percentage"] / 10,
                    child_accent,
                    16,
                    bar_w=WORLD_SUB_BAR_W,
                )
            )
            y += WORLD_SUB_H

    parts.append("</div>")
    return "".join(parts)


def _char_star(char: MihoyoAvatar) -> int:
    star = int(char["rarity"])
    if star in (4, 5):
        return star
    return 4


def _talent_uri(num: int) -> str:
    path = MZ_ICON_PATH / f"{num}.png"
    if not path.exists():
        path = MZ_ICON_PATH / "0.png"
    return _file_uri(path)


def _fetter_uri(num: int) -> str:
    path = HG_ICON_PATH / f"{num}.png"
    if not path.exists():
        path = HG_ICON_PATH / "0.png"
    return _file_uri(path)


def _char_card_html(char: MihoyoAvatar, card_w: int, card_h: int) -> str:
    def sx(n: int) -> int:
        return round(n * card_w / CHAR_NATIVE_W)

    def sy(n: int) -> int:
        return round(n * card_h / CHAR_NATIVE_H)

    fs30 = max(8, round(30 * card_h / CHAR_NATIVE_H))
    fs28 = max(8, round(28 * card_h / CHAR_NATIVE_H))

    star = _char_star(char)
    char_id = char["id"]
    weapon = char["weapon"]
    weapon_star = min(max(int(weapon["rarity"]), 1), 5)
    weapon_name = weapon["name"]

    bg = _file_uri(CHAR_TEXT / f"char_bg{star}.png")
    fg = _file_uri(CHAR_TEXT / "char_fg.png")
    weapon_bg = _file_uri(CHAR_TEXT / f"weapon{weapon_star}.png")
    char_icon = _path_png_uri(CHAR_PATH / f"{char_id}.png", (CHAR_ICON_SIZE, CHAR_ICON_SIZE))
    weapon_icon = _path_png_uri(WEAPON_PATH / f"{weapon_name}.png", (WEAPON_ICON_SIZE, WEAPON_ICON_SIZE))
    namecard = _namecard_uri(char_id)
    talent = _talent_uri(char["actived_constellation_num"])
    fetter = _fetter_uri(char["fetter"])

    dim = char_total_score(char) < CHAR_SCORE_FLOOR
    wrap_op = ";opacity:0.85" if dim else ""
    parts: list[str] = [
        f'<div style="position:relative;width:{card_w}px;height:{card_h}px{wrap_op}">',
        _abs_img(bg, 0, 0, card_w, card_h),
        _abs_img(namecard, sx(32), sy(29), sx(NAMECARD_W), sy(NAMECARD_H)),
    ]
    if dim:
        parts.append(
            f'<div style="position:absolute;left:{sx(32)}px;top:{sy(29)}px;'
            f"width:{sx(NAMECARD_W)}px;height:{sy(NAMECARD_H)}px;"
            f'background:rgba(0,0,0,0.70)"></div>'
        )
    parts.extend(
        [
            _abs_img(char_icon, sx(43), sy(35), sx(CHAR_ICON_SIZE), sy(CHAR_ICON_SIZE)),
            _abs_img(weapon_bg, sx(343), sy(33), sx(WEAPON_BG_SIZE), sy(WEAPON_BG_SIZE)),
            _abs_img(weapon_icon, sx(366), sy(55), sx(WEAPON_ICON_SIZE), sy(WEAPON_ICON_SIZE)),
            _abs_img(fg, 0, 0, card_w, card_h),
            _abs_img(talent, sx(273), sy(55), sx(TALENT_W), sy(TALENT_H)),
            _abs_img(fetter, sx(273), sy(124), sx(FETTER_W), sy(FETTER_H)),
            _label(f"Lv{char['level']}", sx(110), sy(261), fs30, sx(120)),
            _label(weapon_name, sx(453), sy(264), fs28, sx(210)),
            _label(f"Lv{weapon['level']}", sx(496), sy(212), fs28, sx(90)),
            _label(str(weapon["affix_level"]), sx(513), sy(80), fs28, sx(40)),
            "</div>",
        ]
    )
    return "".join(parts)


def _char_section_html(
    chars: list[MihoyoAvatar],
    *,
    side_by_side: bool,
    based_w: int,
    based_h: int,
    cols: int,
    card_w: int,
    card_h: int,
    pad_x: int,
    card_y0: int,
) -> str:
    parts: list[str] = [f'<div style="position:relative;width:{based_w}px;height:{based_h}px">']
    if not side_by_side:
        div_d = _file_uri(CHAR_TEXT / "div_d.png")
        parts.append(_abs_img(div_d, 0, CHAR_DIV_Y, based_w, 80))
    for index, char in enumerate(chars):
        left = pad_x + (index % cols) * (card_w + CHAR_GAP_X)
        top = card_y0 + (index // cols) * card_h
        parts.append(
            f'<div style="position:absolute;left:{left}px;top:{top}px">{_char_card_html(char, card_w, card_h)}</div>'
        )
    parts.append("</div>")
    return "".join(parts)


async def _explore_html(
    raw_data: IndexData,
    packed: WorldPacked,
    world_block_h: int,
) -> str:
    stats = raw_data["stats"]
    culus = _culus_pairs(stats)
    culus_n = len(culus)
    explore_h = _explore_height(culus_n, world_block_h)
    culus_rows = ((culus_n - 1) // EXPLORE_COLS) + 1

    parts: list[str] = [
        f'<div style="position:relative;width:{EXPLORE_W}px;height:{explore_h}px">',
        _abs_img(_file_uri(COLLECT_TEXT / "div_a.png"), 0, EXPLORE_TITLE_OFFER, EXPLORE_W, 80),
    ]

    for index_e, (key, num) in enumerate(culus):
        stem = key.replace("culus_number", "")
        culus_zh = STCMAP[stem]
        icon_path = COLLECT_TEXT / f"Item_{stem.capitalize()}culus.webp"
        icon_uri = _path_png_uri(icon_path, (154, 154))
        max_num = expmax_data[culus_zh]
        percent = (num / max_num) * 100
        level_name = "已集齐" if num >= CMAP[culus_zh][0] else "未集齐"
        left = EXPLORE_OFFER_X + EXPLORE_CARD_STEP * (index_e % EXPLORE_COLS)
        top = EXPLORE_DIV_H + EXPLORE_LINE * (index_e // EXPLORE_COLS) + EXPLORE_TITLE_OFFER
        parts.append(
            await _area_card_html(
                icon_uri=icon_uri,
                icon_pos=(73, 50),
                icon_size=(154, 154),
                percent=percent,
                sub_text=f"进度：{num} / {max_num}",
                com_text="收集完成度",
                name=culus_zh,
                level=num,
                level_name=level_name,
                offerings=[],
                offer=15,
                left=left,
                top=top,
            )
        )

    chest_head_y = EXPLORE_DIV_H + EXPLORE_LINE * culus_rows + EXPLORE_TITLE_OFFER + EXPLORE_SECTION_GAP
    parts.append(
        _abs_img(
            _file_uri(COLLECT_TEXT / "div_b.png"),
            0,
            chest_head_y,
            EXPLORE_W,
            80,
        )
    )

    chest_counts: dict[str, int] = {
        "普通的宝箱": stats["common_chest_number"],
        "精致的宝箱": stats["exquisite_chest_number"],
        "珍贵的宝箱": stats["precious_chest_number"],
        "华丽的宝箱": stats["luxurious_chest_number"],
        "奇馈宝箱": stats["magic_chest_number"],
    }
    for index_c, chest_name in enumerate(_CHEST_ORDER):
        num = chest_counts[chest_name]
        max_num = max_data[chest_name]
        percent = (num / max_num) * 100
        level_name = "已集齐" if num >= max_num else "未集齐"
        icon_uri = _file_uri(COLLECT_TEXT / f"{chest_name}.png")
        left = EXPLORE_OFFER_X + EXPLORE_CARD_STEP * (index_c % EXPLORE_COLS)
        top = chest_head_y + EXPLORE_DIV_H + EXPLORE_LINE * (index_c // EXPLORE_COLS)
        parts.append(
            await _area_card_html(
                icon_uri=icon_uri,
                icon_pos=(75, 55),
                icon_size=(150, 150),
                percent=percent,
                sub_text=f"进度：{num} / {max_num}",
                com_text="收集完成度",
                name=chest_name,
                level=num,
                level_name=level_name,
                offerings=[],
                offer=8,
                left=left,
                top=top,
            )
        )

    world_head_y = chest_head_y + EXPLORE_DIV_H + EXPLORE_LINE + EXPLORE_SECTION_GAP
    parts.append(
        _abs_img(
            _file_uri(COLLECT_TEXT / "div_c.png"),
            0,
            world_head_y,
            EXPLORE_W,
            80,
        )
    )

    world_y0 = world_head_y + EXPLORE_DIV_H + WORLD_PAD_Y
    for col_i, col in enumerate(packed):
        left = WORLD_PAD_LEFT + col_i * (WORLD_COL_W + WORLD_GAP_X)
        y = world_y0
        for world, children, card_h in col:
            parts.append(await _world_card_html(world, children, left, y, card_h))
            y += card_h + WORLD_ROW_GAP

    parts.append("</div>")
    return "".join(parts)


def _title_html(avatar_uri: str, uid: str, raw_data: IndexData) -> str:
    stats = raw_data["stats"]
    title_uri = _file_uri(IMG_TEXT / "title.png")
    return (
        f'<div style="position:relative;width:{TITLE_W}px;height:{TITLE_H}px">'
        f"{_abs_img(title_uri, 0, 0, TITLE_W, TITLE_H)}"
        f"{_abs_img(avatar_uri, 651, 73, AVATAR_SIZE, AVATAR_SIZE)}"
        f"{_label(f'UID {uid}', 840, 530, 36, 500)}"
        f"{_label(str(stats['active_day_number']), 380, 627, 32, 160, align='left')}"
        f"{_label(str(stats['achievement_number']), 872, 627, 32, 160, align='left')}"
        f"{_label(str(stats['spiral_abyss']), 1365, 627, 32, 200, align='left')}"
        f"</div>"
    )


def _wrap_page(width: int, height: int, bg_uri: str, inner: str) -> str:
    footer_uri = _file_uri(IMG_TEXT / "footer.png")
    fx = (width - FOOTER_W) // 2
    fy = height - FOOTER_H - FOOTER_PAD
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  width: {width}px;
  height: {height}px;
  background: #000;
  font-family: {FONT_CSS};
  color: {WHITE};
}}
img {{ display: block; }}
</style>
</head>
<body>
<div style="position:relative;width:{width}px;height:{height}px">
{_abs_img(bg_uri, 0, 0, width, height)}
{inner}
{_abs_img(footer_uri, fx, fy, FOOTER_W, FOOTER_H)}
</div>
</body>
</html>
"""


async def _html_to_img(width: int, height: int, bg_uri: str, inner: str) -> bytes:
    page = _wrap_page(width, height, bg_uri, inner)
    png = await render_html_to_bytes(
        page,
        max_width=width,
        dpi=96,
        default_font_size=16,
        font_name="YuanShen",
        allow_refit=True,
        image_format="png",
        lang="zh",
        root_max_width=width,
    )
    return await convert_img(Image.open(BytesIO(png)))


def _pack_explore(raw_data: IndexData) -> tuple[WorldPacked, int, int]:
    stats = raw_data["stats"]
    culus_n = len(_culus_pairs(stats))
    worlds = list(raw_data["world_explorations"])
    worlds.sort(key=lambda w: -w["id"])
    packed = _pack_world_cols(_group_worlds(worlds))
    world_block_h = _world_block_height(packed)
    explore_h = _explore_height(culus_n, world_block_h)
    return packed, world_block_h, explore_h


async def render_roleinfo_html(
    uid: str,
    raw_data: IndexData,
    char_datas: list[MihoyoAvatar],
    avatar: Image.Image,
    *,
    include_chars: bool = True,
) -> bytes:
    _ensure_ys_font()
    packed, world_block_h, explore_h = _pack_explore(raw_data)
    avatar_uri = _png_uri(avatar.convert("RGBA"))
    title = _title_html(avatar_uri, uid, raw_data)
    explore = await _explore_html(raw_data, packed, world_block_h)
    title_explore = (
        f'<div style="position:absolute;left:0;top:0">{title}</div>'
        f'<div style="position:absolute;left:0;top:{TITLE_TO_EXPLORE_Y}px">{explore}</div>'
    )

    if not include_chars:
        width = TITLE_W
        height = TITLE_TO_EXPLORE_Y + explore_h
        bg_uri = await _bg_jpeg_uri(width, height)
        return await _html_to_img(width, height, bg_uri, title_explore)

    stats = raw_data["stats"]
    char_num = len(char_datas)
    side_by_side = stats["avatar_number"] >= CHAR_SIDE_MIN
    match_height = TITLE_TO_EXPLORE_Y + explore_h if side_by_side else None
    based_w, based_h, cols, card_w, card_h, pad_x, head, foot = _char_grid_metrics(char_num, match_height)
    if side_by_side and cols > SIDE_CHAR_COLS:
        rows_keep = max(1, math.ceil(char_num / SIDE_CHAR_COLS) if char_num else 1)
        need_h = head + foot + rows_keep * CHAR_CARD_H
        match_height = max(TITLE_TO_EXPLORE_Y + explore_h, need_h)
        based_w, based_h, cols, card_w, card_h, pad_x, head, foot = _char_grid_metrics(char_num, match_height)
    rows = max(1, math.ceil(char_num / cols) if char_num else 1)
    y_slack = based_h - head - foot - rows * card_h
    card_y0 = head + max(0, y_slack // 2)

    if side_by_side:
        width = TITLE_W + based_w
        height = based_h
    else:
        width = based_w
        height = based_h + explore_h + 560

    chars = _char_section_html(
        char_datas,
        side_by_side=side_by_side,
        based_w=based_w,
        based_h=based_h,
        cols=cols,
        card_w=card_w,
        card_h=card_h,
        pad_x=pad_x,
        card_y0=card_y0,
    )

    if side_by_side:
        inner = f'{title_explore}<div style="position:absolute;left:{TITLE_W}px;top:0">{chars}</div>'
    else:
        char_y = 500 + explore_h - 110 + 150
        inner = f'{title_explore}<div style="position:absolute;left:0;top:{char_y}px">{chars}</div>'

    bg_uri = await _bg_jpeg_uri(width, height)
    return await _html_to_img(width, height, bg_uri, inner)
