"""深渊 / 剧诗 / 幽境的 HTML 资料卡，版式对齐角色与原魔 wiki。"""

from __future__ import annotations

import re
import html
import base64
import asyncio
import datetime
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter

from gsuid_core.pool import to_thread
from gsuid_core.utils.html_render import _ensure_renderer, render_html_to_bytes
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.ai_core.trigger_bridge import ai_return

from .lunaris_icons import leyline_art_file, sprite_icon_file, monster_icon_file
from .lunaris_tower import (
    TowerMonster,
    TowerTrendRow,
    TowerFloorView,
    chamber_hps,
    floor_totals,
    plain_markup,
    fetch_tower_floor,
    fetch_tower_trend,
    floor_is_plausible,
)
from .lunaris_leyline import LeyView, LeyTrendRow, lane_totals, fetch_leyline, fetch_leyline_trend
from .lunaris_roleplay import RoleView, fetch_roleplay
from ..utils.fonts.genshin_fonts import FONT_ORIGIN_PATH
from ..utils.resource.element_icon import element_icon_path

SCALE = 2
PAGE_W = 680
PAD = 12
GAP = 8
COL = (PAGE_W - PAD * 2 - GAP) // 2
INK = "#f2f5fb"
INK_2 = "rgba(242,245,251,0.62)"
INK_3 = "rgba(242,245,251,0.38)"
GOLD = "#eac683"
HAIR = "rgba(255,255,255,0.08)"
HAIR_TOP = "rgba(255,255,255,0.18)"
SURFACE = "linear-gradient(180deg,rgba(10,12,20,0.55) 0%,rgba(8,10,16,0.72) 100%)"
BODY_FONT = "'MiSans','YuanShen',sans-serif"
NUM_FONT = "'YuanShen','MiSans',sans-serif"
_BG = Path(__file__).resolve().parents[1] / "utils" / "image" / "texture2d" / "bg.jpg"
_FOOT = Path(__file__).resolve().parents[1] / "utils" / "image" / "texture2d" / "footer.png"
_COLOR = re.compile(r"<color=#([0-9A-Fa-f]{6,8})>(.*?)</color>", re.I | re.S)
_NUM = re.compile(r"\d+(?:\.\d+)?%?")
_URI: dict[str, str] = {}
_FONT_READY = False
_RES_COLOR = {
    "物": "#c5c9d3",
    "火": "#ec6a48",
    "水": "#43b6ee",
    "雷": "#b98cf5",
    "冰": "#79d4ec",
    "风": "#3fd6c8",
    "岩": "#e5a93f",
    "草": "#77dd8f",
}
_ELEM: tuple[tuple[str, str], ...] = (
    ("物理伤害", "#c5c9d3"),
    ("冰元素伤害", "#79d4ec"),
    ("火元素伤害", "#ec6a48"),
    ("水元素伤害", "#43b6ee"),
    ("雷元素伤害", "#b98cf5"),
    ("草元素伤害", "#77dd8f"),
    ("风元素伤害", "#3fd6c8"),
    ("岩元素伤害", "#e5a93f"),
    ("冰元素", "#79d4ec"),
    ("火元素", "#ec6a48"),
    ("水元素", "#43b6ee"),
    ("雷元素", "#b98cf5"),
    ("草元素", "#77dd8f"),
    ("风元素", "#3fd6c8"),
    ("岩元素", "#e5a93f"),
)
_ELEM_COLOR = {word: color for word, color in _ELEM}
_ELEM_RE = re.compile("|".join(re.escape(word) for word, _color in _ELEM))


def _ai_return_msg(text: str) -> None:
    try:
        ai_return(text)
    except Exception:
        return


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _nums(text: str) -> str:
    return _NUM.sub(lambda match: f'<span class="num">{match.group(0)}</span>', text)


def _paint(escaped: str) -> str:
    parts: list[str] = []
    pos = 0
    for match in _ELEM_RE.finditer(escaped):
        parts.append(_nums(escaped[pos : match.start()]))
        word = match.group(0)
        parts.append(f'<span class="hi" style="color:{_ELEM_COLOR[word]}">{word}</span>')
        pos = match.end()
    parts.append(_nums(escaped[pos:]))
    return "".join(parts)


def markup_html(text: str) -> str:
    raw = text.replace("\\n", "\n")
    parts: list[str] = []
    pos = 0
    for match in _COLOR.finditer(raw):
        parts.append(_paint(_esc(raw[pos : match.start()])))
        color = match.group(1)[:6]
        parts.append(f'<span class="hi" style="color:#{color}">{_paint(_esc(match.group(2)))}</span>')
        pos = match.end()
    parts.append(_paint(_esc(raw[pos:])))
    return "".join(parts).replace("\n", "<br>")


def format_hp(value: float) -> str:
    if value <= 0:
        return ""
    if value >= 10000:
        wan = f"{value / 10000:.1f}".rstrip("0").rstrip(".")
        return f"HP {wan}万"
    return f"HP {int(value)}"


def _file_uri(path: Path) -> str:
    key = str(path)
    if key in _URI:
        return _URI[key]
    if not path.exists():
        return ""
    mime = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
    uri = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    _URI[key] = uri
    return uri


