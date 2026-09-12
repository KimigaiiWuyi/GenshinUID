"""Wiki 一页 HTML 卡片：角色 / 武器 / 圣遗物 / 食物 / 原魔。视觉对齐面板卡。"""

from __future__ import annotations

import re
import html
import base64
import shutil
from io import BytesIO
from pathlib import Path

from PIL import Image
from httpx import AsyncClient

from gsuid_core.pool import to_thread
from gsuid_core.utils.html_render import _ensure_renderer, render_html_to_bytes
from gsuid_core.utils.api.ambr.api import AMBR_ICON_URL
from gsuid_core.ai_core.trigger_bridge import ai_return
from gsuid_core.utils.api.ambr.request import get_ambr_icon

from .wiki_data import (
    CharWiki,
    FoodWiki,
    WikiItem,
    WeaponWiki,
    FetterBlock,
    MonsterWiki,
    ArtifactWiki,
    CharStoryWiki,
    parse_query,
    food_ai_text,
    quote_ai_text,
    story_ai_text,
    load_char_wiki,
    load_food_wiki,
    weapon_ai_text,
    char_const_text,
    load_char_story,
    load_voice_file,
    monster_ai_text,
    quote_line_text,
    artifact_ai_text,
    char_talent_text,
    load_weapon_wiki,
    load_monster_wiki,
    parse_voice_query,
    char_material_text,
    load_artifact_wiki,
)
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import get_v4_bg
from ..genshinuid_enka.hero_art import hex_rgb, hero_frame
from ..utils.fonts.genshin_fonts import FONT_ORIGIN_PATH
from ..utils.resource.element_icon import element_icon_path
from ..utils.resource.RESOURCE_PATH import (
    REL_PATH,
    CHAR_PATH,
    ICON_PATH,
    WEAPON_PATH,
    GACHA_IMG_PATH,
    WIKI_DATA_ICON,
    MONSTER_ICON_PATH,
    WIKI_DATA_MONSTER_ICON,
)

SCALE = 4
PAGE_W = 640
CHAR_W = 1280
PAD = 12
COL_GAP = 8
CHAR_COL = (CHAR_W - PAD * 2 - COL_GAP) // 2
CHAR_COL3 = (CHAR_W - PAD * 2 - COL_GAP * 2) // 3
VOICE_SIDE = 8
PAGE_BG_H = 900
INNER_W = PAGE_W - PAD * 2
HERO_H = 348
CHAR_HERO_H = 520
ART_W = 300
CHAR_ART_W = 420
HERO_TXT_L = ART_W - 10
HERO_TXT_W = PAGE_W - HERO_TXT_L - PAD
BODY_FONT = "'MiSans','YuanShen',sans-serif"
NUM_FONT = "'YuanShen','MiSans',sans-serif"
INK = "#f2f5fb"
INK_2 = "rgba(242,245,251,0.62)"
INK_3 = "rgba(242,245,251,0.34)"
GOLD = "#eac683"
SURFACE = "linear-gradient(180deg,rgba(10,12,20,0.42) 0%,rgba(8,10,16,0.56) 100%)"
HAIR = "rgba(255,255,255,0.08)"
HAIR_TOP = "rgba(255,255,255,0.18)"
FOOTER = Path(__file__).resolve().parents[1] / "utils" / "image" / "texture2d" / "footer.png"
STAT_ICON_DIR = Path(__file__).resolve().parents[1] / "genshinuid_enka" / "texture2D" / "icon"
_URI: dict[str, str] = {}
_YS_READY = False
_ACCENT: dict[str, str] = {
    "Anemo": "#3fd6c8",
    "Cryo": "#79d4ec",
    "Dendro": "#77dd8f",
    "Electro": "#b98cf5",
    "Geo": "#e5a93f",
    "Hydro": "#43b6ee",
    "Pyro": "#ec6a48",
}
_RES_COLOR: dict[str, str] = {
    "物": "#c5c9d3",
    "火": "#ec6a48",
    "水": "#43b6ee",
    "雷": "#b98cf5",
    "冰": "#79d4ec",
    "风": "#3fd6c8",
    "岩": "#e5a93f",
    "草": "#77dd8f",
}
_COLOR_TAG = re.compile(r"<color=#([0-9A-Fa-f]{6,8})>(.*?)</color>", re.S)
_ITALIC = re.compile(r"</?i>")
_NUM_TOKEN = re.compile(r"-?\d+(?:\.\d+)?(?:%|秒)?(?:/-?\d+(?:\.\d+)?(?:%|秒)?)*")
_STORY_NUM = re.compile(r"\d+(?:\.\d+)?%?")
_QUOTE_RE = re.compile(r"「([^」]*)」|『([^』]*)』|“([^”]*)”|\"([^\"]*)\"")
_STAT_PAIRS: tuple[tuple[str, str], ...] = tuple(
    sorted(
        (
            ("雷元素伤害加成", "雷元素伤害加成"),
            ("火元素伤害加成", "火元素伤害加成"),
            ("水元素伤害加成", "水元素伤害加成"),
            ("冰元素伤害加成", "冰元素伤害加成"),
            ("风元素伤害加成", "风元素伤害加成"),
            ("岩元素伤害加成", "岩元素伤害加成"),
            ("草元素伤害加成", "草元素伤害加成"),
            ("物理伤害加成", "物理伤害加成"),
            ("元素充能效率", "元素充能效率"),
            ("雷元素伤害", "雷元素伤害加成"),
            ("火元素伤害", "火元素伤害加成"),
            ("水元素伤害", "水元素伤害加成"),
            ("冰元素伤害", "冰元素伤害加成"),
            ("风元素伤害", "风元素伤害加成"),
            ("岩元素伤害", "岩元素伤害加成"),
            ("草元素伤害", "草元素伤害加成"),
            ("百分比攻击力", "百分比攻击力"),
            ("百分比防御力", "百分比防御力"),
            ("百分比血量", "百分比血量"),
            ("元素充能", "元素充能效率"),
            ("元素精通", "元素精通"),
            ("暴击伤害", "暴击伤害"),
            ("治疗加成", "治疗加成"),
            ("物理伤害", "物理伤害加成"),
            ("基础攻击力", "攻击力"),
            ("基础生命值", "血量"),
            ("基础防御力", "防御力"),
            ("暴击率", "暴击率"),
            ("攻击力", "攻击力"),
            ("防御力", "防御力"),
            ("生命值", "血量"),
            ("血量", "血量"),
        ),
        key=lambda x: len(x[0]),
        reverse=True,
    )
)


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


def _jpeg_uri(img: Image.Image, quality: int = 84) -> str:
    buf = BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality, optimize=True)
    return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode('ascii')}"


def _file_uri(path: Path) -> str:
    key = f"file:{path}"
    if key in _URI:
        return _URI[key]
    if not path.exists():
        _URI[key] = ""
        return ""
    suffix = path.suffix.lower()
    mime = "image/png"
    if suffix in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    uri = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    _URI[key] = uri
    return uri


