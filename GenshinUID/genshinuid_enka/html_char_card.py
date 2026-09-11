"""原神角色面板竖版一图流：立绘题头 + 总览条 + 武器/圣遗物三列宫格 + 伤害表。

左列 640 CSS 宽，dpr=4 出 2560 宽实图（2K）。有 Akasha 配装数据时右侧再拼 640，
合计 1280 CSS / 5120 实图（伤害分布 + 副词条收益 + 队伍榜）。位图按 ``SCALE`` 栅格化后缩回 CSS。
"""

from __future__ import annotations

import html
import json
import base64
import random
from io import BytesIO
from typing import Mapping
from pathlib import Path
from dataclasses import dataclass

from PIL import Image
from httpx import get

from gsuid_core.pool import to_thread
from gsuid_core.utils.html_render import _ensure_renderer, render_html_to_bytes
from gsuid_core.utils.download_resource.download_image import get_image

from .etc.etc import TEXT_PATH, get_all_artifacts_value
from .hero_art import (
    hex_rgb,
    radar_svg,
    compose_hero,
    draw_con_arc,
    talent_icons,
    con_arc_points,
    compose_page_bg,
    split_dmg_label,
    talent_unlocked,
)
from .akasha_side import SIDE_W, akasha_side_css, akasha_side_html
from .draw_normal import get_artifact_score_data
from .akasha_store import load_akasha_side
from .etc.MAP_PATH import avatarName2SkillAdd
from .etc.base_info import ELEMENT_TEXT_MAP
from .artifact_times import max_sub_roll, substat_rolls, substat_times, substat_is_max
from .mono.Character import Character
from .dmg_calc.dmg_calc import get_char_dmg_percent
from ..utils.api.cv.models import (
    GlobalRankRow,
    BuildLeaderboardRow,
    SubstatPriorityBoard,
    DamageDistributionBoard,
)
from ..utils.map.GS_MAP_PATH import (
    CharId2TalentIcon_data,
    weaponId2Name_data,
    enName_to_avatarId_data,
)
from ..utils.fonts.genshin_fonts import FONT_ORIGIN_PATH
from ..genshinuid_config.gs_config import gsconfig
from ..utils.resource.element_icon import element_icon_path
from ..utils.resource.RESOURCE_PATH import (
    REL_PATH,
    CHAR_PATH,
    ICON_PATH,
    WEAPON_PATH,
    CU_CHBG_PATH,
    GACHA_IMG_PATH,
)

AkashaSideInject = tuple[
    list[SubstatPriorityBoard],
    list[BuildLeaderboardRow],
    list[DamageDistributionBoard],
    list[GlobalRankRow],
]

TEX2D_PATH = Path(__file__).resolve().parents[1] / "utils" / "resource" / "texture2d"
_AKASHA_PATH = Path(__file__).resolve().parent / "effect" / "akasha_1p_avg.json"
RADAR_W = 196

SCALE = 4
PAGE_W = 640
PAGE_BG_H = 1640
PAD = 12
INNER_W = PAGE_W - PAD * 2
BANNER_H = 66
AVATAR_CSS = 48
HERO_W = PAGE_W
HERO_H = 408
ART_W = 332
ART_FADE = 160
HERO_TXT_L = ART_W - 18 + PAD
HERO_TXT_W = HERO_W - HERO_TXT_L - PAD
STAT_W = HERO_TXT_W - 20
SK_GAP = 6
STAT_VAL_W = 78
STAT_DELTA_W = 54
CON_SIZE = 44
CON_GAP = 16
CON_TOP = 50
CON_SPAN = (6 - 1) * (CON_SIZE + CON_GAP)
CON_LEFT = 10
CON_BOW = 70
CON_ICON = 32
CON_RAIL_W = CON_LEFT + CON_BOW + CON_SIZE + 10
HEAD_H = BANNER_H + HERO_H
GRID_GAP = 8
CARD_W = (INNER_W - GRID_GAP * 2) // 3
CARD_H = 184
DMG_W = INNER_W - 20
DMG_VAL_W = 114
DMG_NAME_W = DMG_W - DMG_VAL_W * 3

BODY_FONT = "'MiSans','YuanShen',sans-serif"
NUM_FONT = "'YuanShen','MiSans',sans-serif"
INK = "#f2f5fb"
INK_2 = "rgba(242,245,251,0.62)"
INK_3 = "rgba(242,245,251,0.34)"
GOLD = "#eac683"
UP = "#63e2a4"
# 评分档色统一走十六进制：会喂给 _rgba() 算辉光，rgba 字符串会解析失败
NEUTRAL = "#98a1b2"
SURFACE = "linear-gradient(180deg,rgba(10,12,20,0.42) 0%,rgba(8,10,16,0.56) 100%)"
HAIR = "rgba(255,255,255,0.08)"
HAIR_TOP = "rgba(255,255,255,0.18)"

_FLAT_STATS = {"攻击力", "血量", "防御力", "元素精通", "基础攻击力", "基础防御力", "基础血量"}
# 词条短名：宫格里一行要塞下评分 / 图标 / 名称 / 尖角 / 数值，长名放不下
_SHORT_NAME: dict[str, str] = {
    "血量": "小生命",
    "百分比血量": "大生命",
    "攻击力": "小攻击",
    "百分比攻击力": "大攻击",
    "防御力": "小防御",
    "百分比防御力": "大防御",
    "暴击率": "暴击",
    "暴击伤害": "爆伤",
    "元素精通": "精通",
    "元素充能效率": "充能",
    "治疗加成": "治疗",
    "物理伤害加成": "物伤",
}
_ACCENT: dict[str, str] = {
    "Anemo": "#3fd6c8",
    "Cryo": "#79d4ec",
    "Dendro": "#77dd8f",
    "Electro": "#b98cf5",
    "Geo": "#e5a93f",
    "Hydro": "#43b6ee",
    "Pyro": "#ec6a48",
}
_STAT_CAP: dict[str, float] = {
    "hp": 42000,
    "atk": 3600,
    "def": 2400,
    "em": 1000,
    "crit": 100,
    "cdmg": 260,
    "er": 250,
    "dmg": 100,
    "phys": 100,
    "heal": 60,
}
_TIER_COLOR: dict[int, str] = {
    0: "rgba(242,245,251,0.44)",
    1: "rgba(242,245,251,0.38)",
    2: "rgba(242,245,251,0.68)",
    3: "#8fb4ff",
    4: "#eac683",
}
_STAR_TINT: dict[int, tuple[str, str]] = {
    5: ("rgba(198,152,80,0.32)", "rgba(214,168,92,0.58)"),
    4: ("rgba(150,120,196,0.30)", "rgba(166,134,214,0.55)"),
    3: ("rgba(96,146,190,0.28)", "rgba(112,162,206,0.50)"),
}

_URI: dict[str, str] = {}
_YS_READY = False
_AKASHA: dict[int, list[dict[str, object]]] | None = None
_RADAR_AXES: tuple[tuple[str, str, str], ...] = (
    ("maxHp", "生命", "hp"),
    ("atk", "攻击", "atk"),
    ("def", "防御", "def"),
    ("elementalMastery", "精通", "elementalMastery"),
    ("energyRecharge", "充能", "energyRecharge"),
    ("critRate", "暴击", "critRate"),
    ("critDamage", "爆伤", "critDmg"),
)
_RADAR_PCT = {"energyRecharge", "critRate", "critDamage"}
_CHIP_TO_STAT: dict[str, str] = {
    "暴击伤害": "暴击伤害",
    "暴击率": "暴击率",
    "元素充能效率": "元素充能",
    "元素精通": "元素精通",
    "攻击力": "攻击力",
    "百分比攻击力": "攻击力",
    "血量": "生命值",
    "百分比血量": "生命值",
    "防御力": "防御力",
    "百分比防御力": "防御力",
    "治疗加成": "治疗加成",
}


@dataclass(frozen=True)
class _StatRow:
    name: str
    icon: str
    total: str
    delta: str
    ratio: float


@dataclass(frozen=True)
class _SubRow:
    name: str
    value: str
    icon: str
    raw: float
    times: int | None
    rolls: list[int] | None
    is_max: bool | None
    score: float


@dataclass(frozen=True)
class _SumChip:
    icon: str
    value: str
    count: int
    useful: bool


@dataclass(frozen=True)
class _ArtiView:
    name: str
    piece: str
    icon: str
    star: int
    level: int
    main_name: str
    main_value: str
    subs: list[_SubRow]
    value_score: float
    cv_score: float


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


def _jpeg_uri(img: Image.Image, quality: int = 86) -> str:
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
    elif suffix == ".webp":
        mime = "image/webp"
    uri = f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    _URI[key] = uri
    return uri


def _icon(path: Path, css_size: int, *, trim: bool = False) -> str:
    """按 dpr 倍率栅格化，CSS 侧再缩回 ``css_size``，避免高清屏糊。"""
    if not path.exists():
        return ""
    px = css_size * SCALE
    key = f"resize:{path}:{px}:trim={trim}"
    if key in _URI:
        return _URI[key]
    img = Image.open(path).convert("RGBA")
    if trim:
        box = img.getbbox()
        if box is not None:
            img = img.crop(box)
    img = img.resize((px, px), Image.Resampling.LANCZOS)
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