def _css(accent: str, page_w: int = PAGE_W) -> str:
    col = (page_w - PAD * 2 - GAP) // 2
    col3 = (page_w - PAD * 2 - GAP * 2) // 3
    return f"""
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ width:{page_w}px; font-family:{BODY_FONT}; color:{INK}; background:#05060b; }}
img {{ display:block; }}
.shell {{ position:relative; width:{page_w}px; }}
.pagebg {{ position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; z-index:0; }}
.page {{ position:relative; width:{page_w}px; padding:{PAD}px 0 8px; display:flex;
  flex-direction:column; gap:6px; }}
.mod {{ display:flex; flex-direction:column; gap:4px; padding:0 {PAD}px; }}
.hero {{ border-radius:14px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; padding:16px 18px 14px; }}
.herorow {{ display:flex; align-items:flex-start; gap:16px; }}
.heromain {{ flex:1; min-width:0; }}
.trend {{ width:246px; flex-shrink:0; padding:9px 10px 8px; border-radius:10px;
  background:rgba(0,0,0,0.30); border:1px solid {HAIR}; }}
.trend.wide {{ width:272px; }}
.trendt {{ display:flex; align-items:baseline; gap:6px; font-size:11px; color:{INK_2}; }}
.trendt2 {{ display:flex; align-items:baseline; gap:6px; margin-top:8px; padding-top:7px;
  border-top:1px solid {HAIR}; font-size:11px; color:{INK_2}; }}
.trenden {{ margin-left:auto; font-size:9px; letter-spacing:1px; color:{accent}; }}
.trendsvg {{ display:block; height:86px; margin-top:4px; }}
.trendlg {{ display:flex; align-items:center; gap:4px 7px; margin-top:3px; font-size:11px; color:{INK_2}; }}
.trendlg span {{ display:inline-flex; align-items:center; height:15px; padding:0 5px; border-radius:3px;
  font-size:9px; font-weight:700; color:#fff; }}
.trendlg span.n5 {{ background:#7b4fd6; }}
.trendlg span.n6 {{ background:#c4392d; }}
.trendlg span.up {{ background:#2f7fc4; }}
.trendlg span.dn {{ background:#b87426; }}
.trendlg span.sep {{ width:1px; height:11px; padding:0; margin:0 2px; background:{HAIR}; border-radius:0; }}
.trendlg b {{ font-family:{NUM_FONT}; font-size:12px; color:{GOLD}; margin-right:2px; }}
.hpbars {{ display:flex; flex-direction:column; gap:4px; margin-top:6px; }}
.hprow {{ display:flex; align-items:center; gap:4px; font-size:10px; color:{INK_2}; }}
.hpname {{ width:28px; flex-shrink:0; font-family:{NUM_FONT}; }}
.hptag {{ width:11px; flex-shrink:0; text-align:center; color:{INK_3}; }}
.hpbar {{ height:7px; border-radius:3px; flex-shrink:0; }}
.hprow b {{ width:40px; flex-shrink:0; text-align:right; white-space:nowrap;
  font-family:{NUM_FONT}; font-size:10px; color:{GOLD}; }}
.kicker {{ font-size:11px; letter-spacing:1.6px; color:{accent}; }}
.hname {{ font-family:{NUM_FONT}; font-size:26px; font-weight:700; letter-spacing:1px; margin-top:4px; }}
.hsub {{ margin-top:4px; font-size:14px; color:{GOLD}; }}
.hchips {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; }}
.chip {{ height:22px; padding:0 8px; border-radius:11px; background:rgba(255,255,255,0.08);
  border:1px solid {HAIR}; font-size:11px; display:flex; align-items:center; }}
.chip.gold {{ color:{GOLD}; border-color:rgba(234,198,131,0.45); }}
.hdesc {{ margin-top:10px; font-size:12px; line-height:1.55; color:{INK_2}; }}
.sec {{ display:flex; align-items:center; gap:8px; height:28px; }}
.secbar {{ width:4px; height:18px; border-radius:2px; background:{accent}; flex-shrink:0; }}
.secbox {{ display:flex; align-items:center; gap:7px; height:26px; padding:0 10px 0 8px;
  border-radius:8px; background:linear-gradient(180deg,rgba(255,255,255,0.12),rgba(255,255,255,0.03));
  border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; }}
.sect {{ font-size:14px; font-weight:700; }}
.secen {{ font-size:10px; letter-spacing:1px; color:{accent}; border:1px solid rgba(255,255,255,0.16);
  border-radius:4px; padding:0 6px; height:16px; display:flex; align-items:center; }}
.secr {{ margin-left:auto; font-family:{NUM_FONT}; font-size:13px; font-weight:700; color:{GOLD}; }}
.cols {{ display:flex; gap:{GAP}px; align-items:stretch; }}
.col {{ width:{col}px; min-width:0; display:flex; }}
.col > .panel {{ flex:1; width:100%; }}
.cols3 {{ display:flex; gap:{GAP}px; align-items:flex-start; }}
.col3 {{ width:{col3}px; min-width:0; }}
.panel {{ border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; padding:8px 8px 10px; }}
.half {{ font-size:12px; font-weight:700; color:{GOLD}; margin-bottom:4px; }}
.buff {{ font-size:11px; line-height:1.45; color:{INK_2}; margin-bottom:6px; }}
.igrid {{ display:flex; flex-wrap:wrap; gap:6px 4px; }}
.icell {{ width:96px; display:flex; flex-direction:column; align-items:center; gap:2px; }}
.ibox {{ width:48px; height:48px; border-radius:10px; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.ibox img {{ width:42px; height:42px; object-fit:contain; }}
.inm {{ font-size:10px; color:{INK}; text-align:center; line-height:1.2; width:100%; }}
.icn {{ font-family:{NUM_FONT}; font-size:12px; font-weight:700; color:{GOLD}; }}
.boss {{ font-size:14px; font-weight:700; }}
.bdesc {{ font-size:12px; line-height:1.55; color:{INK_2}; margin-top:4px; }}
.num {{ color:{GOLD}; font-weight:700; font-family:{NUM_FONT}; }}
.hi {{ font-weight:700; }}
.lanehead {{ display:flex; gap:10px; align-items:center; }}
.laneart {{ width:72px; height:72px; border-radius:12px; object-fit:cover; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; }}
.lname {{ font-size:13px; font-weight:700; line-height:1.3; }}
.lmech {{ font-size:11px; color:{GOLD}; margin-top:3px; }}
.resline {{ display:flex; flex-wrap:wrap; gap:4px 10px; margin-top:6px; }}
.reschip {{ font-family:{NUM_FONT}; font-size:12px; font-weight:700; }}
.mname {{ font-size:13px; font-weight:700; color:{accent}; margin-top:8px; }}
.rec {{ display:flex; flex-wrap:wrap; align-items:center; gap:4px 6px; margin-top:6px;
  font-size:12px; color:{INK}; }}
.eicon {{ width:18px; height:18px; object-fit:contain; }}
.ok {{ color:#79d4ec; font-weight:700; }}
.bad {{ color:#ec6a48; font-weight:700; }}
.levels {{ display:flex; flex-wrap:wrap; gap:6px; }}
.lv {{ font-family:{NUM_FONT}; font-size:12px; color:{INK_2}; padding:4px 8px; border-radius:8px;
  background:rgba(0,0,0,0.28); border:1px solid {HAIR}; }}
.foot {{ display:flex; justify-content:center; height:16px; }}
.foot img {{ width:360px; height:13px; opacity:0.5; }}
.empty {{ font-size:13px; color:{INK_2}; line-height:1.5; }}
.lock {{ border-radius:14px; padding:12px 10px 14px; background:{SURFACE};
  border:1px solid rgba(234,198,131,0.55); }}
.lockt {{ text-align:center; font-size:13px; font-weight:700; letter-spacing:2px; color:{GOLD}; }}
.locks {{ display:flex; justify-content:center; gap:22px; margin-top:10px; }}
.elock {{ display:flex; flex-direction:column; align-items:center; gap:4px; }}
.ebox {{ width:64px; height:64px; display:flex; align-items:center; justify-content:center; }}
.ebox img {{ width:56px; height:56px; object-fit:contain; }}
.ename {{ font-size:18px; font-weight:700; letter-spacing:1px; }}
.stage {{ position:relative; overflow:hidden; padding:0; }}
/* 固定 px 框。写成百分比会让 contain 的缩放跟着卡高变，怪物就一会儿大一会儿小、一会儿靠左一会儿靠右。
   top 只敢到 -26px：裁剪后立绘顶部约 6% 是实心内容，再往上就削到头了。 */
.artbox {{ position:absolute; left:-52px; top:-26px; width:492px; height:492px; z-index:0; }}
.artbox img {{ width:100%; height:100%; object-fit:contain; object-position:50% 0%; }}
.veil {{ position:absolute; left:0; right:0; top:0; bottom:0; z-index:1;
  background:linear-gradient(90deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0) 30%,
    rgba(0,0,0,0.46) 56%,rgba(0,0,0,0.8) 100%),
    linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0) 18%,
    rgba(0,0,0,0.72) 34%,rgba(0,0,0,0.92) 50%,rgba(0,0,0,0.94) 100%); }}
.stagein {{ position:relative; z-index:2; padding:142px 12px 12px; }}
.bname {{ font-size:30px; font-weight:700; font-style:italic; letter-spacing:0.8px; line-height:1.2;
  text-align:right; }}
.hpair {{ display:flex; gap:16px; margin-top:6px; justify-content:flex-end; }}
.hpitem {{ display:flex; align-items:center; gap:8px; font-size:12px; color:{INK}; }}
.hpitem b {{ font-family:{NUM_FONT}; color:{GOLD}; font-size:14px; }}
.ntag {{ display:inline-flex; align-items:center; height:16px; padding:0 6px;
  border-radius:4px; background:rgba(255,255,255,0.12); font-size:10px; font-weight:700; color:{GOLD}; }}
.ntag.n5 {{ background:#7b4fd6; color:#fff; }}
.ntag.n6 {{ background:#c4392d; color:#fff; }}
"""