def _icon(path: Path, css_size: int) -> str:
    if not path.exists():
        return ""
    px = css_size * SCALE
    key = f"resize:{path}:{px}"
    if key in _URI:
        return _URI[key]
    img = Image.open(path).convert("RGBA").resize((px, px), Image.Resampling.LANCZOS)
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


def _esc(text: str) -> str:
    return html.escape(text)


def _stat_icon_html(key: str, css: int = 14) -> str:
    path = STAT_ICON_DIR / f"{key}.png"
    if not path.exists():
        return ""
    src = _icon(path, css)
    if not src:
        return ""
    return f'<img class="sic" src="{src}"/>'


def _stat_key_in(window: str) -> str:
    for phrase, key in _STAT_PAIRS:
        if phrase in window:
            return key
    return ""


def _mark_nums(text: str) -> str:
    """转义后把数值标橙黄，并在能对应到属性时于数值前加 ICON。"""
    escaped = _esc(text)

    def _wrap(m: re.Match[str]) -> str:
        left = escaped[max(0, m.start() - 40) : m.start()]
        right = escaped[m.end() : min(len(escaped), m.end() + 28)]
        key = _stat_key_in(left + right)
        ic = _stat_icon_html(key) if key else ""
        return f'{ic}<b class="num">{m.group(0)}</b>'

    return _NUM_TOKEN.sub(_wrap, escaped)


def _mark_story_nums(escaped: str) -> str:
    return _STORY_NUM.sub(lambda m: f'<span class="hi">{m.group(0)}</span>', escaped)


def _mark_glow(text: str) -> str:
    """故事正文：数字和「」/引号内文字略提亮。"""
    parts: list[str] = []
    pos = 0
    for m in _QUOTE_RE.finditer(text):
        parts.append(_mark_story_nums(_esc(text[pos : m.start()])))
        inner = m.group(1) or m.group(2) or m.group(3) or m.group(4) or ""
        open_ch = m.group(0)[0]
        close_ch = m.group(0)[-1]
        parts.append(f'{_esc(open_ch)}<span class="hi">{_mark_story_nums(_esc(inner))}</span>{_esc(close_ch)}')
        pos = m.end()
    parts.append(_mark_story_nums(_esc(text[pos:])))
    return "".join(parts).replace("\n", "<br>")


def _accent(element: str) -> str:
    if element in _ACCENT:
        return _ACCENT[element]
    return "#8ec8f0"


def _rgba(color: str, alpha: float) -> str:
    r, g, b = hex_rgb(color)
    return f"rgba({r},{g},{b},{alpha})"


def _rich_html(text: str) -> str:
    raw = _ITALIC.sub("", text.replace("\\n", "\n"))
    plain = _COLOR_TAG.sub(lambda m: m.group(2), raw)
    return _mark_nums(plain).replace("\n", "<br>")


def _img(cls: str, src: str) -> str:
    if not src:
        return ""
    return f'<img class="{cls}" src="{src}"/>'


def _stars(n: int) -> str:
    return "★" * max(1, min(5, n))


def _section(title: str, en: str, accent: str, extra: str = "") -> str:
    return (
        '<div class="sec">'
        f'<div class="secbar" style="background:{accent};box-shadow:0 0 10px {_rgba(accent, 0.45)}"></div>'
        '<div class="secbox">'
        f'<div class="sect">{_esc(title)}</div>'
        f'<div class="secen" style="color:{accent};border-color:{_rgba(accent, 0.45)}">{_esc(en)}</div>'
        "</div>"
        f'<div class="secr">{extra}</div>'
        "</div>"
    )