def _talent_icon(name: str, css_size: int) -> str:
    """命座是浅色线稿，抬一下 alpha 再缩，否则 22px 圆里只剩灰点。"""
    path = ICON_PATH / f"{name}.png"
    if not path.exists():
        return ""
    px = css_size * SCALE
    key = f"talent:{path}:{px}"
    if key in _URI:
        return _URI[key]
    img = Image.open(path).convert("RGBA")
    r, g, b, a = img.split()
    a = a.point(lambda v: min(255, int(v * 1.65)) if v else 0)
    img = Image.merge("RGBA", (r, g, b, a)).resize((px, px), Image.Resampling.LANCZOS)
    uri = _png_uri(img)
    _URI[key] = uri
    return uri


def _esc(text: str) -> str:
    return html.escape(text)


def _accent(element: str) -> str:
    if element in _ACCENT:
        return _ACCENT[element]
    return "#8ec8f0"


def _rgba(color: str, alpha: float) -> str:
    r, g, b = hex_rgb(color)
    return f"rgba({r},{g},{b},{alpha})"


def _ratio_to_pct(value: float) -> float:
    if value > 10:
        return value
    return value * 100


def _fmt_int(value: float) -> str:
    return f"{int(round(value)):,}"


def _fmt_pct(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def _fmt_stat_value(name: str, value: float) -> str:
    if name in _FLAT_STATS:
        return _fmt_int(value)
    return _fmt_pct(value)


def _short(name: str) -> str:
    if name in _SHORT_NAME:
        return _SHORT_NAME[name]
    if name.endswith("元素伤害加成"):
        return f"{name[0]}伤"
    return name.replace("百分比", "")


def _fight_num(fight: Mapping[str, object], key: str, default: float = 0.0) -> float:
    if key not in fight:
        return default
    raw = fight[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return default
    return float(raw)


def _card_str(card: Mapping[str, object], key: str, default: str = "") -> str:
    if key not in card:
        return default
    raw = card[key]
    if isinstance(raw, str):
        return raw
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return str(raw)
    return default


def _card_int(card: Mapping[str, object], key: str, default: int = 0) -> int:
    if key not in card:
        return default
    raw = card[key]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return default
    return int(raw)


def _wpn_stat_icon(name: str, css_size: int) -> str:
    key = name[2:] if name.startswith("基础") else name
    return _stat_icon(key, css_size)


def _load_splash_image(char: Character, char_url: str | None) -> Image.Image:
    if char.char_bytes is not None:
        return Image.open(BytesIO(char.char_bytes)).convert("RGBA")
    if gsconfig.get_config("RandomPic").data and char_url is None:
        folder = CU_CHBG_PATH / char.char_name
        if folder.exists():
            files = [p for p in folder.iterdir() if p.is_file()]
            if files:
                picked = random.choice(files)
                raw = picked.read_bytes()
                char.char_bytes = raw
                return Image.open(BytesIO(raw)).convert("RGBA")
    if char_url:
        payload = get(char_url, follow_redirects=True)
        char.char_bytes = payload.content
        return Image.open(BytesIO(payload.content)).convert("RGBA")
    gacha = GACHA_IMG_PATH / f"{char.char_name}.png"
    if gacha.exists():
        return Image.open(gacha).convert("RGBA")
    portrait = CHAR_PATH / f"{char.char_id}.png"
    if portrait.exists():
        return Image.open(portrait).convert("RGBA")
    return Image.new("RGBA", (ART_W * SCALE, HERO_H * SCALE), (18, 12, 32, 255))


def _compose_hero(splash: Image.Image, accent: str) -> Image.Image:
    hero = compose_hero(splash, accent, SCALE, HERO_W, HERO_H, ART_W + PAD, ART_FADE, HERO_TXT_L)
    arc = draw_con_arc(SCALE, CON_RAIL_W, HERO_H, CON_TOP, CON_SPAN, CON_LEFT, CON_BOW, CON_SIZE, accent)
    out = hero.convert("RGBA")
    out.alpha_composite(arc, (0, 0))
    return out


@to_thread
def _build_hero(splash: Image.Image, accent: str) -> str:
    return _png_uri(_compose_hero(splash, accent))


@to_thread
def _build_page_bg(splash: Image.Image, accent: str, width: int = PAGE_W) -> str:
    return _jpeg_uri(compose_page_bg(splash, accent, SCALE, width, PAGE_BG_H), 82)


def _stat_icon(name: str, css_size: int) -> str:
    elem = element_icon_path(name)
    if elem is not None:
        return _icon(elem, css_size)
    return _icon(TEXT_PATH / "icon" / f"{name}.png", css_size, trim=True)


def _elem_icon(element: str, css_size: int) -> str:
    path = element_icon_path(element)
    if path is None:
        return ""
    return _icon(path, css_size)


def _badge(path: Path, css_h: int) -> str:
    if not path.exists():
        return ""
    src = Image.open(path).convert("RGBA")
    sw, sh = src.size
    if sh <= 0:
        return ""
    css_w = max(1, round(css_h * sw / sh))
    px_w, px_h = css_w * SCALE, css_h * SCALE
    key = f"badge:{path}:{px_w}x{px_h}"
    if key in _URI:
        uri = _URI[key]
    else:
        uri = _png_uri(src.resize((px_w, px_h), Image.Resampling.LANCZOS))
        _URI[key] = uri
    return f'<img class="hbadge" style="width:{css_w}px;height:{css_h}px" src="{uri}"/>'


def _fetter_badge(level: int) -> str:
    return _badge(TEX2D_PATH / "hg" / f"{min(10, max(0, level))}.png", 26)


def _talent_badge(unlocked: int) -> str:
    return _badge(TEX2D_PATH / "mz" / f"{min(6, max(0, unlocked))}.png", 26)


def _img(cls: str, src: str) -> str:
    if not src:
        return ""
    return f'<img class="{cls}" src="{src}"/>'


def _build_stat_rows(card: Mapping[str, object], element: str) -> list[_StatRow]:
    if "avatarFightProp" not in card:
        return []
    fight_raw = card["avatarFightProp"]
    if not isinstance(fight_raw, dict):
        return []
    fight: Mapping[str, object] = fight_raw
    hp = _fight_num(fight, "hp")
    atk = _fight_num(fight, "atk")
    defense = _fight_num(fight, "def")
    add_hp = hp - _fight_num(fight, "baseHp")
    add_atk = atk - _fight_num(fight, "baseAtk")
    add_def = defense - _fight_num(fight, "baseDef")
    em = _fight_num(fight, "elementalMastery")
    crit = _ratio_to_pct(_fight_num(fight, "critRate"))
    cdmg = _ratio_to_pct(_fight_num(fight, "critDmg"))
    er = _ratio_to_pct(_fight_num(fight, "energyRecharge"))
    phys = _ratio_to_pct(_fight_num(fight, "physicalDmgBonus"))
    ele = _ratio_to_pct(_fight_num(fight, "dmgBonus"))
    heal = _ratio_to_pct(_fight_num(fight, "healBonus"))
    ele_zh = ELEMENT_TEXT_MAP[element] if element in ELEMENT_TEXT_MAP else ""
    return [
        _StatRow("生命值", "血量", _fmt_int(hp), f"+{_fmt_int(add_hp)}", hp / _STAT_CAP["hp"]),
        _StatRow("攻击力", "攻击力", _fmt_int(atk), f"+{_fmt_int(add_atk)}", atk / _STAT_CAP["atk"]),
        _StatRow("防御力", "防御力", _fmt_int(defense), f"+{_fmt_int(add_def)}", defense / _STAT_CAP["def"]),
        _StatRow("元素精通", "元素精通", _fmt_int(em), "", em / _STAT_CAP["em"]),
        _StatRow("暴击率", "暴击率", _fmt_pct(crit), "", crit / _STAT_CAP["crit"]),
        _StatRow("暴击伤害", "暴击伤害", _fmt_pct(cdmg), "", cdmg / _STAT_CAP["cdmg"]),
        _StatRow("元素充能", "元素充能效率", _fmt_pct(er), "", er / _STAT_CAP["er"]),
        _StatRow(f"{ele_zh}元素伤害", f"{ele_zh}元素伤害加成", _fmt_pct(ele), "", ele / _STAT_CAP["dmg"]),
        _StatRow("物理伤害", "物理伤害加成", _fmt_pct(phys), "", phys / _STAT_CAP["phys"]),
        _StatRow("治疗加成", "治疗加成", _fmt_pct(heal), "", heal / _STAT_CAP["heal"]),
    ]


def _skill_levels(card: Mapping[str, object], char_name: str) -> list[tuple[str, str, int, bool, str]]:
    if "avatarSkill" not in card:
        return []
    raw = card["avatarSkill"]
    if not isinstance(raw, list):
        return []
    if char_name in avatarName2SkillAdd:
        skill_add = avatarName2SkillAdd[char_name]
    else:
        skill_add = ["E", "Q"]
    talents = 0
    if "talentList" in card and isinstance(card["talentList"], list):
        talents = len(card["talentList"])
    bonus = {"A": 0, "E": 0, "Q": 0}
    for idx in range(0, 2):
        if talents >= 3 + idx * 2 and idx < len(skill_add):
            key = skill_add[idx]
            if key in bonus:
                bonus[key] += 3
    slots = ["普攻", "战技", "爆发", "特殊"]
    out: list[tuple[str, str, int, bool, str]] = []
    n = 0
    for item in raw:
        if not isinstance(item, dict):
            continue
        if "skillIcon" not in item or "skillLevel" not in item:
            continue
        icon = item["skillIcon"]
        level = item["skillLevel"]
        if not isinstance(icon, str) or not isinstance(level, int):
            continue
        extra = 0
        kind = ""
        if n == 0:
            extra = bonus["A"]
            kind = "A"
        elif n == 1:
            extra = bonus["E"]
            kind = "E"
        elif n == 2:
            extra = bonus["Q"]
            kind = "Q"
        out.append((slots[n] if n < len(slots) else "", icon, level + extra, extra > 0, kind))
        n += 1
        if n >= 3:
            break
    return out


def _talent_unlocked(card: Mapping[str, object]) -> int:
    return talent_unlocked(card)


def _talent_icons(char_id: str, element: str = "") -> list[str]:
    return talent_icons(char_id, CharId2TalentIcon_data, element)


async def _score_artifacts(char: Character) -> list[_ArtiView]:
    if "equipList" not in char.card_prop:
        return []
    raw = char.card_prop["equipList"]
    if not isinstance(raw, list):
        return []
    views: list[_ArtiView] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        scored = await get_artifact_score_data(item, char)
        if "aritifactName" not in scored:
            continue
        name = scored["aritifactName"]
        if not isinstance(name, str):
            continue
        piece = scored["aritifactPieceName"] if "aritifactPieceName" in scored else ""
        star = scored["aritifactStar"] if "aritifactStar" in scored else 5
        level = scored["aritifactLevel"] if "aritifactLevel" in scored else 0
        main = scored["reliquaryMainstat"] if "reliquaryMainstat" in scored else {}
        main_name = ""
        main_value = ""
        if isinstance(main, dict) and "statName" in main and "statValue" in main:
            mn = main["statName"]
            mv = main["statValue"]
            if isinstance(mn, str) and isinstance(mv, (int, float)) and not isinstance(mv, bool):
                main_name = mn
                main_value = _fmt_stat_value(mn, float(mv))
        subs: list[_SubRow] = []
        if "reliquarySubstats" in scored and isinstance(scored["reliquarySubstats"], list):
            for sub in scored["reliquarySubstats"]:
                if not isinstance(sub, dict):
                    continue
                if "statName" not in sub or "statValue" not in sub:
                    continue
                sn = sub["statName"]
                sv = sub["statValue"]
                if not isinstance(sn, str) or not isinstance(sv, (int, float)) or isinstance(sv, bool):
                    continue
                score = 0.0
                if "value_score" in sub and isinstance(sub["value_score"], (int, float)):
                    score = float(sub["value_score"])
                subs.append(
                    _SubRow(
                        name=_short(sn),
                        value=_fmt_stat_value(sn, float(sv)),
                        icon=sn,
                        raw=float(sv),
                        times=substat_times(sub),
                        rolls=substat_rolls(sub),
                        is_max=substat_is_max(sub),
                        score=score,
                    )
                )
        vs = 0.0
        if "value_score" in scored and isinstance(scored["value_score"], (int, float)):
            vs = float(scored["value_score"])
        cv = 0.0
        if "cv_score" in scored and isinstance(scored["cv_score"], (int, float)):
            cv = float(scored["cv_score"])
        views.append(
            _ArtiView(
                name=name,
                piece=piece if isinstance(piece, str) else "",
                icon=name,
                star=int(star) if isinstance(star, (int, float)) else 5,
                level=int(level) if isinstance(level, (int, float)) else 0,
                main_name=main_name,
                main_value=main_value,
                subs=subs,
                value_score=vs,
                cv_score=cv,
            )
        )
    return views


def _set_label(card: Mapping[str, object]) -> str:
    counts: dict[str, int] = {}
    if "equipList" in card and isinstance(card["equipList"], list):
        for item in card["equipList"]:
            if not isinstance(item, dict) or "aritifactSetsName" not in item:
                continue
            name = item["aritifactSetsName"]
            if not isinstance(name, str) or not name:
                continue
            counts[name] = counts[name] + 1 if name in counts else 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    # 只报成套的；单件不触发套装效果，写出来只会把横条挤爆
    parts = [f"{name}·{n}" for name, n in ranked if n >= 2]
    if parts:
        return " ".join(parts)
    return "散件"


def _grade(score: float) -> tuple[str, str]:
    if score >= 46:
        return "SSS", "#ef6b6b"
    if score >= 40:
        return "SS", GOLD
    if score >= 34:
        return "S", "#c48ef0"
    if score >= 28:
        return "A", "#8fb4ff"
    if score >= 22:
        return "B", "#7fd3a4"
    return "C", NEUTRAL


def _score_color(score: float, kind: str) -> str:
    if kind == "cv":
        if score >= 50:
            return "#ef6b6b"
        if score >= 45:
            return GOLD
        if score >= 39:
            return "#c48ef0"
        return NEUTRAL
    if score >= 7.2:
        return "#ef6b6b"
    if score >= 6.0:
        return "#ffb056"
    if score >= 4.5:
        return "#c48ef0"
    if score >= 3.0:
        return "#f2f5fb"
    return "#8b919c"


def _sub_badge_tone(score: float, useful: bool) -> tuple[str, str, str]:
    """有效词条红>橙>紫>蓝>绿；无效词条灰底压暗。顶两档对齐旧面板 4.5 / 3.4。"""
    if not useful:
        return "#b4bac2", "rgba(88,94,104,0.62)", "rgba(128,134,144,0.38)"
    if score >= 4.5:
        return "#ff8b8b", "rgba(239,107,107,0.32)", "rgba(239,107,107,0.62)"
    if score >= 3.4:
        return "#ffb056", "rgba(245,161,74,0.30)", "rgba(245,161,74,0.60)"
    if score >= 2.2:
        return "#d4a8ff", "rgba(196,142,240,0.28)", "rgba(196,142,240,0.56)"
    if score >= 1.0:
        return "#9ec8ff", "rgba(126,182,255,0.26)", "rgba(126,182,255,0.52)"
    return "#7fdbb0", "rgba(111,212,160,0.22)", "rgba(111,212,160,0.44)"


def _useful_count(artis: list[_ArtiView]) -> tuple[int, int]:
    hit = 0
    total = 0
    for arti in artis:
        for sub in arti.subs:
            total += 1
            if sub.score > 0:
                hit += 1
    return hit, total


def _roll_stats(artis: list[_ArtiView]) -> tuple[int, int, int]:
    """返回（总掷骰次数, 4 档次数, 满词条数）；无掷骰明细时总数为 0。"""
    total = 0
    tier4 = 0
    maxed = 0
    for arti in artis:
        for sub in arti.subs:
            if sub.rolls:
                total += len(sub.rolls)
                tier4 += sum(1 for r in sub.rolls if r == 4)
            elif sub.times is not None:
                total += sub.times + 1
            if sub.is_max:
                maxed += 1
    return total, tier4, maxed


def _stars(n: int) -> str:
    return "★" * min(5, max(0, n))


def _star_tint(star: int) -> tuple[str, str]:
    if star in _STAR_TINT:
        return _STAR_TINT[star]
    return _STAR_TINT[3]


_SUM_ORDER: tuple[str, ...] = (
    "暴击伤害",
    "暴击率",
    "百分比攻击力",
    "攻击力",
    "元素充能效率",
    "元素精通",
    "百分比血量",
    "血量",
    "百分比防御力",
    "防御力",
    "治疗加成",
)


def _sub_roll_n(sub: _SubRow) -> int:
    if sub.rolls:
        return len(sub.rolls)
    if sub.times is not None:
        return sub.times + 1
    return 1


def _sub_totals(artis: list[_ArtiView]) -> tuple[list[_SumChip], int, float]:
    raws: dict[str, float] = {}
    counts: dict[str, int] = {}
    scores: dict[str, float] = {}
    for arti in artis:
        for sub in arti.subs:
            if sub.icon in raws:
                raws[sub.icon] += sub.raw
                counts[sub.icon] += _sub_roll_n(sub)
                scores[sub.icon] += sub.score
            else:
                raws[sub.icon] = sub.raw
                counts[sub.icon] = _sub_roll_n(sub)
                scores[sub.icon] = sub.score
    chips: list[_SumChip] = []
    seen: set[str] = set()
    rv = 0.0
    rolls_n = 0
    for key in _SUM_ORDER:
        if key not in raws or raws[key] <= 0:
            continue
        seen.add(key)
        n = counts[key]
        rolls_n += n
        cap = max_sub_roll(key)
        if cap > 0:
            rv += raws[key] / cap * 100
        chips.append(
            _SumChip(
                icon=key,
                value=_fmt_stat_value(key, raws[key]),
                count=n,
                useful=scores[key] > 0,
            )
        )
    for key, val in raws.items():
        if key in seen or val <= 0:
            continue
        n = counts[key]
        rolls_n += n
        cap = max_sub_roll(key)
        if cap > 0:
            rv += val / cap * 100
        chips.append(
            _SumChip(
                icon=key,
                value=_fmt_stat_value(key, val),
                count=n,
                useful=scores[key] > 0,
            )
        )
    return chips, rolls_n, rv


def _hot_stat_names(chips: list[_SumChip]) -> set[str]:
    out: set[str] = set()
    for chip in chips:
        if not chip.useful:
            continue
        if chip.icon in _CHIP_TO_STAT:
            out.add(_CHIP_TO_STAT[chip.icon])
        elif chip.icon.endswith("元素伤害加成"):
            out.add(chip.icon[:-2])
    return out


def _sub_beam_style(score: float, useful: bool) -> str:
    if not useful:
        return "display:none;"
    if score >= 4.5:
        return (
            "display:block;background:linear-gradient(90deg,rgba(239,107,107,0.72) 0%,"
            "rgba(239,107,107,0.28) 30%,rgba(239,107,107,0) 78%);"
            "box-shadow:0 0 4px rgba(239,107,107,0.45);"
        )
    if score >= 3.4:
        return (
            "display:block;background:linear-gradient(90deg,rgba(255,176,86,0.70) 0%,"
            "rgba(245,161,74,0.26) 30%,rgba(234,198,131,0) 78%);"
            "box-shadow:0 0 4px rgba(255,168,80,0.38);"
        )
    if score >= 2.2:
        return (
            "display:block;background:linear-gradient(90deg,rgba(196,142,240,0.62) 0%,"
            "rgba(196,142,240,0.24) 30%,rgba(196,142,240,0) 78%);"
            "box-shadow:0 0 4px rgba(196,142,240,0.34);"
        )
    return (
        "display:block;background:linear-gradient(90deg,rgba(255,255,255,0.42) 0%,"
        "rgba(255,255,255,0.16) 28%,rgba(255,255,255,0) 78%);"
        "box-shadow:0 0 3px rgba(255,255,255,0.18);"
    )


def _chevron(rank: int) -> str:
    color = _TIER_COLOR[rank] if rank in _TIER_COLOR else _TIER_COLOR[0]
    return f'<span class="cv1" style="color:{color}">›</span>'


def _chevrons(sub: _SubRow) -> str:
    """一个尖角 = 一次成功强化，颜色按该次掷骰档位（1–4）。"""
    if sub.rolls:
        ranks = sub.rolls[1:]
    elif sub.times is not None:
        ranks = [0] * sub.times
    else:
        return '<div class="chev none">?</div>'
    if not ranks:
        return '<div class="chev"></div>'
    return f'<div class="chev">{"".join(_chevron(r) for r in ranks[:5])}</div>'


def _sub_row(sub: _SubRow) -> str:
    useful = sub.score > 0
    cls = "srow on" if useful else "srow off"
    value = sub.value if sub.value.startswith("+") else f"+{sub.value}"
    ink, fill, edge = _sub_badge_tone(sub.score, useful)
    special = useful and sub.score >= 2.2
    glow = f"text-shadow:0 0 8px {_rgba(ink, 0.5)};" if special else ""
    if special:
        name_st = f"color:{ink};font-weight:700;"
        val_st = f"color:{ink};font-weight:700;{glow}"
    elif useful:
        name_st = "color:#f6f8fc;font-weight:700;"
        val_st = "color:#f7f9fd;font-weight:700;"
    else:
        name_st = ""
        val_st = ""
    return (
        f'<div class="{cls}">'
        f'<div class="ssb" style="color:{ink};background:{fill};border-color:{edge}">{sub.score:.1f}</div>'
        '<div class="srest">'
        f'<div class="sbeam" style="{_sub_beam_style(sub.score, useful)}"></div>'
        f'<img class="sic" src="{_stat_icon(sub.icon, 16)}"/>'
        f'<div class="snm" style="{name_st}">{_esc(sub.name)}</div>'
        f"{_chevrons(sub)}"
        f'<div class="sv" style="{val_st}">{_esc(value)}</div>'
        "</div></div>"
    )


def _arti_card(arti: _ArtiView, accent: str) -> str:
    soft, edge = _star_tint(arti.star)
    color = _score_color(arti.value_score, "v")
    rows = "".join(_sub_row(sub) for sub in arti.subs[:4])
    return (
        f'<div class="card">'
        f'<div class="cwm" style="background:{soft};border-color:{edge}">'
        f'<img src="{_icon(REL_PATH / f"{arti.icon}.png", 56)}"/>'
        f'<div class="clv">+{arti.level}</div></div>'
        '<div class="chead">'
        f'<div class="cname">{_esc(arti.name)}</div>'
        f'<div class="cscore"><span class="csv" style="color:{color};'
        f'text-shadow:0 0 14px {_rgba(color, 0.5)}">{arti.value_score:.1f}</span>'
        f'<span class="csl" style="color:{color}">词条</span>'
        f'<span class="csc" style="color:{color}">{arti.cv_score:.1f} CV</span></div>'
        "</div>"
        f'<div class="cmain">{_img("cmic", _stat_icon(arti.main_name, 18))}'
        f'<span class="cmn">{_esc(_short(arti.main_name))}</span>'
        f'<span class="cmv" style="color:{accent};text-shadow:0 0 16px {_rgba(accent, 0.55)}">'
        f"{_esc(arti.main_value)}</span></div>"
        f'<div class="csubs">{rows}</div>'
        "</div>"
    )


def _weapon_card(card: Mapping[str, object], accent: str) -> str:
    if "weaponInfo" not in card or not isinstance(card["weaponInfo"], dict):
        return '<div class="card"></div>'
    wpn = card["weaponInfo"]
    name = _card_str(wpn, "weaponName", "武器")
    star = int(_fight_num(wpn, "weaponStar", 1))
    soft, edge = _star_tint(star)
    affix = int(_fight_num(wpn, "weaponAffix", 1))
    effect = _card_str(wpn, "weaponEffect", "无特效。")
    pills: list[str] = []
    stats = wpn["weaponStats"] if "weaponStats" in wpn and isinstance(wpn["weaponStats"], list) else []
    for item in stats[:2]:
        if not isinstance(item, dict) or "statName" not in item or "statValue" not in item:
            continue
        sn = item["statName"]
        sv = item["statValue"]
        if not isinstance(sn, str) or not isinstance(sv, (int, float)) or isinstance(sv, bool):
            continue
        pills.append(
            f'<div class="wp">{_img("wpic", _wpn_stat_icon(sn, 16))}'
            f"<span>{_esc(sn.replace('百分比', ''))}</span>"
            f'<b style="color:{accent}">{_esc(_fmt_stat_value(sn, float(sv)))}</b></div>'
        )
    return (
        f'<div class="card">'
        f'<div class="cwm" style="background:{soft};border-color:{edge}">'
        f'<img src="{_icon(WEAPON_PATH / f"{name}.png", 56)}"/>'
        f'<div class="clv">Lv.{_card_str(wpn, "weaponLevel", "1")}</div></div>'
        '<div class="chead">'
        f'<div class="cname">{_esc(name)}</div>'
        f'<div class="cstar">{_stars(star)}</div>'
        f'<div class="cscore"><span class="wr" style="background:{_rgba(accent, 0.24)};'
        f'color:{accent}">精{affix}</span>'
        f'<span class="csc">{_esc(_card_str(wpn, "weaponType"))}</span></div>'
        "</div>"
        f'<div class="wps">{"".join(pills)}</div>'
        f'<div class="wdesc">{_esc(effect)}</div>'
        "</div>"
    )


def _hero_html(
    hero_uri: str,
    char: Character,
    accent: str,
    stats: list[_StatRow],
    skills: list[tuple[str, str, int, bool, str]],
    talents: list[str],
    unlocked: int,
    hot: set[str],
    data_time: str = "",
) -> str:
    lock = _icon(TEXT_PATH / "icon_lock.png", 18)
    eicon = _elem_icon(char.char_element, 28)
    fetter_raw = char.char_fetter
    if isinstance(fetter_raw, bool) or not isinstance(fetter_raw, (int, float)):
        fetter_n = 0
    else:
        fetter_n = int(fetter_raw)
    chips = "".join(
        [
            f'<div class="chip">Lv.{char.char_level}</div>',
            _talent_badge(unlocked),
            _fetter_badge(fetter_n),
        ]
    )
    rows: list[str] = []
    gold_st = f"border:1px solid {GOLD}"
    for i, row in enumerate(stats):
        alt = " alt" if i % 2 else ""
        is_hot = row.name in hot
        hot_cls = " hot" if is_hot else ""
        hot_st = f' style="{gold_st}"' if is_hot else ""
        delta = f'<div class="sd">{_esc(row.delta)}</div>' if row.delta else '<div class="sd"></div>'
        rows.append(
            f'<div class="stat{alt}{hot_cls}"{hot_st}>'
            f'<img class="stic" src="{_stat_icon(row.icon, 18)}"/>'
            f'<div class="stnm">{_esc(row.name)}</div>'
            f'<div class="stv">{_esc(row.total)}</div>{delta}'
            "</div>"
        )
    sk: list[str] = []
    for sname, sicon, slv, boosted, kind in skills:
        color = "#63b8ff" if boosted else INK
        sk.append(
            '<div class="sk">'
            f'<img class="skic" src="{_icon(ICON_PATH / f"{sicon}.png", 22)}"/>'
            f'<div class="skmeta"><div class="sknm">{_aeq_btn(kind, accent)}'
            f"<span>{_esc(sname)}</span></div>"
            f'<div class="sklv" style="color:{color}">{slv}</div></div>'
            "</div>"
        )
    pts = con_arc_points(6, CON_TOP, CON_SPAN, CON_LEFT, CON_BOW)
    cn: list[str] = []
    for i, ticon in enumerate(talents):
        x, y = pts[i]
        uri = _talent_icon(ticon, CON_ICON) if ticon else ""
        pos = f"left:{x}px;top:{y}px"
        if not uri:
            cn.append(f'<div class="con off lock" style="{pos}"><img src="{lock}"/></div>')
            continue
        if i < unlocked:
            cn.append(
                f'<div class="con on" style="{pos};border-color:{_rgba(accent, 0.72)};'
                f'background:{_rgba(accent, 0.28)};box-shadow:0 0 10px {_rgba(accent, 0.45)}">'
                f'<img src="{uri}"/></div>'
            )
        else:
            cn.append(f'<div class="con off" style="{pos};border-color:{_rgba(accent, 0.28)}"><img src="{uri}"/></div>')
    return (
        '<div class="hero">'
        f'<img class="herobg" src="{hero_uri}"/>'
        f'<div class="conrail">{"".join(cn)}</div>'
        '<div class="heroin">'
        '<div class="htitle">'
        f"{_img('helem', eicon)}"
        f'<div class="hname" style="text-shadow:0 0 22px {_rgba(accent, 0.5)}">{_esc(char.char_name)}</div>'
        "</div>"
        f'<div class="hchips">{chips}</div>'
        f"{_data_time_html(data_time)}"
        '<div class="statpane">'
        f'<div class="stats">{"".join(rows)}</div>'
        f'<div class="skrow">{"".join(sk)}</div>'
        "</div>"
        "</div>"
        "</div>"
    )


async def _banner_avatar(card: Mapping[str, object]) -> str:
    url = _card_str(card, "playerAvatar")
    fallback = TEX2D_PATH / "icon.png"
    if url.startswith("http://") or url.startswith("https://"):
        img = await get_image(url, ICON_PATH, size=(AVATAR_CSS * SCALE, AVATAR_CSS * SCALE))
        rgba = img.convert("RGBA")
        extrema = rgba.getextrema()
        if len(extrema) >= 4 and extrema[3][1] == 0:
            return _icon(fallback, AVATAR_CSS)
        return _png_uri(rgba)
    local = Path(url) if url else fallback
    if not local.exists():
        local = fallback
    return _icon(local, AVATAR_CSS)


def _user_banner(card: Mapping[str, object], avatar_uri: str) -> str:
    name = _card_str(card, "playerName", "旅行者")
    uid = _card_str(card, "playerUid")
    sign = _card_str(card, "playerSignature")
    region = _card_str(card, "playerRegion")
    level = _card_int(card, "playerLevel")
    world = _card_int(card, "playerWorldLevel")
    bits: list[str] = []
    if level:
        bits.append(f"冒险 {level}")
    if world:
        bits.append(f"世界 {world}")
    if region:
        bits.append(region)
    info = " · ".join(bits)
    uid_line = f"UID {uid}" if uid else ""
    return (
        '<div class="ubanner">'
        f"{_img('uav', avatar_uri)}"
        '<div class="umain">'
        f'<div class="uname">{_esc(name)}</div>'
        f'<div class="usub">{_esc(sign)}</div>'
        "</div>"
        '<div class="umeta">'
        f'<div class="uidl">{_esc(uid_line)}</div>'
        f'<div class="uinfo">{_esc(info)}</div>'
        "</div>"
        "</div>"
    )


def _akasha_index() -> dict[int, list[dict[str, object]]]:
    global _AKASHA
    if _AKASHA is not None:
        return _AKASHA
    raw = json.loads(_AKASHA_PATH.read_text(encoding="utf-8"))
    out: dict[int, list[dict[str, object]]] = {}
    if not isinstance(raw, dict) or "leaderboards" not in raw:
        _AKASHA = out
        return out
    boards = raw["leaderboards"]
    if not isinstance(boards, list):
        _AKASHA = out
        return out
    for item in boards:
        if not isinstance(item, dict) or "characterId" not in item:
            continue
        cid = item["characterId"]
        if not isinstance(cid, int):
            continue
        if cid in out:
            out[cid].append(item)
        else:
            out[cid] = [item]
    _AKASHA = out
    return out


def _akasha_avg_stats(char_id: str, weapon_item_id: str) -> tuple[dict[str, float], str] | None:
    if not char_id.isdigit():
        return None
    cid = int(char_id)
    index = _akasha_index()
    if cid not in index or not index[cid]:
        return None
    boards = index[cid]
    picked = boards[0]
    for board in boards:
        if "weaponId" not in board:
            continue
        wid = board["weaponId"]
        if str(wid) == weapon_item_id:
            picked = board
            break
    if "avgStats" not in picked or not isinstance(picked["avgStats"], dict):
        return None
    stats: dict[str, float] = {}
    raw_stats = picked["avgStats"]
    for key, val in raw_stats.items():
        if isinstance(key, str) and isinstance(val, (int, float)) and not isinstance(val, bool):
            stats[key] = float(val)
    if len(stats) < 3:
        return None
    short = ""
    if "short" in picked and isinstance(picked["short"], str):
        short = picked["short"]
    return stats, short


def _radar_axes(
    fight: Mapping[str, object],
    avg: Mapping[str, float],
) -> list[tuple[str, str, str, float, float]]:
    out: list[tuple[str, str, str, float, float]] = []
    for akey, label, fkey in _RADAR_AXES:
        if akey not in avg:
            continue
        av = avg[akey]
        pv = _fight_num(fight, fkey)
        if akey in _RADAR_PCT:
            plab = _fmt_pct(_ratio_to_pct(pv))
            alab = _fmt_pct(_ratio_to_pct(av))
        else:
            plab = str(int(round(pv)))
            alab = str(int(round(av)))
        scale = max(pv, av, 1.0) * 1.12
        out.append((label, plab, alab, max(0.0, min(1.0, pv / scale)), max(0.0, min(1.0, av / scale))))
    return out


def _radar_block(card: Mapping[str, object], char_id: str, accent: str) -> str:
    if "avatarFightProp" not in card or not isinstance(card["avatarFightProp"], dict):
        return ""
    weapon_id = ""
    if "weaponInfo" in card and isinstance(card["weaponInfo"], dict):
        wpn = card["weaponInfo"]
        if "itemId" in wpn and isinstance(wpn["itemId"], (int, str)):
            weapon_id = str(wpn["itemId"])
    found = _akasha_avg_stats(char_id, weapon_id)
    if found is None:
        return ""
    avg, short = found
    axes = _radar_axes(card["avatarFightProp"], avg)
    svg = radar_svg(axes, accent, RADAR_W)
    if not svg:
        return ""
    cap = "Akasha 1%均"
    if short:
        cap = f"Akasha 1% · {short}"
    return f'<div class="radarbox">{svg}<div class="radarcap">{_esc(cap)}</div></div>'


def _ov_icon(src: str) -> str:
    if not src:
        return '<span class="ovicw"></span>'
    return f'<span class="ovicw"><img src="{src}"/></span>'


def _ov_cell(icon: str, label: str, value: str, extra: str = "") -> str:
    return (
        '<div class="ovcell">'
        f"{_ov_icon(icon)}"
        f'<div class="skv"><span>{_esc(label)}</span><b class="{extra}">{_esc(value)}</b></div>'
        "</div>"
    )


def _strip_html(
    score: float,
    cv_total: float,
    percent: str,
    set_label: str,
    rolls: tuple[int, int, int],
    useful: tuple[int, int],
    set_icon: str,
    accent: str,
    totals: tuple[list[_SumChip], int, float],
    radar: str,
) -> str:
    grade, gcolor = _grade(score)
    total, tier4, maxed = rolls
    hit, all_n = useful
    roll_text = f"{total} 次" if total else "无明细"
    high_text = f"4档 {tier4} · 满 {maxed}" if total else "—"
    count_text = f"{hit}/{all_n}" if all_n else "0/0"
    chips, roll_n, rv = totals
    bits: list[str] = []
    for chip in chips:
        on = " on" if chip.useful else ""
        bits.append(
            f'<div class="ovsum{on}"><span class="ovx">×{chip.count}</span>'
            f"{_img('osumic', _stat_icon(chip.icon, 16))}"
            f"<b>{_esc(chip.value)}</b></div>"
        )
    if roll_n:
        bits.append(
            f'<div class="ovsum on"><span class="ovx">×{roll_n}</span>'
            f'<span class="ovrv">RV</span><b>{rv:.0f}%</b></div>'
        )
    sums = "".join(bits)
    inner = (
        '<div class="strip">'
        '<div class="ovtop">'
        '<div class="ovscore">'
        f"{_ov_icon(_stat_icon('暴击伤害', 18))}"
        f'<div class="sbig" style="color:{accent};text-shadow:0 0 20px {_rgba(accent, 0.55)}">{score:.1f}</div>'
        f'<div class="sunit">有效词条<span>{_esc(count_text)}</span></div>'
        "</div>"
        '<div class="ovgrade">'
        f'<div class="grade" style="color:{gcolor};border-color:{gcolor};'
        f'background:{_rgba(gcolor, 0.18)}">{grade}</div>'
        '<div class="sunit">整体评级</div>'
        "</div>"
        '<div class="ovset">'
        f"{_img('setic', set_icon)}"
        f'<div class="skv wide"><span>套装</span><b>{_esc(set_label)}</b></div>'
        "</div>"
        "</div>"
        f'<div class="ovsums">{sums}</div>'
        '<div class="ovbot">'
        '<div class="ovbotrow">'
        f"{_ov_cell(_stat_icon('暴击伤害', 18), '总暴击分', f'{cv_total:.1f} CV')}"
        f"{_ov_cell(_stat_icon('元素精通', 18), '掷骰次数', roll_text)}"
        "</div>"
        '<div class="ovbotrow">'
        f"{_ov_cell(_stat_icon('元素充能效率', 18), '高档 / 满值', high_text)}"
        f"{_ov_cell(_stat_icon('百分比攻击力', 18), '毕业度', percent, 'gold')}"
        "</div>"
        "</div>"
        "</div>"
    )
    if radar:
        return f'<div class="ovbox">{radar}{inner}</div>'
    return inner


def _legend() -> str:
    tiers = "".join(f'<div class="lg">{_chevron(t)}<span>{t}档</span></div>' for t in (1, 2, 3, 4))
    return f'<div class="legend">{tiers}<span class="lgtip">一尖角 = 一次强化</span></div>'


def _section(title: str, en: str, right: str, icon: str, accent: str) -> str:
    return (
        '<div class="sec">'
        f'<div class="secbar" style="background:{accent}"></div>'
        '<div class="secbox">'
        f'<img class="secic" src="{icon}"/>'
        f'<div class="sect">{_esc(title)}</div>'
        f'<div class="secen" style="color:{accent};background:{_rgba(accent, 0.16)};'
        f'border-color:{_rgba(accent, 0.42)}">{_esc(en)}</div>'
        "</div>"
        f'<div class="secr">{right}</div>'
        "</div>"
    )


def _aeq_btn(kind: str, accent: str) -> str:
    if not kind:
        return ""
    tones: dict[str, tuple[str, str, str]] = {
        "A": ("#d7deea", "rgba(214,222,234,0.16)", "rgba(214,222,234,0.42)"),
        "E": ("#8ee4b8", "rgba(111,212,160,0.20)", "rgba(126,220,170,0.50)"),
        "Q": (accent, _rgba(accent, 0.22), _rgba(accent, 0.52)),
    }
    ink, fill, edge = tones[kind] if kind in tones else tones["A"]
    return f'<span class="akey" style="color:{ink};background:{fill};border-color:{edge}">{kind}</span>'


def _dmg_html(dmg_data: Mapping[str, Mapping[str, object]], accent: str) -> str:
    if not dmg_data:
        return '<div class="dmg"><div class="dmgempty">暂无该角色倍率表，本次仅展示面板与圣遗物明细。</div></div>'
    rows: list[tuple[str, float, float, float]] = []
    for name in dmg_data:
        row = dmg_data[name]
        crit = row["crit"] if "crit" in row and isinstance(row["crit"], (int, float)) else 0
        avg = row["avg"] if "avg" in row and isinstance(row["avg"], (int, float)) else 0
        normal = row["normal"] if "normal" in row and isinstance(row["normal"], (int, float)) else 0
        rows.append((name, float(crit), float(avg), float(normal)))
    top = max((r[2] for r in rows), default=1.0)
    if top <= 0:
        top = 1.0
    heads = [
        ("角色动作", "攻击力", "act"),
        ("暴击值", "暴击率", "val"),
        ("期望值", "暴击伤害", "val"),
        ("普通值", "百分比攻击力", "val"),
    ]
    head = "".join(
        f'<div class="dh {cls}"><img class="dhic" src="{_stat_icon(icon, 12)}"/><span>{_esc(label)}</span></div>'
        for label, icon, cls in heads
    )
    out = [f'<div class="dhead">{head}</div>']
    for i, (name, crit, avg, normal) in enumerate(rows):
        cls = "drow alt" if i % 2 else "drow"
        kind, label = split_dmg_label(name)
        fill = max(3, round((DMG_NAME_W - 20) * avg / top))
        out.append(
            f'<div class="{cls}">'
            f'<div class="dn"><div class="dnt">{_aeq_btn(kind, accent)}'
            f'<span class="dtx">{_esc(label)}</span></div>'
            f'<div class="dnb"><div class="dnf" style="width:{fill}px;'
            f'background:{_rgba(accent, 0.6)}"></div></div></div>'
            f'<div class="dc">{_fmt_int(crit)}</div>'
            f'<div class="dc hot">{_fmt_int(avg)}</div>'
            f'<div class="dc dim">{_fmt_int(normal)}</div>'
            "</div>"
        )
    return f'<div class="dmg">{"".join(out)}</div>'


def _css(accent: str, has_side: bool = False) -> str:
    total_w = PAGE_W + SIDE_W if has_side else PAGE_W
    extra = ""
    if has_side:
        extra = (
            f".shell.dual {{ display:grid; grid-template-columns:{PAGE_W}px {SIDE_W}px; }}"
            f".colL {{ width:{PAGE_W}px; position:relative; z-index:1; }}"
            f".colR {{ width:{SIDE_W}px; position:relative; z-index:1;"
            f"background:rgba(6,8,14,0.32); }}" + akasha_side_css(accent, SIDE_W)
        )
    return f"""
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ width:{total_w}px; font-family:{BODY_FONT}; color:{INK}; background:#05060b; }}
img {{ display:block; }}
.shell {{ position:relative; width:{total_w}px; }}
.pagebg {{ position:absolute; left:0; top:0; width:100%; height:100%;
  object-fit:cover; object-position:38% 22%; z-index:0; }}
.padem {{ position:absolute; left:0; top:{HEAD_H}px; width:100%;
  height:calc(100% - {HEAD_H}px); z-index:0;
  background:linear-gradient(180deg,rgba(8,10,16,0.12) 0%,rgba(8,10,16,0.36) 100%); }}
.page {{ position:relative; width:{PAGE_W}px; padding:0 0 {PAD}px; display:flex;
  flex-direction:column; gap:12px; background:transparent; }}
.headstack {{ display:flex; flex-direction:column; gap:0; width:{PAGE_W}px; }}
.mod {{ display:flex; flex-direction:column; gap:8px; padding:0 {PAD}px; }}

.ubanner {{ width:{PAGE_W}px; height:{BANNER_H}px; padding:0 16px; display:flex;
  align-items:center; gap:12px; background:rgba(8,10,16,0.62); border:none; }}
.uav {{ width:{AVATAR_CSS}px; height:{AVATAR_CSS}px; border-radius:{AVATAR_CSS // 2}px;
  flex-shrink:0; object-fit:cover; border:1px solid {HAIR}; }}
.umain {{ flex:1; min-width:0; }}
.uname {{ font-size:17px; font-weight:700; line-height:1.15; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }}
.usub {{ font-size:12px; color:{INK_2}; margin-top:3px; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; min-height:15px; }}
.umeta {{ text-align:right; flex-shrink:0; }}
.uidl {{ font-family:{NUM_FONT}; font-size:13px; font-weight:700; line-height:1.2; }}
.uinfo {{ font-size:12px; color:{INK_2}; margin-top:3px; line-height:1.2; }}

.hero {{ position:relative; width:{HERO_W}px; height:{HERO_H}px;
  overflow:hidden; border:none; border-radius:0; }}
.herobg {{ position:absolute; left:0; top:0; width:{HERO_W}px; height:{HERO_H}px; }}
.heroin {{ position:absolute; left:{HERO_TXT_L}px; top:0; width:{HERO_TXT_W}px; height:{HERO_H}px;
  padding:18px 12px 12px 12px; display:flex; flex-direction:column; border:none;
  background:none; }}
.conrail {{ position:absolute; left:0; top:0; width:{CON_RAIL_W}px; height:{HERO_H}px; }}
.htitle {{ display:flex; align-items:center; gap:8px; min-width:0; width:100%; }}
.helem {{ width:28px; height:28px; flex-shrink:0; }}
.hname {{ font-family:{NUM_FONT}; font-size:31px; font-weight:700; line-height:1;
  letter-spacing:1px; }}
.hchips {{ display:flex; align-items:center; gap:5px; margin-top:7px; }}
.hbadge {{ display:block; flex-shrink:0; }}
.chip {{ display:flex; align-items:center; justify-content:center; height:24px; padding:0 8px;
  border-radius:12px; background:rgba(255,255,255,0.08); border:1px solid {HAIR};
  font-size:12px; line-height:1; color:{INK}; white-space:nowrap; flex-shrink:0; }}
.htime {{ width:{STAT_W}px; margin-top:8px; font-size:10px; color:{INK_3}; font-weight:400;
  letter-spacing:0.2px; white-space:nowrap; text-align:right; line-height:1;
  padding:0 8px 0 0; }}

.statpane {{ margin-top:6px; width:{STAT_W}px;
  display:flex; flex-direction:column; gap:7px; box-sizing:border-box; }}
.stats {{ display:flex; flex-direction:column; gap:2px; width:100%; }}
.stat {{ width:100%; height:24px; padding:0 8px; border-radius:6px; box-sizing:border-box;
  background:rgba(0,0,0,0.28); display:flex; align-items:center; gap:6px; border:1px solid transparent; }}
.stat.alt {{ background:rgba(0,0,0,0.48); }}
.stic {{ width:18px; height:18px; }}
.stnm {{ flex:1; font-size:12px; color:{INK}; white-space:nowrap;
  text-shadow:0 1px 8px rgba(0,0,0,0.75); }}
.stv {{ width:{STAT_VAL_W}px; text-align:right; font-family:{NUM_FONT}; font-size:16px;
  font-weight:700; line-height:1; text-shadow:0 1px 8px rgba(0,0,0,0.65); }}
.sd {{ width:{STAT_DELTA_W}px; text-align:right; font-size:11px; color:{UP}; }}

.skrow {{ display:grid; grid-template-columns:1fr 1fr 1fr; column-gap:{SK_GAP}px; width:100%; }}
.sk {{ display:flex; align-items:center; gap:4px; height:36px; padding:0 6px 0 4px;
  min-width:0; border-radius:18px; background:rgba(0,0,0,0.42);
  border:1px solid {HAIR}; }}
.skic {{ width:22px; height:22px; flex-shrink:0; }}
.skmeta {{ display:flex; flex-direction:column; min-width:0; }}
.sknm {{ display:flex; align-items:center; gap:3px; font-size:11px; color:{INK};
  line-height:1.15; white-space:nowrap; font-weight:600;
  text-shadow:0 1px 8px rgba(0,0,0,0.9), 0 0 10px rgba(0,0,0,0.55); }}
.sk .akey {{ width:14px; height:14px; font-size:9px; flex-shrink:0; }}
.sklv {{ font-family:{NUM_FONT}; font-size:16px; font-weight:700; line-height:1.1;
  text-shadow:0 1px 8px rgba(0,0,0,0.55); }}
.con {{ position:absolute; z-index:2; width:{CON_SIZE}px; height:{CON_SIZE}px;
  border-radius:{CON_SIZE // 2}px; border:1px solid {HAIR}; background:rgba(6,8,14,0.78);
  display:flex; align-items:center; justify-content:center; }}
.con img {{ width:{CON_ICON}px; height:{CON_ICON}px; }}
.con.off {{ opacity:0.58; }}
.con.off.lock {{ opacity:0.42; }}
.con.off.lock img {{ width:16px; height:16px; }}

.sec {{ display:flex; align-items:center; gap:8px; height:32px; }}
.secbar {{ width:4px; height:22px; border-radius:2px; flex-shrink:0;
  box-shadow:0 0 10px rgba(255,255,255,0.18); }}
.secbox {{ display:flex; align-items:center; gap:7px; height:28px; padding:0 10px 0 8px;
  border-radius:8px; background:linear-gradient(180deg,rgba(255,255,255,0.12) 0%,
    rgba(255,255,255,0.03) 100%); border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP};
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.10); }}
.secic {{ width:18px; height:18px; }}
.sect {{ font-size:15px; font-weight:700; letter-spacing:0.4px; }}
.secen {{ font-size:9px; letter-spacing:1.4px; height:16px; padding:0 6px; border-radius:4px;
  border:1px solid; display:flex; align-items:center; }}
.secr {{ margin-left:auto; display:flex; align-items:center; gap:9px; font-size:11px;
  color:{INK_3}; }}
.legend {{ display:flex; align-items:center; gap:9px; }}
.lg {{ display:flex; align-items:center; gap:2px; font-size:11px; color:{INK_2}; }}
.lgtip {{ color:{INK_3}; }}

.ovbox {{ width:{INNER_W}px; display:flex; gap:8px; align-items:stretch; }}
.radarbox {{ width:{RADAR_W}px; flex-shrink:0; display:flex; flex-direction:column;
  align-items:center; justify-content:center; padding:4px 0 2px;
  border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  border-top:1px solid {HAIR_TOP}; }}
.radarbox svg {{ width:{RADAR_W}px; height:{RADAR_W}px; display:block; }}
.radarcap {{ font-size:10px; color:{INK_3}; margin-top:2px; }}
.strip {{ width:{INNER_W}px; min-height:92px; padding:10px 12px 11px; border-radius:12px;
  background:{SURFACE}; border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP};
  display:flex; flex-direction:column; gap:8px; }}
.ovbox .strip {{ flex:1; width:auto; min-width:0; justify-content:space-between; }}
.ovtop {{ display:flex; align-items:center; gap:10px; }}
.ovscore, .ovgrade {{ display:flex; align-items:center; gap:7px; flex-shrink:0; }}
.ovset {{ display:flex; align-items:center; gap:7px; flex:1; min-width:0; }}
.ovbot {{ display:flex; flex-direction:column; gap:6px; }}
.ovbotrow {{ display:flex; gap:10px; }}
.ovbotrow .ovcell {{ flex:1; min-width:0; }}
.ovcell {{ display:flex; align-items:center; gap:7px; min-width:0; min-height:32px; }}
.ovicw {{ width:26px; height:26px; border-radius:7px; flex-shrink:0;
  background:rgba(255,255,255,0.08); border:1px solid {HAIR};
  display:flex; align-items:center; justify-content:center; }}
.ovicw img {{ width:18px; height:18px; object-fit:contain; }}
.setic {{ width:36px; height:36px; flex-shrink:0; object-fit:contain; }}
.ovsums {{ display:flex; flex-wrap:wrap; gap:5px 6px; padding:2px 0 1px; }}
.ovsum {{ display:flex; align-items:center; gap:4px; height:24px; padding:0 8px 0 6px;
  border-radius:12px; background:rgba(0,0,0,0.38); border:1px solid rgba(255,255,255,0.12); }}
.ovsum.on {{ border:1px solid rgba(234,198,131,0.70); }}
.stat.hot {{ border:1px solid {GOLD}; }}
.ovx {{ font-family:{NUM_FONT}; font-size:11px; font-weight:700; color:{INK_2}; }}
.ovsum.on .ovx {{ color:{GOLD}; }}
.ovrv {{ font-size:10px; font-weight:700; letter-spacing:0.6px; color:{GOLD}; }}
.osumic {{ width:16px; height:16px; flex-shrink:0; }}
.ovsum b {{ font-family:{NUM_FONT}; font-size:13px; font-weight:700; color:{INK}; }}
.sbig {{ font-family:{NUM_FONT}; font-size:30px; font-weight:700; line-height:1; }}
.sunit {{ font-size:11px; color:{INK_3}; line-height:1.25; display:flex; flex-direction:column;
  white-space:nowrap; }}
.sunit span {{ font-size:10px; color:{INK_2}; margin-top:2px; white-space:nowrap; }}
.grade {{ width:26px; height:26px; min-width:26px; padding:0; border:1px solid; border-radius:7px;
  display:flex; align-items:center; justify-content:center; font-family:{NUM_FONT};
  font-size:13px; font-weight:700; letter-spacing:0; }}
.skv {{ display:flex; flex-direction:column; justify-content:center; min-width:0; }}
.skv.wide {{ flex:1; overflow:hidden; }}
.skv span {{ font-size:10px; color:{INK_3}; line-height:1.3; }}
.skv b {{ font-size:13px; font-weight:700; line-height:1.3; white-space:nowrap; }}
.skv b.gold {{ color:{GOLD}; }}

.grid {{ display:flex; flex-wrap:wrap; gap:{GRID_GAP}px; }}
.card {{ position:relative; width:{CARD_W}px; height:{CARD_H}px; padding:6px 10px;
  border-radius:12px; background:{SURFACE}; border:1px solid {HAIR};
  display:flex; flex-direction:column; }}
.cwm {{ position:absolute; right:8px; top:6px; width:62px; height:62px; border-radius:12px;
  border:1px solid; display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.cwm img {{ width:56px; height:56px; }}
.clv {{ position:absolute; right:0; bottom:0; height:15px; padding:0 5px;
  background:rgba(4,6,12,0.82); display:flex; align-items:center; justify-content:center;
  font-family:{NUM_FONT}; font-size:11px; color:{INK}; border-radius:6px 0 0 0; }}
.chead {{ min-height:64px; padding-right:70px; }}
.cname {{ font-size:14px; font-weight:700; line-height:1.2; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }}
.cscore {{ display:flex; align-items:flex-end; gap:4px; margin-top:2px; flex-wrap:wrap; }}
.csv {{ font-family:{NUM_FONT}; font-size:20px; font-weight:700; line-height:1; }}
.csl {{ font-size:10px; color:{INK_3}; line-height:1; padding-bottom:1px; }}
.csc {{ font-size:10.5px; color:{INK_2}; padding-left:2px; line-height:1; padding-bottom:1px; }}
.wr {{ display:flex; align-items:center; justify-content:center; height:17px; padding:0 6px;
  border-radius:5px; font-size:11.5px; }}
.cstar {{ color:{GOLD}; font-size:12px; letter-spacing:1px; line-height:1.2; margin-top:1px; }}
.cmain {{ display:flex; align-items:center; gap:5px; height:22px; margin-top:2px; }}
.cmic {{ width:18px; height:18px; flex-shrink:0; }}
.cmn {{ flex:1; font-size:12px; color:{INK_2}; }}
.cmv {{ font-family:{NUM_FONT}; font-size:21px; font-weight:700; line-height:1; }}
.csubs {{ display:flex; flex-direction:column; gap:2px; margin-top:2px; }}
.srow {{ display:flex; align-items:center; height:18px; gap:3px; padding:0 2px; }}
.srest {{ position:relative; flex:1; min-width:0; display:flex; align-items:center;
  gap:3px; height:18px; }}
.sbeam {{ display:none; position:absolute; left:0; right:0; top:1px; height:16px;
  border-radius:4px; pointer-events:none; z-index:0; }}
.sic, .snm, .chev, .sv {{ position:relative; z-index:1; }}
.srow.off {{ opacity:0.82; }}
.srow.off .snm {{ color:rgba(242,245,251,0.40); font-weight:400; }}
.srow.off .sv {{ color:rgba(242,245,251,0.40); font-weight:400; }}
.srow.off .sic {{ opacity:0.5; }}
.srow.off .cv1 {{ opacity:0.55; font-weight:400; }}
.ssb {{ flex-shrink:0; min-width:28px; height:16px; padding:0 4px; border-radius:4px;
  border:1px solid; display:flex; align-items:center; justify-content:center;
  font-family:{NUM_FONT}; font-size:11px; font-weight:700; line-height:1; }}
.srow.off .ssb {{ font-weight:500; }}
.sic {{ width:16px; height:16px; }}
.snm {{ font-size:12px; color:{INK_2}; white-space:nowrap; }}
.chev {{ flex:1; display:flex; align-items:center; padding-left:1px; }}
.chev.none {{ font-size:11px; color:{INK_3}; }}
.cv1 {{ font-family:{BODY_FONT}; font-size:15px; font-weight:700; line-height:1;
  margin-right:-2px; }}
.sv {{ font-family:{NUM_FONT}; font-size:14px; font-weight:700; white-space:nowrap; }}
.wps {{ display:flex; flex-direction:column; gap:3px; margin-top:2px; }}
.wp {{ display:flex; align-items:center; height:22px; padding:0 8px; border-radius:6px;
  background:rgba(255,255,255,0.08); gap:6px; }}
.wpic {{ width:16px; height:16px; flex-shrink:0; }}
.wp span {{ flex:1; font-size:11.5px; color:{INK_2}; }}
.wp b {{ font-family:{NUM_FONT}; font-size:15px; font-weight:700; }}
.wdesc {{ font-size:11.5px; line-height:1.4; color:{INK_2}; margin-top:4px; overflow:hidden; }}

.dmg {{ width:{INNER_W}px; padding:3px 10px 8px 10px; border-radius:11px; background:{SURFACE};
  border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; display:flex;
  flex-direction:column; }}
.dmgempty {{ padding:13px 4px; font-size:13px; color:{INK_3}; }}
.dhead {{ display:flex; align-items:center; height:26px; padding-bottom:4px; font-size:11px;
  color:{INK_3}; letter-spacing:0.6px; border-bottom:1px solid {HAIR}; }}
.dh {{ display:flex; align-items:center; gap:4px; }}
.dh.act {{ width:{DMG_NAME_W}px; padding-left:7px; }}
.dh.val {{ width:{DMG_VAL_W}px; padding-right:10px; justify-content:flex-end; }}
.dhic {{ width:12px; height:12px; opacity:0.72; }}
.drow {{ display:flex; align-items:center; height:27px; border-radius:5px; }}
.drow.alt {{ background:rgba(255,255,255,0.04); }}
.dn {{ width:{DMG_NAME_W}px; padding-left:7px; display:flex; flex-direction:column; }}
.dnt {{ display:flex; align-items:center; gap:5px; min-width:0; }}
.dtx {{ font-size:12.5px; line-height:1.15; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }}
.akey {{ width:16px; height:16px; border-radius:4px; border:1px solid; border-bottom-width:2px;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
  font-family:{NUM_FONT}; font-size:10.5px; font-weight:700; line-height:1;
  box-shadow:0 1px 0 rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.22); }}
.dnb {{ width:{DMG_NAME_W - 20}px; height:2px; border-radius:1px;
  background:rgba(255,255,255,0.07); margin-top:3px; overflow:hidden; }}
.dnf {{ height:2px; border-radius:1px; }}
.dc {{ width:{DMG_VAL_W}px; padding-right:10px; text-align:right; font-family:{NUM_FONT};
  font-size:13.5px; color:{INK_2}; }}
.dc.hot {{ color:{INK}; font-weight:700; }}
.dc.dim {{ color:{INK_3}; }}

.foot {{ display:flex; align-items:center; justify-content:center; height:18px; }}
.foot img {{ width:400px; height:15px; opacity:0.5; }}
{extra}
"""


async def render_char_card_html(
    char: Character,
    char_url: str | None,
    *,
    akasha_side: AkashaSideInject | None = None,
) -> Image.Image:
    _ensure_ys_font()
    if "atk" in char.fight_prop:
        await get_char_dmg_percent(char)
    card = char.card_prop
    accent = _accent(char.char_element)
    splash = _load_splash_image(char, char_url)
    hero_uri = await _build_hero(splash, accent)

    stats = _build_stat_rows(card, char.char_element)
    skills = _skill_levels(card, char.char_name)
    char_id = str(char.char_id)
    if "avatarId" in card and isinstance(card["avatarId"], (int, str)):
        char_id = str(card["avatarId"])
    talents = _talent_icons(char_id, char.char_element)
    unlocked = _talent_unlocked(card)
    artis = await _score_artifacts(char)
    score = await get_all_artifacts_value(card, char.baseHp, char.baseAtk, char.baseDef, char.char_name)
    cv_total = sum(a.cv_score for a in artis)
    percent = "暂无匹配" if char.percent == "0.00" else f"{char.percent}%"

    dmg_map: dict[str, Mapping[str, object]] = {}
    if isinstance(char.dmg_data, dict):
        for key, val in char.dmg_data.items():
            if isinstance(key, str) and isinstance(val, dict):
                dmg_map[key] = val

    cards = [_weapon_card(card, accent)] + [_arti_card(a, accent) for a in artis[:5]]
    totals = _sub_totals(artis)
    hot = _hot_stat_names(totals[0])
    set_icon = _icon(REL_PATH / f"{artis[0].icon}.png", 36) if artis else _stat_icon("元素精通", 36)
    footer = _file_uri(Path(__file__).parents[1] / "utils" / "image" / "texture2d" / "footer.png")
    banner_uri = await _banner_avatar(card)
    if akasha_side is None:
        boards, rows, dists, ranks = await _fetch_akasha_side(char)
    else:
        boards, rows, dists, ranks = akasha_side
    rank_wids = [item["weapon_id"] for item in ranks if item["weapon_id"]]
    side_html = akasha_side_html(
        boards[0] if boards else None,
        rows,
        accent=accent,
        char_icons=_side_char_icons(rows),
        weapon_icons=_side_weapon_icons(rows, rank_wids),
        boards=boards,
        dists=dists,
        ranks=ranks,
        self_uid=_card_str(card, "playerUid"),
        target_height=_left_card_height(len(dmg_map), len(cards)),
        section_icons={
            "dist": _stat_icon("攻击力", 18),
            "gain": _stat_icon("暴击伤害", 18),
            "teams": _stat_icon("元素精通", 18),
            "rank": _stat_icon("暴击率", 18),
            "hp": _stat_icon("血量", 12),
            "atk": _stat_icon("攻击力", 12),
            "face": _icon(CHAR_PATH / f"{char_id}.png", 40),
        },
    )
    has_side = bool(side_html)
    bg_w = PAGE_W + SIDE_W if has_side else PAGE_W
    page_bg = await _build_page_bg(splash, accent, bg_w)
    inner_page = "".join(
        [
            '<div class="page">',
            '<div class="headstack">',
            _user_banner(card, banner_uri),
            _hero_html(
                hero_uri,
                char,
                accent,
                stats,
                skills,
                talents,
                unlocked,
                hot,
                _card_str(card, "dataTime"),
            ),
            "</div>",
            '<div class="mod">',
            _section("武器 · 圣遗物强化明细", "ROLLS", _legend(), _stat_icon("暴击伤害", 18), accent),
            _strip_html(
                score,
                cv_total,
                percent,
                _set_label(card),
                _roll_stats(artis),
                _useful_count(artis),
                set_icon,
                accent,
                totals,
                _radar_block(card, char_id, accent),
            ),
            f'<div class="grid">{"".join(cards)}</div>',
            "</div>",
            '<div class="mod">',
            _section("伤害计算", "DAMAGE", f"主词条 {_esc(char.seq_str)}", _stat_icon("攻击力", 18), accent),
            _dmg_html(dmg_map, accent),
            "</div>",
            f'<div class="foot"><img src="{footer}"/></div>',
            "</div>",
        ]
    )
    if has_side:
        body = (
            '<div class="shell dual">'
            f'<img class="pagebg" src="{page_bg}"/>'
            '<div class="padem"></div>'
            f'<div class="colL">{inner_page}</div>'
            f'<div class="colR">{side_html}</div>'
            "</div>"
        )
    else:
        body = f'<div class="shell"><img class="pagebg" src="{page_bg}"/><div class="padem"></div>{inner_page}</div>'
    total_w = PAGE_W + SIDE_W if has_side else PAGE_W
    page = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        f"<style>{_css(accent, has_side)}</style></head><body>{body}</body></html>"
    )
    png = await render_html_to_bytes(
        page,
        max_width=total_w * SCALE,
        dpi=96 * SCALE,
        default_font_size=13,
        font_name="YuanShen",
        allow_refit=True,
        image_format="png",
        lang="zh",
        root_max_width=total_w,
    )
    return Image.open(BytesIO(png)).convert("RGBA")


def _data_time_html(raw: str) -> str:
    if not raw:
        return ""
    return f'<div class="htime">{_esc(raw)}</div>'


def _left_card_height(dmg_rows: int, card_count: int) -> int:
    ov = RADAR_W + 18
    rows = (card_count + 2) // 3
    if rows < 1:
        rows = 1
    grid = rows * CARD_H + max(0, rows - 1) * GRID_GAP
    rolls = 32 + 8 + ov + 8 + grid
    dmg = 32 + 8 + 11 + 26 + dmg_rows * 27
    return HEAD_H + 12 + rolls + 12 + dmg + 12 + 18 + 12


async def _fetch_akasha_side(char: Character) -> AkashaSideInject:
    empty: AkashaSideInject = ([], [], [], [])
    if not gsconfig.get_config("EnableAkasha").data:
        return empty
    uid = _card_str(char.card_prop, "playerUid")
    char_id = str(char.char_id)
    if "avatarId" in char.card_prop and isinstance(char.card_prop["avatarId"], (int, str)):
        char_id = str(char.card_prop["avatarId"])
    if not uid:
        return empty
    loaded = load_akasha_side(uid, char_id)
    if loaded is None:
        return empty
    return loaded


def _side_char_icons(rows: list[BuildLeaderboardRow], css: int = 36) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        for mate in row["teammates"]:
            name = mate["character"]["name"]
            if name in out or name not in enName_to_avatarId_data:
                continue
            src = _icon(CHAR_PATH / f"{enName_to_avatarId_data[name]}.png", css)
            if src:
                out[name] = src
    return out


def _side_weapon_icons(
    rows: list[BuildLeaderboardRow],
    extra_ids: list[str] | None = None,
    css: int = 28,
) -> dict[str, str]:
    out: dict[str, str] = {}
    wids: list[str] = [row["weapon"]["weaponId"] for row in rows]
    if extra_ids is not None:
        wids.extend(extra_ids)
    for wid in wids:
        if wid in out or wid not in weaponId2Name_data:
            continue
        src = _icon(WEAPON_PATH / f"{weaponId2Name_data[wid]}.png", css)
        if src:
            out[wid] = src
    return out