def _section(title: str, en: str, extra: str = "") -> str:
    return (
        '<div class="sec"><div class="secbar"></div><div class="secbox">'
        f'<div class="sect">{_esc(title)}</div><div class="secen">{_esc(en)}</div></div>'
        f'<div class="secr">{_esc(extra)}</div></div>'
    )


def _chips(items: list[tuple[str, bool]]) -> str:
    parts: list[str] = []
    for text, gold in items:
        if not text:
            continue
        kind = " chip gold" if gold else ""
        parts.append(f'<div class="chip{kind}">{_esc(text)}</div>')
    return f'<div class="hchips">{"".join(parts)}</div>'


def _monster_grid(rows: list[tuple[str, str, int, str]]) -> str:
    cells: list[str] = []
    for name, uri, count, hp in rows:
        box = f'<div class="ibox"><img src="{uri}"/></div>' if uri else ""
        count_html = f'<div class="icn">×{count}</div>' if count > 1 else ""
        hp_html = f'<div class="icn">{_esc(hp)}</div>' if hp else ""
        cells.append(f'<div class="icell">{box}<div class="inm">{_esc(name)}</div>{hp_html}{count_html}</div>')
    return f'<div class="igrid">{"".join(cells)}</div>'


def _hero(kicker: str, title: str, sub: str, chips: str, desc: str, side: str = "", side_left: bool = False) -> str:
    body = f'<div class="hdesc">{desc}</div>' if desc else ""
    main = (
        f'<div class="heromain"><div class="kicker">{_esc(kicker)}</div>'
        f'<div class="hname">{_esc(title)}</div>'
        f'<div class="hsub">{_esc(sub)}</div>{chips}{body}</div>'
    )
    row = f"{side}{main}" if side_left else f"{main}{side}"
    return f'<div class="hero"><div class="herorow">{row}</div></div>'