def _css(accent: str, width: int = PAGE_W) -> str:
    return f"""
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ width:{width}px; font-family:{BODY_FONT}; color:{INK}; background:#05060b; }}
img {{ display:block; }}
.shell {{ position:relative; width:{width}px; }}
.pagebg {{ position:absolute; left:0; top:0; width:100%; height:100%;
  object-fit:cover; object-position:center; z-index:0; }}
.padem {{ position:absolute; left:0; top:{HERO_H}px; width:100%;
  height:calc(100% - {HERO_H}px); z-index:0;
  background:linear-gradient(180deg,rgba(8,10,16,0.16) 0%,rgba(8,10,16,0.42) 100%); }}
.page {{ position:relative; width:{width}px; padding:0 0 {PAD}px; display:flex;
  flex-direction:column; gap:10px; }}
.mod {{ display:flex; flex-direction:column; gap:7px; padding:0 {PAD}px; }}
.cols {{ display:flex; gap:{COL_GAP}px; padding:0 {PAD}px; align-items:flex-start; }}
.col {{ width:{CHAR_COL}px; display:flex; flex-direction:column; gap:7px; min-width:0; }}
.cols3 {{ display:flex; gap:{COL_GAP}px; padding:0 {PAD}px; align-items:flex-start; }}
.col3 {{ width:{CHAR_COL3}px; display:flex; flex-direction:column; gap:7px; min-width:0; }}
.toprow {{ display:flex; width:{width}px; align-items:stretch; gap:{COL_GAP}px;
  padding:10px {PAD}px 0; box-sizing:border-box; }}
.topmats {{ width:{CHAR_COL}px; padding:0; display:flex; flex-direction:column;
  gap:7px; box-sizing:border-box; }}
.topmats .panel {{ flex:1; }}
.hero {{ position:relative; width:{CHAR_COL}px; min-height:{HERO_H}px; overflow:hidden;
  flex-shrink:0; align-self:stretch; border-radius:12px; background:{SURFACE};
  border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; }}
.herowide {{ position:relative; width:{width - PAD * 2}px; min-height:{HERO_H}px; overflow:hidden;
  border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; }}
.herobg {{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover;
  object-position:12% 10%; }}
.heroin {{ position:absolute; left:250px; right:10px; bottom:10px; top:auto; width:auto;
  height:auto; padding:9px 10px 8px; display:flex; flex-direction:column;
  border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; }}
.wide .padem {{ display:none; }}
.sic {{ width:14px; height:14px; display:inline-block; vertical-align:-2px; margin:0 2px 0 1px; }}
.htitle {{ display:flex; align-items:center; gap:7px; min-width:0; }}
.helem {{ width:26px; height:26px; flex-shrink:0; }}
.hname {{ font-family:{NUM_FONT}; font-size:28px; font-weight:700; line-height:1; letter-spacing:1px; }}
.hsub {{ font-size:12px; color:{INK_2}; margin-top:6px; line-height:1.35; }}
.hchips {{ display:flex; flex-wrap:wrap; gap:5px; margin-top:8px; }}
.chip {{ display:flex; align-items:center; height:22px; padding:0 8px; border-radius:11px;
  background:rgba(255,255,255,0.08); border:1px solid {HAIR}; font-size:11px; color:{INK}; }}
.chip.gold {{ color:{GOLD}; border-color:{_rgba(GOLD, 0.45)}; }}
.stats {{ display:flex; flex-direction:column; gap:3px; margin-top:10px; width:100%; }}
.stat {{ width:100%; height:22px; padding:0 8px; border-radius:6px; background:rgba(0,0,0,0.34);
  display:flex; align-items:center; gap:6px; }}
.stat.alt {{ background:rgba(0,0,0,0.50); }}
.stnm {{ flex:1; font-size:11px; color:{INK_2}; }}
.stv {{ font-family:{NUM_FONT}; font-size:14px; font-weight:700; color:{GOLD};
  display:flex; align-items:center; gap:4px; }}
.hdesc {{ margin-top:8px; font-size:11px; line-height:1.45; color:{INK_2}; }}
.sec {{ display:flex; align-items:center; gap:8px; height:28px; }}
.secbar {{ width:4px; height:18px; border-radius:2px; flex-shrink:0; }}
.secbox {{ display:flex; align-items:center; gap:7px; height:26px; padding:0 10px 0 8px;
  border-radius:8px; background:linear-gradient(180deg,rgba(255,255,255,0.12) 0%,
    rgba(255,255,255,0.03) 100%); border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; }}
.sect {{ font-size:14px; font-weight:700; letter-spacing:0.3px; }}
.secen {{ font-size:9px; letter-spacing:1.2px; height:15px; padding:0 6px; border-radius:4px;
  border:1px solid; display:flex; align-items:center; }}
.secr {{ margin-left:auto; font-size:11px; color:{INK_3}; }}
.panel {{ border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; padding:9px 10px 10px; }}
.trow {{ display:flex; gap:8px; padding:8px 0; border-bottom:1px solid {HAIR}; }}
.trow:last-child {{ border-bottom:none; padding-bottom:0; }}
.trow:first-child {{ padding-top:0; }}
.tic {{ width:36px; height:36px; border-radius:18px; flex-shrink:0; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.tic img {{ width:24px; height:24px; }}
.tbody {{ flex:1; min-width:0; }}
.tnm {{ display:flex; align-items:center; gap:6px; }}
.tnm b {{ font-size:13px; font-weight:700; }}
.akey {{ width:16px; height:16px; border-radius:4px; border:1px solid {accent};
  color:{accent}; display:flex; align-items:center; justify-content:center;
  font-family:{NUM_FONT}; font-size:10px; font-weight:700; flex-shrink:0; }}
.tmeta {{ font-size:10px; color:{INK_3}; }}
.tdesc {{ font-size:11px; line-height:1.45; color:{INK_2}; margin-top:4px; }}
.tgrid {{ display:flex; flex-wrap:wrap; gap:4px 10px; margin-top:6px; }}
.tcell {{ width:calc(50% - 5px); display:flex; justify-content:space-between; gap:6px;
  font-size:11px; }}
.tcell span {{ color:{INK_3}; }}
.tcell b {{ font-family:{NUM_FONT}; font-size:12px; font-weight:700; color:{GOLD}; }}
.crow {{ display:flex; gap:8px; padding:7px 0; border-bottom:1px solid {HAIR}; }}
.crow:last-child {{ border-bottom:none; padding-bottom:0; }}
.cic {{ width:32px; height:32px; border-radius:16px; flex-shrink:0; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.cic img {{ width:20px; height:20px; }}
.cnm {{ font-size:12px; font-weight:700; color:{GOLD}; }}
.cdesc {{ font-size:11px; line-height:1.4; color:{INK_2}; margin-top:2px; }}
.igrid {{ display:flex; flex-wrap:wrap; gap:8px; }}
.icell {{ width:72px; display:flex; flex-direction:column; align-items:center; gap:3px; }}
.ibox {{ width:52px; height:52px; border-radius:10px; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.ibox img {{ width:44px; height:44px; object-fit:contain; }}
.inm {{ font-size:10px; color:{INK_2}; text-align:center; line-height:1.2; width:72px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.icn {{ font-family:{NUM_FONT}; font-size:12px; font-weight:700; color:{GOLD}; }}
.fx {{ font-size:12px; line-height:1.5; color:{INK_2}; }}
.fx b {{ color:{GOLD}; font-weight:700; }}
.num {{ color:{GOLD}; font-weight:700; font-family:{NUM_FONT};
  display:inline-flex; align-items:center; gap:2px; }}
.tdesc .num, .cdesc .num {{ color:{GOLD}; }}
.plist {{ display:flex; flex-direction:column; gap:8px; }}
.prow {{ display:flex; gap:8px; align-items:flex-start; }}
.pbox {{ width:48px; height:48px; border-radius:10px; background:rgba(0,0,0,0.38);
  border:1px solid {HAIR}; flex-shrink:0; display:flex; align-items:center; justify-content:center;
  overflow:hidden; }}
.pbox img {{ width:42px; height:42px; object-fit:contain; }}
.pnm {{ font-size:12px; font-weight:700; }}
.pslot {{ font-size:10px; color:{INK_3}; }}
.pdesc {{ font-size:11px; color:{INK_2}; line-height:1.4; margin-top:2px; }}
.resgrid {{ display:grid; grid-template-columns:1fr 1fr; gap:6px 12px; }}
.res {{ display:flex; align-items:center; gap:6px; }}
.rdot {{ width:8px; height:8px; border-radius:4px; flex-shrink:0; }}
.rnm {{ width:16px; font-size:11px; }}
.rbar {{ flex:1; height:7px; border-radius:4px; background:rgba(255,255,255,0.08); overflow:hidden; }}
.rfill {{ height:7px; border-radius:4px; }}
.rval {{ width:42px; text-align:right; font-family:{NUM_FONT}; font-size:12px;
  font-weight:700; color:{GOLD}; }}
.whero {{ position:relative; width:{PAGE_W}px; height:300px; overflow:hidden; }}
.wart {{ position:absolute; left:40px; top:10px; width:240px; height:280px; object-fit:contain; }}
.wtxt {{ position:absolute; left:290px; top:18px; width:330px; }}
.bigicon {{ width:220px; height:220px; object-fit:contain; margin:8px auto 0; }}
.foot {{ display:flex; align-items:center; justify-content:center; height:16px; }}
.foot img {{ width:360px; height:13px; opacity:0.45; }}
.stitle {{ font-size:13px; font-weight:700; color:{GOLD}; margin-bottom:6px; }}
.story {{ font-size:12px; line-height:1.7; color:{INK_2}; }}
.hi {{ color:#f3ead2; }}
.stips {{ font-size:10px; color:{INK_3}; margin-top:6px; }}
.qrow {{ padding:7px 0; border-bottom:1px solid {HAIR}; }}
.qrow:last-child {{ border-bottom:none; padding-bottom:0; }}
.qrow:first-child {{ padding-top:0; }}
.qhead {{ display:flex; align-items:center; gap:6px; }}
.qidx {{ font-family:{NUM_FONT}; font-size:13px; font-weight:700; color:{GOLD};
  min-width:18px; flex-shrink:0; }}
.qtitle {{ font-size:12px; font-weight:700; color:{INK}; }}
.qtext {{ font-size:11px; line-height:1.55; color:{INK_2}; margin-top:3px; }}
"""


def _keep_wiki_file(src: Path, dest: Path) -> Path:
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return dest


async def _asset_path(icon: str) -> Path | None:
    if not icon:
        return None
    name = icon if icon.endswith(".png") else f"{icon}.png"
    cached = WIKI_DATA_ICON / name
    if cached.exists():
        return cached
    bundled = ICON_PATH / name
    if bundled.exists():
        return _keep_wiki_file(bundled, cached)
    url = f"{AMBR_ICON_URL}/{name}"
    try:
        async with AsyncClient(timeout=20) as client:
            req = await client.get(url)
        if req.status_code != 200:
            return None
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(req.content)
        return cached
    except Exception:
        return None


async def _uri_icon(icon: str, css: int) -> str:
    path = await _asset_path(icon)
    if path is None:
        return ""
    return _icon(path, css)


async def _uri_item(item: WikiItem, css: int) -> str:
    return await _uri_icon(item.icon, css)


def _items_html(items: tuple[WikiItem, ...], uris: dict[str, str], extra: tuple[tuple[str, str, int], ...] = ()) -> str:
    bits: list[str] = []
    for it in items:
        src = uris[it.item_id] if it.item_id in uris else ""
        if not src:
            continue
        cnt = f'<div class="icn">{it.count}</div>' if it.count > 0 else '<div class="icn"></div>'
        bits.append(
            '<div class="icell">'
            f'<div class="ibox">{_img("", src)}</div>'
            f'<div class="inm">{_esc(it.name)}</div>'
            f"{cnt}"
            "</div>"
        )
    for name, src, count in extra:
        bits.append(
            '<div class="icell">'
            f'<div class="ibox">{_img("", src)}</div>'
            f'<div class="inm">{_esc(name)}</div>'
            f'<div class="icn">{count}</div>'
            "</div>"
        )
    if not bits:
        return '<div class="fx">无材料数据</div>'
    return f'<div class="igrid">{"".join(bits)}</div>'


@to_thread
def _build_hero(
    splash: Image.Image,
    accent: str,
    width: int = PAGE_W,
    height: int = HERO_H,
    art_w: int = ART_W,
) -> str:
    framed = hero_frame(splash, width * SCALE, height * SCALE, art_w * SCALE)
    return _png_uri(framed)


@to_thread
def _encode_v4_bg(width: int = PAGE_W) -> str:
    return _jpeg_uri(get_v4_bg(width * SCALE, PAGE_BG_H * SCALE), 82)


async def _page_bg(width: int = PAGE_W) -> str:
    key = f"v4bg:{width}:{PAGE_BG_H}:{SCALE}"
    if key in _URI:
        return _URI[key]
    uri = await _encode_v4_bg(width)
    _URI[key] = uri
    return uri


def _load_splash(name: str, char_id: str, icon: str) -> Image.Image:
    gacha = GACHA_IMG_PATH / f"{name}.png"
    if gacha.exists():
        return Image.open(gacha).convert("RGBA")
    nid = char_id.split("-")[0]
    portrait = CHAR_PATH / f"{nid}.png"
    if portrait.exists():
        return Image.open(portrait).convert("RGBA")
    ip = ICON_PATH / f"{icon}.png"
    if ip.exists():
        return Image.open(ip).convert("RGBA")
    return Image.new("RGBA", (ART_W * SCALE, HERO_H * SCALE), (18, 12, 32, 255))


def _elem_icon(element: str, css: int) -> str:
    path = element_icon_path(element)
    if path is None:
        return ""
    return _icon(path, css)


def _char_chips(data: CharWiki) -> list[str]:
    chips = [
        f'<div class="chip gold">{_stars(data.rarity)}</div>',
        f'<div class="chip">{_esc(data.weapon)}</div>',
        f'<div class="chip">{_esc(data.region)}</div>',
        f'<div class="chip">{_esc(data.birthday)}</div>',
    ]
    if data.cv:
        chips.append(f'<div class="chip">CV {_esc(data.cv)}</div>')
    return chips


def _char_stats_html(data: CharWiki) -> str:
    stats = [
        ("生命值", f"{data.hp:,}"),
        ("攻击力", f"{data.atk:,}"),
        ("防御力", f"{data.defense:,}"),
        (data.substat, data.substat_value),
    ]
    return "".join(
        f'<div class="stat{" alt" if i % 2 else ""}"><div class="stnm">{_esc(n)}</div>'
        f'<div class="stv">{_stat_icon_html(_stat_key_in(n), 14)}{_esc(v)}</div></div>'
        for i, (n, v) in enumerate(stats)
        if n and n != "—"
    )


def _char_hero_block(
    data: CharWiki,
    hero: str,
    *,
    with_stats: bool,
    with_desc: bool,
    box: str = "hero",
) -> str:
    title = data.title or data.constellation
    extra = ""
    if with_stats:
        extra += f'<div class="stats">{_char_stats_html(data)}</div>'
    if with_desc:
        extra += f'<div class="hdesc">{_mark_glow(data.description)}</div>'
    return (
        f'<div class="{box}">'
        f'<img class="herobg" src="{hero}"/>'
        '<div class="heroin">'
        '<div class="htitle">'
        f"{_img('helem', _elem_icon(data.element, 26))}"
        f'<div class="hname">{_esc(data.name)}</div>'
        "</div>"
        f'<div class="hsub">{_esc(title)} · {_esc(data.constellation)} · {_esc(data.native)}</div>'
        f'<div class="hchips">{"".join(_char_chips(data))}</div>'
        f"{extra}"
        "</div></div>"
    )


def _combat_talent_html(data: CharWiki, icons: dict[str, str]) -> str:
    bits: list[str] = []
    for t in data.talents:
        if t.slot == "P":
            continue
        meta: list[str] = []
        if t.cooldown:
            meta.append(f"CD {t.cooldown}s")
        if t.cost:
            meta.append(f"能量 {t.cost}")
        grid = "".join(
            f'<div class="tcell"><span>{_esc(a)}</span>'
            f'<b class="num">{_stat_icon_html(_stat_key_in(a + b), 12)}{_esc(b)}</b></div>'
            for a, b in t.rows[:10]
        )
        src = icons[t.icon] if t.icon in icons else ""
        bits.append(
            '<div class="trow">'
            f'<div class="tic">{_img("", src)}</div>'
            '<div class="tbody">'
            '<div class="tnm">'
            f'<div class="akey">{_esc(t.slot)}</div>'
            f"<b>{_esc(t.name)}</b>"
            f'<div class="tmeta">{_esc(" · ".join(meta))}</div>'
            "</div>"
            f'<div class="tdesc">{_rich_html(t.description)}</div>'
            f'<div class="tgrid">{grid}</div>'
            "</div></div>"
        )
    return "".join(bits)