_SPRITE = re.compile(r"\{SPRITE_PRESET#(\d+)\}", re.I)


def _resists(rows: list[tuple[str, float]]) -> str:
    parts: list[str] = []
    for name, value in rows:
        color = _RES_COLOR[name] if name in _RES_COLOR else GOLD
        percent = f"{value * 100:.0f}%"
        parts.append(f'<span class="reschip" style="color:{color}">{_esc(name)} {percent}</span>')
    return f'<div class="resline">{"".join(parts)}</div>'


async def _recommend_html(raw: str, tag: str) -> str:
    ids = _SPRITE.findall(raw)
    uris: dict[str, str] = {}
    for preset_id in ids:
        if preset_id in uris:
            continue
        path = await sprite_icon_file(preset_id)
        uris[preset_id] = _file_uri(path) if path is not None else ""
    parts: list[str] = []
    pos = 0
    for match in _SPRITE.finditer(raw):
        parts.append(markup_html(raw[pos : match.start()]))
        uri = uris[match.group(1)] if match.group(1) in uris else ""
        if uri:
            parts.append(f'<img class="eicon" src="{uri}"/>')
        pos = match.end()
    parts.append(markup_html(raw[pos:]))
    if tag == "Advantage":
        parts.append('<span class="ok">优势</span>')
    elif tag == "Disadvantage":
        parts.append('<span class="bad">劣势</span>')
    return f'<div class="rec">{"".join(parts)}</div>'


def _page(accent: str, bg: str, inner: str, page_w: int = PAGE_W) -> str:
    footer = _file_uri(_FOOT)
    foot = f'<div class="foot"><img src="{footer}"/></div>' if footer else ""
    body = f'<div class="shell"><img class="pagebg" src="{bg}"/><div class="page">{inner}{foot}</div></div>'
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{_css(accent, page_w)}</style></head><body>{body}</body></html>"
    )


def _ensure_font() -> None:
    global _FONT_READY
    if _FONT_READY:
        return
    _ensure_renderer(force=True, extra_fonts=[(FONT_ORIGIN_PATH.read_bytes(), "YuanShen")])
    _FONT_READY = True