def _passive_html(data: CharWiki, icons: dict[str, str]) -> str:
    bits: list[str] = []
    for t in data.talents:
        if t.slot != "P":
            continue
        src = icons[t.icon] if t.icon in icons else ""
        bits.append(
            '<div class="trow">'
            f'<div class="tic">{_img("", src)}</div>'
            '<div class="tbody">'
            f'<div class="tnm"><b>{_esc(t.name)}</b></div>'
            f'<div class="tdesc">{_rich_html(t.description)}</div>'
            "</div></div>"
        )
    return "".join(bits) if bits else '<div class="fx">无</div>'


def _const_html(data: CharWiki, icons: dict[str, str]) -> str:
    bits: list[str] = []
    for c in data.consts:
        src = icons[c.icon] if c.icon in icons else ""
        bits.append(
            '<div class="crow">'
            f'<div class="cic">{_img("", src)}</div>'
            '<div class="tbody">'
            f'<div class="cnm">C{c.index} {_esc(c.name)}</div>'
            f'<div class="cdesc">{_rich_html(c.description)}</div>'
            "</div></div>"
        )
    return "".join(bits)


def _mat_blocks(data: CharWiki, icons: dict[str, str], accent: str) -> tuple[str, str]:
    mora_uri = icons["202"] if "202" in icons else ""
    item_uris = {it.item_id: (icons[it.item_id] if it.item_id in icons else "") for it in data.ascend_items}
    item_uris.update({it.item_id: (icons[it.item_id] if it.item_id in icons else "") for it in data.talent_items})
    extra_a: tuple[tuple[str, str, int], ...] = ()
    if data.mora_ascend:
        extra_a = (("摩拉", mora_uri, data.mora_ascend),)
    extra_t: tuple[tuple[str, str, int], ...] = ()
    if data.mora_talent:
        extra_t = (("摩拉", mora_uri, data.mora_talent),)
    ascend = (
        _section("突破材料", "ASCENSION", accent, f"Lv.1→{data.level}")
        + f'<div class="panel">{_items_html(data.ascend_items, item_uris, extra_a)}</div>'
    )
    talent = (
        _section("天赋材料（一份 1→10）", "TALENT MAT", accent, "满级三份 ×3")
        + f'<div class="panel">{_items_html(data.talent_items, item_uris, extra_t)}</div>'
    )
    return ascend, talent


def _char_html(data: CharWiki, hero: str, accent: str, icons: dict[str, str]) -> str:
    footer = _file_uri(FOOTER)
    ascend, talent = _mat_blocks(data, icons, accent)
    return "".join(
        [
            '<div class="toprow">',
            _char_hero_block(data, hero, with_stats=True, with_desc=True),
            '<div class="topmats">',
            ascend,
            talent,
            "</div>",
            "</div>",
            '<div class="cols">',
            '<div class="col">',
            _section("天赋", "TALENT", accent, "Lv.10"),
            f'<div class="panel">{_combat_talent_html(data, icons)}</div>',
            "</div>",
            '<div class="col">',
            _section("固有天赋", "PASSIVE", accent),
            f'<div class="panel">{_passive_html(data, icons)}</div>',
            _section("命座", "CONSTELLATION", accent, data.constellation),
            f'<div class="panel">{_const_html(data, icons)}</div>',
            "</div>",
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def _collect_char_icons(data: CharWiki) -> dict[str, str]:
    out: dict[str, str] = {}
    names: list[str] = []
    for t in data.talents:
        if t.icon:
            names.append(t.icon)
    for c in data.consts:
        if c.icon:
            names.append(c.icon)
    for it in (*data.ascend_items, *data.talent_items):
        names.append(it.icon)
        out[it.item_id] = ""
    for name in names:
        uri = await _uri_icon(name, 36)
        out[name] = uri
    for it in (*data.ascend_items, *data.talent_items):
        out[it.item_id] = out[it.icon] if it.icon in out else await _uri_icon(it.icon, 44)
    if data.icon:
        await _uri_icon(data.icon, 64)
    mora = await _uri_icon("UI_ItemIcon_202", 44)
    out["202"] = mora
    return out


def _page(accent: str, bg: str, inner: str, width: int = PAGE_W) -> str:
    wide = " wide" if width > PAGE_W else ""
    body = (
        f'<div class="shell{wide}"><img class="pagebg" src="{bg}"/><div class="padem"></div>'
        f'<div class="page">{inner}</div></div>'
    )
    return (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{_css(accent, width)}</style></head><body>{body}</body></html>"
    )


async def _render_page(accent: str, bg: str, inner: str, width: int = PAGE_W) -> Image.Image:
    _ensure_ys_font()
    page = _page(accent, bg, inner, width)
    png = await render_html_to_bytes(
        page,
        max_width=width * SCALE,
        dpi=96 * SCALE,
        default_font_size=13,
        font_name="YuanShen",
        allow_refit=True,
        image_format="png",
        lang="zh",
        root_max_width=width,
    )
    return Image.open(BytesIO(png)).convert("RGBA")


def _ai_return_msg(text: str) -> None:
    try:
        ai_return(text)
    except Exception:
        return


def _ai_return_weapon(data: WeaponWiki) -> None:
    _ai_return_msg(weapon_ai_text(data))


def _ai_return_artifact(data: ArtifactWiki) -> None:
    _ai_return_msg(artifact_ai_text(data))


def _ai_return_food(data: FoodWiki) -> None:
    _ai_return_msg(food_ai_text(data))


def _ai_return_monster(data: MonsterWiki) -> None:
    _ai_return_msg(monster_ai_text(data))


def _ai_return_story(data: CharStoryWiki) -> None:
    _ai_return_msg(story_ai_text(data))


def _ai_return_voice(data: CharStoryWiki) -> None:
    _ai_return_msg(quote_ai_text(data))


async def _prepare_char(
    text: str,
    *,
    need_icons: bool,
) -> tuple[CharWiki, str, str, dict[str, str]] | str:
    name, level = parse_query(text)
    data = await load_char_wiki(name, level)
    if isinstance(data, str):
        return data
    accent = _accent(data.element)
    splash = _load_splash(data.name, data.char_id, data.icon)
    if data.icon:
        path = await _asset_path(data.icon)
        if path is not None and splash.size[0] < 80:
            splash = Image.open(path).convert("RGBA")
    hero = await _build_hero(splash, accent, PAGE_W, CHAR_HERO_H, CHAR_ART_W)
    icons = await _collect_char_icons(data) if need_icons else {}
    return data, hero, accent, icons


async def render_char_card(text: str) -> str | bytes:
    bundled = await _prepare_char(text, need_icons=True)
    if isinstance(bundled, str):
        return bundled
    data, hero, accent, icons = bundled
    inner = _char_html(data, hero, accent, icons)
    bg = await _page_bg(CHAR_W)
    img = await _render_page(accent, bg, inner, CHAR_W)
    return await convert_img(img)


def _talent_part_html(data: CharWiki, hero: str, accent: str, icons: dict[str, str]) -> str:
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="mod">',
            _char_hero_block(data, hero, with_stats=False, with_desc=False, box="herowide"),
            "</div>",
            '<div class="mod">',
            _section("固有天赋", "PASSIVE", accent),
            f'<div class="panel">{_passive_html(data, icons)}</div>',
            "</div>",
            '<div class="mod">',
            _section("天赋", "TALENT", accent, "Lv.10"),
            f'<div class="panel">{_combat_talent_html(data, icons)}</div>',
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


def _const_part_html(data: CharWiki, hero: str, accent: str, icons: dict[str, str]) -> str:
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="mod">',
            _char_hero_block(data, hero, with_stats=False, with_desc=False, box="herowide"),
            "</div>",
            '<div class="mod">',
            _section("命座", "CONSTELLATION", accent, data.constellation),
            f'<div class="panel">{_const_html(data, icons)}</div>',
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


def _mat_part_html(data: CharWiki, hero: str, accent: str, icons: dict[str, str]) -> str:
    footer = _file_uri(FOOTER)
    ascend, talent = _mat_blocks(data, icons, accent)
    return "".join(
        [
            '<div class="toprow">',
            _char_hero_block(data, hero, with_stats=False, with_desc=False),
            '<div class="topmats">',
            ascend,
            talent,
            "</div></div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def _render_char_part(
    text: str,
    *,
    html_fn,
    ai_fn,
    width: int = CHAR_W,
) -> str | bytes:
    bundled = await _prepare_char(text, need_icons=True)
    if isinstance(bundled, str):
        _ai_return_msg(bundled)
        return bundled
    data, hero, accent, icons = bundled
    _ai_return_msg(ai_fn(data))
    inner = html_fn(data, hero, accent, icons)
    bg = await _page_bg(width)
    img = await _render_page(accent, bg, inner, width)
    return await convert_img(img)


async def render_char_talent_card(text: str) -> str | bytes:
    return await _render_char_part(
        text,
        html_fn=_talent_part_html,
        ai_fn=char_talent_text,
        width=CHAR_COL + PAD * 2,
    )


async def render_char_const_card(text: str) -> str | bytes:
    return await _render_char_part(
        text,
        html_fn=_const_part_html,
        ai_fn=char_const_text,
        width=CHAR_COL + PAD * 2,
    )


async def render_char_material_card(text: str) -> str | bytes:
    return await _render_char_part(
        text,
        html_fn=_mat_part_html,
        ai_fn=char_material_text,
    )


def _weapon_html(data: WeaponWiki, art: str, accent: str, icons: dict[str, str]) -> str:
    mora = icons["202"] if "202" in icons else ""
    ore = icons["104013"] if "104013" in icons else ""
    bits: list[tuple[str, str, int]] = []
    if data.mora:
        bits.append(("摩拉", mora, data.mora))
    if data.ore:
        bits.append(("精锻用魔矿", ore, data.ore))
    extra = tuple(bits)
    item_uris = {it.item_id: (icons[it.item_id] if it.item_id in icons else "") for it in data.items}
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="whero">',
            f'<img class="wart" src="{art}"/>',
            '<div class="wtxt">',
            f'<div class="hname">{_esc(data.name)}</div>',
            '<div class="hchips">',
            f'<div class="chip gold">{_stars(data.rarity)}</div>',
            f'<div class="chip">{_esc(data.weapon_type)}</div>',
            f'<div class="chip">Lv.{data.level}</div>',
            "</div>",
            '<div class="stats">',
            '<div class="stat"><div class="stnm">基础攻击力</div>'
            f'<div class="stv">{_stat_icon_html("攻击力", 14)}{data.atk_base} / {data.atk_max}</div></div>',
            f'<div class="stat alt"><div class="stnm">{_esc(data.substat)}</div>'
            f'<div class="stv">{_stat_icon_html(_stat_key_in(data.substat), 14)}'
            f"{_esc(data.sub_base)} / {_esc(data.sub_max)}</div></div>",
            "</div>",
            f'<div class="hdesc">{_mark_glow(data.description)}</div>',
            "</div></div>",
            '<div class="mod">',
            _section(data.effect_name or "武器特效", "REFINE R1–R5", accent),
            f'<div class="panel"><div class="fx">{_mark_nums(data.effect)}</div></div>',
            "</div>",
            '<div class="mod">',
            _section("突破材料", "ASCENSION", accent, f"1→{data.level}"),
            f'<div class="panel">{_items_html(data.items, item_uris, extra)}</div>',
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def _weapon_art(data: WeaponWiki) -> str:
    wiki_named = WIKI_DATA_ICON / f"{data.name}.png"
    if wiki_named.exists():
        return _icon(wiki_named, 240)
    local = WEAPON_PATH / f"{data.name}.png"
    if local.exists():
        return _icon(_keep_wiki_file(local, wiki_named), 240)
    gacha = data.icon.replace("UI_EquipIcon_", "UI_Gacha_EquipIcon_")
    path = await _asset_path(gacha)
    if path is not None:
        img = Image.open(path).convert("RGBA")
        img = img.resize((240 * SCALE, 240 * SCALE), Image.Resampling.LANCZOS)
        return _png_uri(img)
    path = await _asset_path(data.icon)
    if path is None:
        return ""
    return _icon(path, 240)


async def render_weapon_card(text: str) -> str | bytes:
    name, level = parse_query(text)
    data = await load_weapon_wiki(name, level)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    _ai_return_weapon(data)
    accent = GOLD
    art = await _weapon_art(data)
    icons: dict[str, str] = {}
    for it in data.items:
        icons[it.item_id] = await _uri_item(it, 44)
    icons["202"] = await _uri_icon("UI_ItemIcon_202", 44)
    icons["104013"] = await _uri_icon("UI_ItemIcon_104013", 44)
    inner = _weapon_html(data, art, accent, icons)
    bg = await _page_bg()
    img = await _render_page(accent, bg, inner)
    return await convert_img(img)


def _artifact_html(data: ArtifactWiki, accent: str, icons: dict[str, str]) -> str:
    stars = "/".join(str(s) for s in data.rarity) if data.rarity else "—"
    fx = ""
    if data.effect1:
        fx = f'<div class="fx"><b>1 件套</b> {_mark_nums(data.effect1)}</div>'
    else:
        fx = (
            f'<div class="fx"><b>2 件套</b> {_mark_nums(data.effect2)}</div>'
            f'<div class="fx" style="margin-top:8px"><b>4 件套</b> {_mark_nums(data.effect4)}</div>'
        )
    cover = icons["cover"] if "cover" in icons else ""
    plist: list[str] = []
    for p in data.pieces:
        src = icons[p.icon] if p.icon in icons else ""
        plist.append(
            '<div class="prow">'
            f'<div class="pbox">{_img("", src)}</div>'
            "<div>"
            f'<div class="pslot">{_esc(p.slot)}</div>'
            f'<div class="pnm">{_esc(p.name)}</div>'
            f'<div class="pdesc">{_esc(p.description)}</div>'
            "</div></div>"
        )
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="mod" style="padding-top:18px">',
            f"{_img('bigicon', cover)}",
            f'<div class="hname" style="text-align:center;margin-top:8px">{_esc(data.name)}</div>',
            f'<div class="hchips" style="justify-content:center"><div class="chip gold">{_esc(stars)} 星</div></div>',
            "</div>",
            '<div class="mod">',
            _section("套装效果", "SET", accent),
            f'<div class="panel">{fx}</div>',
            "</div>",
            '<div class="mod">',
            _section("圣遗物部件", "PIECES", accent),
            f'<div class="panel"><div class="plist">{"".join(plist)}</div></div>',
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def render_artifact_card(text: str) -> str | bytes:
    name, _level = parse_query(text)
    data = await load_artifact_wiki(name)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    _ai_return_artifact(data)
    accent = GOLD
    icons: dict[str, str] = {}
    if data.icon:
        icons["cover"] = await _uri_icon(data.icon, 180)
    for p in data.pieces:
        if p.icon:
            local = REL_PATH / f"{p.name}.png"
            if local.exists():
                icons[p.icon] = _icon(local, 42)
            else:
                icons[p.icon] = await _uri_icon(p.icon, 42)
    inner = _artifact_html(data, accent, icons)
    bg = await _page_bg()
    img = await _render_page(accent, bg, inner)
    return await convert_img(img)


def _food_html(data: FoodWiki, accent: str, cover: str, icons: dict[str, str]) -> str:
    item_uris = {it.item_id: (icons[it.item_id] if it.item_id in icons else "") for it in data.ingredients}
    footer = _file_uri(FOOTER)
    buff = icons["buff"] if "buff" in icons else ""
    return "".join(
        [
            '<div class="mod" style="padding-top:16px">',
            f"{_img('bigicon', cover)}",
            '<div class="hchips" style="justify-content:center;margin-top:4px">',
            f"{_img('helem', buff)}",
            "</div>",
            f'<div class="hname" style="text-align:center;margin-top:6px">{_esc(data.name)}</div>',
            '<div class="hchips" style="justify-content:center">',
            f'<div class="chip gold">{_stars(data.rarity)}</div>',
            f'<div class="chip">{_esc(data.kind)}</div>',
            f'<div class="chip">{_esc(data.source)}</div>' if data.source else "",
            "</div></div>",
            '<div class="mod">',
            _section("效果", "EFFECT", accent),
            f'<div class="panel"><div class="fx">{_rich_html(data.effect)}</div></div>',
            "</div>",
            '<div class="mod">',
            _section("介绍", "LORE", accent),
            f'<div class="panel"><div class="fx">{_mark_glow(data.description)}</div></div>',
            "</div>",
            '<div class="mod">',
            _section("食材", "RECIPE", accent),
            f'<div class="panel">{_items_html(data.ingredients, item_uris)}</div>',
            "</div>",
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def render_food_card(text: str) -> str | bytes:
    name, _level = parse_query(text)
    data = await load_food_wiki(name)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    _ai_return_food(data)
    accent = "#77dd8f"
    cover = await _uri_icon(data.icon, 200)
    if not cover and data.food_id:
        cover = await _uri_icon(f"UI_ItemIcon_{data.food_id}", 200)
    icons: dict[str, str] = {}
    if data.effect_icon:
        icons["buff"] = await _uri_icon(data.effect_icon, 28)
    for it in data.ingredients:
        icons[it.item_id] = await _uri_item(it, 44)
    inner = _food_html(data, accent, cover, icons)
    bg = await _page_bg()
    img = await _render_page(accent, bg, inner)
    return await convert_img(img)


_SKIP_DROP_NAMES = {"摩拉", "冒险阅历", "好感经验"}


def _is_relic_drop(item: WikiItem) -> bool:
    return item.icon.startswith("UI_RelicIcon")


def _monster_drops(rewards: tuple[WikiItem, ...], icons: dict[str, str]) -> tuple[WikiItem, ...]:
    seen: set[str] = set()
    out: list[WikiItem] = []
    for it in rewards:
        if it.name in _SKIP_DROP_NAMES or it.rank < 3 or _is_relic_drop(it):
            continue
        if it.name in seen:
            continue
        src = icons[it.item_id] if it.item_id in icons else ""
        if not src:
            continue
        seen.add(it.name)
        out.append(it)
    return tuple(out)


def _res_html(entry_resists: tuple[tuple[str, float], ...]) -> str:
    bits: list[str] = []
    for lab, val in entry_resists:
        pct = val * 100
        color = _RES_COLOR[lab] if lab in _RES_COLOR else INK
        width = min(100.0, abs(pct))
        fill = "#63e2a4" if pct < 0 else color
        bits.append(
            '<div class="res">'
            f'<div class="rdot" style="background:{color}"></div>'
            f'<div class="rnm">{_esc(lab)}</div>'
            '<div class="rbar">'
            f'<div class="rfill" style="width:{width:.0f}%;background:{fill}"></div>'
            "</div>"
            f'<div class="rval">{pct:.0f}%</div>'
            "</div>"
        )
    return f'<div class="resgrid">{"".join(bits)}</div>'


def _monster_html(data: MonsterWiki, cover: str, accent: str, icons: dict[str, str]) -> str:
    footer = _file_uri(FOOTER)
    blocks: list[str] = []
    for i, ent in enumerate(data.entries[:4]):
        label = f"形态 {i + 1}" if len(data.entries) > 1 else "抗性"
        blocks.append(_section(label, "RESIST", accent, ent.entry_id))
        blocks.append(f'<div class="panel">{_res_html(ent.resists)}</div>')
        if ent.affixes:
            af = "".join(
                f'<div class="fx" style="margin-top:6px"><b>{_esc(a.name)}</b> {_mark_nums(a.description)}</div>'
                for a in ent.affixes[:8]
            )
            blocks.append(_section("词缀", "AFFIX", accent))
            blocks.append(f'<div class="panel">{af}</div>')
        notable = _monster_drops(ent.rewards, icons)
        if notable:
            uris = {it.item_id: (icons[it.item_id] if it.item_id in icons else "") for it in notable}
            blocks.append(_section("掉落", "DROP", accent))
            blocks.append(f'<div class="panel">{_items_html(notable, uris)}</div>')
    return "".join(
        [
            '<div class="mod" style="padding-top:16px">',
            f"{_img('bigicon', cover)}",
            f'<div class="hname" style="text-align:center;margin-top:6px">{_esc(data.name)}</div>',
            f'<div class="hsub" style="text-align:center">{_esc(data.special_name)} · {_esc(data.kind)}</div>',
            f'<div class="hdesc" style="padding:0 8px">{_rich_html(data.description)}</div>',
            "</div>",
            f'<div class="mod">{"".join(blocks)}</div>',
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def _monster_cover(icon: str) -> str:
    if not icon:
        return ""
    name = icon if icon.endswith(".png") else f"{icon}.png"
    cached = WIKI_DATA_MONSTER_ICON / name
    if not cached.exists():
        bundled = MONSTER_ICON_PATH / name
        if bundled.exists():
            _keep_wiki_file(bundled, cached)
        else:
            try:
                await get_ambr_icon("monster", icon.replace(".png", ""), WIKI_DATA_MONSTER_ICON)
            except Exception:
                return ""
    if not cached.exists():
        return ""
    return _icon(cached, 180)


async def render_monster_card(text: str) -> str | bytes:
    name, _level = parse_query(text)
    data = await load_monster_wiki(name)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    _ai_return_monster(data)
    accent = "#ec6a48"
    cover = await _monster_cover(data.icon)
    icons: dict[str, str] = {}
    for ent in data.entries[:4]:
        for it in ent.rewards:
            if it.item_id in icons or _is_relic_drop(it) or it.name in _SKIP_DROP_NAMES:
                continue
            icons[it.item_id] = await _uri_item(it, 44)
    inner = _monster_html(data, cover, accent, icons)
    bg = await _page_bg()
    img = await _render_page(accent, bg, inner)
    return await convert_img(img)


def _story_panel(block: FetterBlock) -> str:
    tip = f'<div class="stips">{_esc(block.tips)}</div>' if block.tips else ""
    body = _mark_glow(block.text)
    return f'<div class="panel"><div class="stitle">{_esc(block.title)}</div><div class="story">{body}</div>{tip}</div>'


def _pack_cols(items: list[str]) -> str:
    left = items[0::2]
    right = items[1::2]
    return f'<div class="cols"><div class="col">{"".join(left)}</div><div class="col">{"".join(right)}</div></div>'


def _fetter_hero(data: CharStoryWiki, hero: str) -> str:
    chips = [
        f'<div class="chip gold">{_stars(data.rarity)}</div>',
        f'<div class="chip">{_esc(data.element_zh)}</div>',
    ]
    if data.title:
        chips.append(f'<div class="chip">{_esc(data.title)}</div>')
    return (
        '<div class="hero">'
        f'<img class="herobg" src="{hero}"/>'
        '<div class="heroin">'
        '<div class="htitle">'
        f"{_img('helem', _elem_icon(data.element, 26))}"
        f'<div class="hname">{_esc(data.name)}</div>'
        "</div>"
        f'<div class="hchips">{"".join(chips)}</div>'
        "</div></div>"
    )


def _quote_row(idx: int, block: FetterBlock) -> str:
    tip = f'<div class="stips">{_esc(block.tips)}</div>' if block.tips else ""
    return (
        '<div class="qrow">'
        '<div class="qhead">'
        f'<div class="qidx">{idx}</div>'
        f'<div class="qtitle">{_esc(block.title)}</div>'
        "</div>"
        f'<div class="qtext">{_mark_glow(block.text)}</div>'
        f"{tip}"
        "</div>"
    )


def _pack_cols3(items: list[str]) -> str:
    cols: list[list[str]] = [[], [], []]
    for i, row in enumerate(items):
        cols[i % 3].append(row)
    bits: list[str] = []
    for col in cols:
        if not col:
            continue
        bits.append(f'<div class="col3"><div class="panel">{"".join(col)}</div></div>')
    return f'<div class="cols3">{"".join(bits)}</div>'


def _story_html(data: CharStoryWiki, hero: str, accent: str) -> str:
    hero_block = _fetter_hero(data, hero)
    stories = list(data.stories)
    first = _story_panel(stories[0]) if stories else '<div class="panel"><div class="fx">暂无故事</div></div>'
    rest = [_story_panel(b) for b in stories[1:]]
    rest_html = _pack_cols(rest) if rest else ""
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="toprow">',
            hero_block,
            '<div class="topmats">',
            _section(stories[0].title if stories else "角色详细", "PROFILE", accent),
            first,
            "</div></div>",
            '<div class="mod">',
            _section("角色故事", "STORY", accent, str(len(stories))),
            "</div>",
            rest_html,
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def render_story_card(text: str) -> str | bytes:
    return await _render_fetter_card(text, "story")


def _voice_html(data: CharStoryWiki, hero: str, accent: str) -> str:
    quotes = list(data.quotes)
    side_n = min(VOICE_SIDE, len(quotes))
    side = [_quote_row(i, b) for i, b in enumerate(quotes[:side_n], 1)]
    rest = [_quote_row(i, b) for i, b in enumerate(quotes[side_n:], side_n + 1)]
    if side:
        side_html = f'<div class="panel">{"".join(side)}</div>'
    else:
        side_html = '<div class="panel"><div class="fx">暂无语音</div></div>'
    extra = f"{len(quotes)} · 「角色语音{_esc(data.name)}N」收听" if quotes else ""
    rest_html = _pack_cols3(rest) if rest else ""
    footer = _file_uri(FOOTER)
    return "".join(
        [
            '<div class="toprow">',
            _fetter_hero(data, hero),
            '<div class="topmats">',
            _section("语音", "VOICE", accent, extra),
            side_html,
            "</div></div>",
            '<div class="mod">',
            _section("角色语音", "LINES", accent, str(len(quotes))),
            "</div>",
            rest_html,
            f'<div class="foot">{_img("", footer)}</div>',
        ]
    )


async def _render_fetter_card(text: str, kind: str) -> str | bytes:
    name, _level = parse_query(text)
    data = await load_char_story(name)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    if kind == "voice":
        if not data.quotes:
            msg = f"未找到角色「{data.name}」的语音。"
            _ai_return_msg(msg)
            return msg
        _ai_return_voice(data)
        inner_fn = _voice_html
    else:
        if not data.stories:
            msg = f"未找到角色「{data.name}」的故事。"
            _ai_return_msg(msg)
            return msg
        _ai_return_story(data)
        inner_fn = _story_html
    accent = _accent(data.element)
    splash = _load_splash(data.name, data.char_id, data.icon)
    if data.icon:
        path = await _asset_path(data.icon)
        if path is not None and splash.size[0] < 80:
            splash = Image.open(path).convert("RGBA")
    hero = await _build_hero(splash, accent, PAGE_W, CHAR_HERO_H, CHAR_ART_W)
    inner = inner_fn(data, hero, accent)
    bg = await _page_bg(CHAR_W)
    img = await _render_page(accent, bg, inner, CHAR_W)
    return await convert_img(img)


async def render_voice_card(text: str) -> str | bytes:
    return await _render_fetter_card(text, "voice")


async def render_voice_audio(text: str) -> str | tuple[str, Path]:
    name, index = parse_voice_query(text)
    if index is None:
        msg = "请在角色名后加上语音编号，例如「角色语音可莉3」。"
        _ai_return_msg(msg)
        return msg
    data = await load_char_story(name)
    if isinstance(data, str):
        _ai_return_msg(data)
        return data
    if not data.quotes:
        msg = f"未找到角色「{data.name}」的语音。"
        _ai_return_msg(msg)
        return msg
    result = await load_voice_file(data, index)
    if isinstance(result, str):
        _ai_return_msg(result)
        return result
    path, block = result
    _ai_return_msg(quote_line_text(data, block, index))
    return f"{index}. {block.title}", path