@to_thread
def _bg_uri(page_w: int = PAGE_W) -> str:
    src = Image.open(_BG).convert("RGB")
    width = page_w * SCALE
    height = 1400 * SCALE
    scale = max(width / src.width, height / src.height)
    resized = src.resize((int(src.width * scale), int(src.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    crop = resized.crop((left, top, left + width, top + height))
    crop = crop.filter(ImageFilter.GaussianBlur(radius=10))
    veil = Image.new("RGB", crop.size, (5, 6, 12))
    crop = Image.blend(crop, veil, 0.55)
    buf = BytesIO()
    crop.save(buf, format="JPEG", quality=82)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


async def _render(accent: str, inner: str, page_w: int = PAGE_W) -> bytes:
    _ensure_font()
    page = _page(accent, await _bg_uri(page_w), inner, page_w)
    png = await render_html_to_bytes(
        page,
        max_width=page_w * SCALE,
        dpi=96 * SCALE,
        default_font_size=13,
        font_name="YuanShen",
        allow_refit=True,
        image_format="png",
        lang="zh",
        root_max_width=page_w,
    )
    return await convert_img(Image.open(BytesIO(png)).convert("RGBA"))


async def _icons(names: list[str], leyline: bool) -> dict[str, str]:
    wanted: list[str] = []
    for name in names:
        if name and name not in wanted:
            wanted.append(name)

    async def _one(name: str) -> tuple[str, str]:
        path = await (leyline_art_file(name) if leyline else monster_icon_file(name))
        return name, _file_uri(path) if path is not None else ""

    pairs = await asyncio.gather(*(_one(name) for name in wanted))
    return {name: uri for name, uri in pairs}


def _mon_bit(mon: TowerMonster) -> str:
    hp = format_hp(mon["hp"])
    tail = f" {hp}" if hp else ""
    return f"{mon['name']}×{mon['count']}{tail}"


def abyss_ai_text(view: TowerFloorView, trend: list[TowerTrendRow] | None = None) -> str:
    lines = [
        f"【深境螺旋 第{view['floor']}层】{view['buff_name']}",
        f"日程 {view['open_time'][:10]} ~ {view['close_time'][:10]}（{view['schedule_id']}）",
        plain_markup(view["buff_desc"]),
    ]
    if chamber_hps(view):
        upper, lower = floor_totals(view)
        head = f"本层总血量：上半 {format_hp(upper)}、下半 {format_hp(lower)}，合计 {format_hp(upper + lower)}。"
        rows = "；".join(
            f"{item['name']} 上半 {format_hp(item['upper'])} / 下半 {format_hp(item['lower'])}"
            for item in chamber_hps(view)
        )
        lines.append(f"{head} 逐间：{rows}")
    if trend:
        lines.append(
            f"近 {len(trend)} 期上下半走势："
            + "，".join(f"{row['label']} {format_hp(row['upper'])}/{format_hp(row['lower'])}" for row in trend)
        )
    for chamber in view["chambers"]:
        upper = "、".join(_mon_bit(mon) for mon in chamber["upper"])
        lower = "、".join(_mon_bit(mon) for mon in chamber["lower"])
        lines.append(f"{chamber['name']} Lv{chamber['level']}")
        lines.append(f"上半：{upper}。{plain_markup(chamber['upper_buff'])}")
        lines.append(f"下半：{lower}。{plain_markup(chamber['lower_buff'])}")
    return "\n".join(line for line in lines if line)


def _abyss_inner(view: TowerFloorView, icons: dict[str, str], trend: list[TowerTrendRow]) -> str:
    chips = _chips(
        [
            (view["open_time"][:10], False),
            (view["close_time"][:10], False),
            (view["schedule_id"], False),
            ("数据 Lunaris", True),
        ]
    )
    bars = [(item["name"], item["upper"], item["lower"]) for item in chamber_hps(view)]
    blocks = [
        _hero(
            "SPIRAL ABYSS",
            f"深境螺旋 · 第{view['floor']}层",
            view["buff_name"],
            chips,
            markup_html(view["buff_desc"]),
            _abyss_trend_block(trend, bars),
            True,
        )
    ]
    for chamber in view["chambers"]:
        blocks.append(_section(chamber["name"], "CHAMBER", f"Lv{chamber['level']}"))
        halves: list[str] = []
        for label, monsters, buff in (
            ("上半", chamber["upper"], chamber["upper_buff"]),
            ("下半", chamber["lower"], chamber["lower_buff"]),
        ):
            grid = _monster_grid(
                [
                    (
                        mon["name"],
                        icons[mon["icon"]] if mon["icon"] in icons else "",
                        mon["count"],
                        format_hp(mon["hp"]),
                    )
                    for mon in monsters
                ]
            )
            halves.append(
                f'<div class="col"><div class="panel"><div class="half">{label}</div>'
                f'<div class="buff">{markup_html(buff)}</div>{grid}</div></div>'
            )
        blocks.append(f'<div class="cols">{"".join(halves)}</div>')
    return f'<div class="mod">{"".join(blocks)}</div>'


def _with_ranges(body: str, ranges: str) -> str:
    if not ranges:
        return body
    return f"{body}\n{ranges}" if body else ranges


async def build_abyss_image(
    floor: int,
    when: datetime.date | None = None,
    schedule_id: str = "",
    shift: int = 0,
) -> str | bytes:
    viewed, error, ranges = await fetch_tower_floor(floor, when, schedule_id, shift)
    if viewed is None:
        _ai_return_msg(_with_ranges(error, ranges))
        return error
    names = [mon["icon"] for chamber in viewed["chambers"] for mon in chamber["upper"] + chamber["lower"]]
    icons = await _icons(names, False)
    trend = await fetch_tower_trend(
        viewed["schedule_id"],
        floor,
        floor_totals(viewed) if floor_is_plausible(viewed) else (0.0, 0.0),
    )
    _ai_return_msg(_with_ranges(abyss_ai_text(viewed, trend), ranges))
    return await _render("#e7c27a", _abyss_inner(viewed, icons, trend))


def _element_lock(elements: list[str]) -> str:
    if not elements:
        return ""
    cells: list[str] = []
    for name in elements:
        path = element_icon_path(name)
        uri = _file_uri(path) if path is not None else ""
        img = f'<img src="{uri}"/>' if uri else ""
        color = _RES_COLOR[name] if name in _RES_COLOR else GOLD
        cells.append(
            f'<div class="elock"><div class="ebox">{img}</div>'
            f'<div class="ename" style="color:{color}">{_esc(name)}</div></div>'
        )
    return f'<div class="lock"><div class="lockt">本期限制元素</div><div class="locks">{"".join(cells)}</div></div>'


def roleplay_ai_text(view: RoleView) -> str:
    locked = "、".join(view["elements"]) if view["elements"] else "无"
    lines = [
        f"【幻想真境剧诗 {view['schedule_id']}】数据版本 {view['data_version']}",
        f"本期限制元素：{locked}",
        f"日程 {view['begin'][:10]} ~ {view['end'][:10]}",
    ]
    if view["note"]:
        lines.append(view["note"])
    if view["difficulty"]:
        lines.append(
            f"最高档难度 {view['difficulty']}，角色等级≥{view['min_level']}，"
            f"{view['room_count']} 幕，邀约池 {view['invite']}"
        )
    for room in view["rooms"]:
        if not room["monsters"] and not room["boss_name"]:
            lines.append(f"第{room['index']}幕 Lv{room['level']}")
            continue
        names = "、".join(mon["name"] for mon in room["monsters"])
        lines.append(f"第{room['index']}幕 Lv{room['level']} {room['boss_name']}：{names}")
        if room["boss_desc"]:
            lines.append(plain_markup(room["boss_desc"]))
    if not view["rooms"]:
        lines.append("这一期怪物还没公布。")
    return "\n".join(lines)


def _role_inner(view: RoleView, icons: dict[str, str]) -> str:
    chips = _chips(
        [
            (view["begin"][:10], False),
            (view["end"][:10], False),
            (f"难度 {view['difficulty']}" if view["difficulty"] else "", True),
            (f"Lv≥{view['min_level']}" if view["min_level"] else "", False),
            (f"{view['room_count']}幕" if view["room_count"] else "", False),
            (f"数据 {view['data_version']}", True),
        ]
    )
    blocks = [
        _hero("IMAGINARIUM THEATER", "幻想真境剧诗", f"日程 {view['schedule_id']}", chips, markup_html(view["note"])),
        _element_lock(view["elements"]),
    ]
    quiet: list[str] = []
    for room in view["rooms"]:
        if not room["monsters"] and not room["boss_name"]:
            quiet.append(f"第{room['index']}幕 Lv{room['level']}")
            continue
        label = f"额外 {room['index']}" if room["extra"] else f"第{room['index']}幕"
        blocks.append(_section(label, "ACT", room["boss_name"] or f"Lv{room['level']}"))
        grid = _monster_grid(
            [(mon["name"], icons[mon["icon"]] if mon["icon"] in icons else "", 1, "") for mon in room["monsters"]]
        )
        blocks.append(
            '<div class="panel">'
            f'<div class="boss">{_esc(room["boss_name"])}</div>'
            f'<div class="bdesc">{markup_html(room["boss_desc"])}</div>{grid}</div>'
        )
    if quiet:
        chips_html = "".join(f'<div class="lv">{_esc(item)}</div>' for item in quiet)
        blocks.append(_section("其余幕", "LEVEL", ""))
        blocks.append(f'<div class="panel"><div class="levels">{chips_html}</div></div>')
    if not view["rooms"]:
        blocks.append('<div class="panel"><div class="empty">这一期怪物阵容 Lunaris 还没公布。</div></div>')
    return f'<div class="mod">{"".join(blocks)}</div>'


async def build_roleplay_image(
    schedule_id: str = "",
    when: datetime.date | None = None,
    shift: int = 0,
) -> str | bytes:
    viewed, error, ranges = await fetch_roleplay(schedule_id, when=when, shift=shift)
    if viewed is None:
        _ai_return_msg(_with_ranges(error, ranges))
        return error
    _ai_return_msg(_with_ranges(roleplay_ai_text(viewed), ranges))
    names = [mon["icon"] for room in viewed["rooms"] for mon in room["monsters"]]
    icons = await _icons(names, False)
    return await _render("#d4a4f5", _role_inner(viewed, icons))


def leyline_ai_text(view: LeyView, trend: list[LeyTrendRow] | None = None) -> str:
    lines = [
        f"【幽境危战 {view['schedule_id']}】{view['name']}",
        f"日程 {view['begin'][:10]} ~ {view['end'][:10]}，同栏为 N5 Lv105 与 N6 Lv110，机制取高难度",
    ]
    if trend:
        n5, n6 = lane_totals(view)
        lines.append(
            f"三只怪血量合计：N5 {format_hp(n5)}、N6 {format_hp(n6)}。"
            f"近 {len(trend)} 期 N5/N6 走势："
            + "，".join(f"{row['label']} {format_hp(row['n5'])}/{format_hp(row['n6'])}" for row in trend)
        )
    for lane in view["lanes"]:
        bits = " ".join(f"{item['label']} Lv{item['level']} {format_hp(item['hp'])}" for item in lane["hps"])
        lines.append(f"{lane['name']} {bits}")
        if lane["special"]:
            lines.append(plain_markup(lane["special"]))
        for mech in lane["mechs"]:
            lines.append(f"高难度机制 {mech['name']}：{plain_markup(mech['body'])}")
        for tip in lane["tips"]:
            lines.append(f"推荐 {tip['tag']} {plain_markup(_SPRITE.sub('', tip['text']))}")
        resists = " ".join(f"{item['name']}{item['value'] * 100:.0f}%" for item in lane["resists"])
        lines.append(resists)
    return "\n".join(line for line in lines if line)


_TREND_LEFT = 6
_TREND_RIGHT = 220
_TREND_TOP = 4
_TREND_BOTTOM = 58
_SERIES_LEY = (("n5", "#8f6fe0", "#b39aee"), ("n6", "#e05545", "#f08a7e"))
_SERIES_ABY = (("upper", "#4f9fe0", "#9fd0f2"), ("lower", "#e0913c", "#f2c48d"))


def _hp_line_chart(
    labels: list[str],
    marks: list[int],
    series: list[tuple[list[float], str, str]],
    fill: str,
    width: int = 226,
) -> str:
    """共用一根 0 起纵轴的折线。量纲一致才不误导，所以不给每条线单独归一。"""
    if len(labels) < 2:
        return ""
    peak = max(max(values) for values, _stroke, _dot in series) * 1.14
    if peak <= 0:
        return ""
    right = width - 6
    step = (right - _TREND_LEFT) / (len(labels) - 1)
    rise = _TREND_BOTTOM - _TREND_TOP

    def spot(index: int, value: float) -> str:
        x = _TREND_LEFT + step * index
        y = _TREND_BOTTOM - rise * (value / peak)
        return f"{x:.1f},{y:.1f}"

    bits = [
        '<defs><linearGradient id="trfill" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{fill}" stop-opacity="0.30"/>'
        f'<stop offset="1" stop-color="{fill}" stop-opacity="0"/></linearGradient></defs>',
        f'<line x1="{_TREND_LEFT}" y1="{_TREND_BOTTOM}" x2="{right}" y2="{_TREND_BOTTOM}"'
        f' stroke="rgba(255,255,255,0.14)" stroke-width="1"/>',
    ]
    # 面积铺在最高那条线下面
    fill_values = max((values for values, _stroke, _dot in series), key=lambda item: item[-1])
    top_points = " ".join(spot(index, fill_values[index]) for index in range(len(labels)))
    bits.append(
        f'<polygon points="{_TREND_LEFT},{_TREND_BOTTOM} {top_points} {right},{_TREND_BOTTOM}" fill="url(#trfill)"/>'
    )
    for index in marks:
        x = _TREND_LEFT + step * index
        bits.append(
            f'<line x1="{x:.1f}" y1="{_TREND_TOP}" x2="{x:.1f}" y2="{_TREND_BOTTOM}"'
            f' stroke="{GOLD}" stroke-opacity="0.45" stroke-width="1" stroke-dasharray="2 3"/>'
        )
    for values, stroke, _dot in series:
        points = " ".join(spot(index, values[index]) for index in range(len(labels)))
        bits.append(
            f'<polyline points="{points}" fill="none" stroke="{stroke}" stroke-width="1.8"'
            f' stroke-linejoin="round" stroke-linecap="round"/>'
        )
    for index, label in enumerate(labels):
        x = _TREND_LEFT + step * index
        for values, _stroke, dot in series:
            y = _TREND_BOTTOM - rise * (values[index] / peak)
            if index in marks:
                bits.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.4" fill="{dot}" fill-opacity="0.28"/>')
            bits.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="{dot}"/>')
        tint = GOLD if index in marks else INK_3
        # 首尾标签改成贴边对齐，否则 text-anchor=middle 会被 viewBox 切掉半个字
        anchor = "start" if index == 0 else "end" if index == len(labels) - 1 else "middle"
        bits.append(
            f'<text x="{x:.1f}" y="{_TREND_BOTTOM + 14}" font-size="9" fill="{tint}" text-anchor="{anchor}"'
            f' font-family="{NUM_FONT}">{_esc(label)}</text>'
        )
    return f'<svg class="trendsvg" viewBox="0 0 {width} 76" width="{width}" height="76">{"".join(bits)}</svg>'


def _period_label(text: str) -> str:
    """深渊 buff 名带「之月」后缀，6 个三字标签横排在 226px 里会互相压到。"""
    if len(text) > 2 and text.endswith("之月"):
        return text[:-2]
    return text


def _compact_hp(value: float) -> str:
    """逐间条上的短写法。小标题已经写了「血量」，这里不再重复 HP。"""
    if value <= 0:
        return "-"
    if value >= 10000:
        return f"{value / 10000:.1f}".rstrip("0").rstrip(".") + "万"
    return str(int(value))


def _hp_bars(rows: list[tuple[str, float, float]], top: str, bottom: str) -> str:
    """当期逐间血量条。上半 / 下半并排，最长的一条铺满。"""
    if not rows:
        return ""
    peak = max(max(upper, lower) for _name, upper, lower in rows)
    if peak <= 0:
        return ""
    lines: list[str] = []
    for name, upper, lower in rows:
        cells: list[str] = []
        for value, tag, color in ((upper, "上", top), (lower, "下", bottom)):
            width = max(2.0, 44.0 * (value / peak))
            cells.append(
                f'<span class="hptag">{tag}</span>'
                f'<span class="hpbar" style="width:{width:.1f}px;background:{color}"></span>'
                f"<b>{_esc(_compact_hp(value))}</b>"
            )
        lines.append(f'<div class="hprow"><span class="hpname">{_esc(name)}</span>{"".join(cells)}</div>')
    return f'<div class="hpbars">{"".join(lines)}</div>'


def _ley_trend_block(rows: list[LeyTrendRow]) -> str:
    """幽境：近几期三只怪 N5 / N6 总血量。"""
    if len(rows) < 2:
        return ""
    labels = [_period_label(row["label"]) for row in rows]
    marks = [index for index, row in enumerate(rows) if row["current"]]
    svg = _hp_line_chart(
        labels,
        marks,
        [([row[key] for row in rows], stroke, dot) for key, stroke, dot in _SERIES_LEY],
        "#e05545",
    )
    if not svg:
        return ""
    last = rows[-1]
    legend = (
        f'<div class="trendlg"><span class="n5">N5</span><b>{_esc(format_hp(last["n5"]))}</b>'
        f'<span class="sep"></span><span class="n6">N6</span><b>{_esc(format_hp(last["n6"]))}</b></div>'
    )
    return (
        f'<div class="trend"><div class="trendt"><span>近 {len(rows)} 期 · 三怪总血量</span>'
        f'<span class="trenden">TOTAL HP</span></div>{svg}{legend}</div>'
    )


def _abyss_trend_block(trend: list[TowerTrendRow], bars: list[tuple[str, float, float]]) -> str:
    """深渊：近几期上下半折线 + 当期逐间血量条。"""
    if len(trend) < 2 and not bars:
        return ""
    parts: list[str] = []
    if len(trend) >= 2:
        labels = [_period_label(row["label"]) for row in trend]
        marks = [index for index, row in enumerate(trend) if row["current"]]
        svg = _hp_line_chart(
            labels,
            marks,
            [([row[key] for row in trend], stroke, dot) for key, stroke, dot in _SERIES_ABY],
            "#e0913c",
            252,
        )
        if svg:
            last = trend[-1]
            legend = (
                f'<div class="trendlg"><span class="up">上半</span><b>{_esc(format_hp(last["upper"]))}</b>'
                f'<span class="sep"></span><span class="dn">下半</span><b>{_esc(format_hp(last["lower"]))}</b></div>'
            )
            parts.append(
                f'<div class="trendt"><span>近 {len(trend)} 期 · 上下半血量</span>'
                f'<span class="trenden">TOTAL HP</span></div>{svg}{legend}'
            )
    if bars:
        parts.append(
            '<div class="trendt2"><span>当期逐间血量</span><span class="trenden">THIS FLOOR</span></div>'
            + _hp_bars(bars, "#4f9fe0", "#e0913c")
        )
    if not parts:
        return ""
    return f'<div class="trend wide">{"".join(parts)}</div>'


async def _ley_inner(view: LeyView, icons: dict[str, str], trend: list[LeyTrendRow]) -> str:
    chips = _chips(
        [
            (view["begin"][:10], False),
            (view["end"][:10], False),
            ("N5 Lv105", True),
            ("N6 Lv110", True),
            (view["schedule_id"], False),
        ]
    )
    blocks = [_hero("STYGIAN ONSLAUGHT", "幽境危战", view["name"], chips, "", _ley_trend_block(trend))]
    blocks.append(_section("N5 / N6", "HARD", ""))
    for lane in view["lanes"]:
        uri = icons[lane["icon"]] if lane["icon"] in icons else ""
        hp_bits = "".join(
            (
                f'<div class="hpitem"><span class="ntag{badge}">{_esc(item["label"])}</span>'
                f"<span>Lv{item['level']}</span><b>{_esc(format_hp(item['hp']))}</b></div>"
            )
            for item in lane["hps"]
            if item["hp"] > 0
            for badge in (" n5" if item["label"] == "N5" else " n6" if item["label"] == "N6" else "",)
        )
        title = f'<div class="bname">{_esc(lane["name"])}</div><div class="hpair">{hp_bits}</div>'
        art = f'<div class="artbox"><img src="{uri}"/></div>' if uri else ""
        veil = '<div class="veil"></div>' if uri else ""
        mech_html = "".join(
            f'<div class="mname">{_esc(mech["name"])}</div><div class="bdesc">{markup_html(mech["body"])}</div>'
            for mech in lane["mechs"]
            if mech["name"] or mech["body"]
        )
        tip_html = "".join([await _recommend_html(tip["text"], tip["tag"]) for tip in lane["tips"]])
        blocks.append(
            f'<div class="panel stage">{art}{veil}<div class="stagein">{title}'
            f'<div class="bdesc">{markup_html(lane["special"])}</div>'
            f"{mech_html}{tip_html}"
            f"{_resists([(item['name'], item['value']) for item in lane['resists']])}</div></div>"
        )
    return f'<div class="mod">{"".join(blocks)}</div>'


async def build_leyline_image(
    schedule_id: str = "",
    when: datetime.date | None = None,
    shift: int = 0,
) -> str | bytes:
    viewed, error, ranges = await fetch_leyline(schedule_id, when=when, shift=shift)
    if viewed is None:
        _ai_return_msg(_with_ranges(error, ranges))
        return error
    icons = await _icons([lane["icon"] for lane in viewed["lanes"]], True)
    trend = await fetch_leyline_trend(viewed["schedule_id"], lane_totals(viewed))
    _ai_return_msg(_with_ranges(leyline_ai_text(viewed, trend), ranges))
    return await _render("#7dcea0", await _ley_inner(viewed, icons, trend))
