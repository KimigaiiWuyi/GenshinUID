"""角色卡右侧 Akasha 栏：伤害分布 + 加一发副词条收益 + 各队伍榜。

纯 HTML/CSS 字符串，不依赖 html_char_card / Core，方便单测 spec-load。
列宽 640，与左侧竖版卡对齐；无数据时调用方应保持单列。
小标题复用左侧 ``.sec`` 样式；模块间距 12px，与左列 ``.page`` gap 一致。
"""

from __future__ import annotations

import html
import json
from typing import Mapping, Sequence
from pathlib import Path

SIDE_W = 640
SIDE_PAD = 12
SIDE_INNER = SIDE_W - SIDE_PAD * 2
TEAM_SLOTS = 4
SIDE_LOADOUTS = 2
SIDE_GAIN_LOADOUTS = 2
SIDE_RANK_MAX = 3
DD_GAP = 8
RANK_ROW_H = 64
RANK_HEADER_H = 40
CALC_KEY_LEN = 10

BODY_FONT = "'MiSans','YuanShen',sans-serif"
NUM_FONT = "'YuanShen','MiSans',sans-serif"
INK = "#f2f5fb"
INK_2 = "rgba(242,245,251,0.62)"
INK_3 = "rgba(242,245,251,0.34)"
UP = "#63e2a4"
DOWN = "#ef6b6b"
HAIR = "rgba(255,255,255,0.08)"
HAIR_TOP = "rgba(255,255,255,0.18)"
SURFACE = "linear-gradient(180deg,rgba(10,12,20,0.42) 0%,rgba(8,10,16,0.56) 100%)"
_TYPE_COLOR: dict[str, str] = {
    "E": "#5b8def",
    "Q": "#c48ef0",
    "NA": "#e8c44d",
    "N": "#e8c44d",
    "A": "#e8c44d",
    "CA": "#ffb056",
    "LC": "#b98cf5",
    "LCR": "#9b7dff",
    "LB": "#77dd8f",
    "SSC": "#8fb4d4",
    "SSW": "#7fd0c4",
    "B": "#ffb056",
}
_TYPE_KEY: dict[str, str] = {
    "NA": "A",
    "N": "A",
    "A": "A",
    "E": "E",
    "Q": "Q",
    "CA": "B",
    "PA": "C",
    "PL": "C",
    "Plunge": "C",
}
_AKEY_COLOR: dict[str, str] = {
    "A": "#e8c44d",
    "E": "#5b8def",
    "Q": "#c48ef0",
    "B": "#ffb056",
    "C": "#9b7dff",
}
_RX_EN: tuple[tuple[str, str], ...] = (
    ("Lunar-Charged", "月感电"),
    ("Lunar-Crystallize", "月结晶"),
    ("Stellar-Conduct", "星超导"),
    ("Stellar Swirl", "星扩散"),
    ("Hyperbloom", "超绽放"),
    ("Electro-Charged", "感电"),
    ("Electrocharged", "感电"),
    ("Overloaded", "超载"),
    ("Overload", "超载"),
    ("Burgeon", "烈绽放"),
    ("Vape", "蒸发"),
    ("Melt", "融化"),
    ("Bloom", "绽放"),
)
_RX_TYPE: dict[str, str] = {
    "LC": "月感电",
    "LCR": "月结晶",
    "LB": "月绽放",
    "SSC": "星超导",
    "SSW": "星扩散",
}
_RX_ZH = (
    "月感电",
    "月结晶",
    "月绽放",
    "星超导",
    "星扩散",
    "超绽放",
    "烈绽放",
    "蒸发",
    "融化",
    "感电",
    "超载",
    "绽放",
)
_REF_ZH = ("", "一", "二", "三", "四", "五")
_REGION_BG: dict[str, str] = {
    "CN": "#ff3a3a",
    "ASIA": "#a96d39",
    "EU": "#5062ff",
    "NA": "#ffa500",
    "TW": "#252525",
    "B": "#802397",
}
DD_BAR_W = 600

SUBSTAT_ZH: dict[str, str] = {
    "Base": "当前",
    "Flat HP": "生命值",
    "HP%": "生命%",
    "Flat ATK": "攻击力",
    "ATK%": "攻击%",
    "Flat DEF": "防御力",
    "DEF%": "防御%",
    "Crit RATE": "暴击率",
    "Crit DMG": "暴击伤害",
    "Elemental Mastery": "精通",
    "Energy Recharge": "充能",
    "Healing Bonus": "治疗",
}
_ZH_PATH = Path(__file__).resolve().parent / "akasha_zh.json"
_ZH: dict[str, dict[str, str]] | None = None
_PCT_ROLLS = {
    "HP%",
    "ATK%",
    "DEF%",
    "Crit RATE",
    "Crit DMG",
    "Energy Recharge",
    "Healing Bonus",
}


def substat_zh(name: str) -> str:
    if name in SUBSTAT_ZH:
        return SUBSTAT_ZH[name]
    return name


def fmt_result(value: float) -> str:
    return f"{int(round(value)):,}"


def fmt_dmg_gain(value: float) -> str:
    if abs(value) < 0.5:
        return "—"
    n = int(round(value))
    sign = "+" if n > 0 else ""
    return f"{sign}{n:,}"


def fmt_pct_gain(value: float) -> str:
    if abs(value) < 0.005:
        return "—"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def fmt_rank(value: int) -> str:
    return f"{value:,}"


def fmt_out_of(value: int) -> str:
    if value >= 10000:
        return f"{round(value / 1000)}k"
    return f"{value:,}"


def fmt_top_pct(value: float) -> str:
    return f"前{int(round(value))}%"


def top_pct_color(value: float) -> str:
    if value <= 1:
        return "#ef6b6b"
    if value <= 5:
        return "#ffb056"
    if value <= 10:
        return "#c48ef0"
    if value <= 30:
        return "#8fb4ff"
    if value <= 50:
        return "#f2f5fb"
    return "#8b919c"


def zh_table() -> dict[str, dict[str, str]]:
    global _ZH
    if _ZH is not None:
        return _ZH
    raw = json.loads(_ZH_PATH.read_text(encoding="utf-8"))
    out: dict[str, dict[str, str]] = {}
    if isinstance(raw, dict):
        for key, val in raw.items():
            if not isinstance(key, str) or not isinstance(val, dict):
                continue
            bucket: dict[str, str] = {}
            for en, zh in val.items():
                if isinstance(en, str) and isinstance(zh, str):
                    bucket[en] = zh
            out[key] = bucket
    _ZH = out
    return out


def zh_text(text: str) -> str:
    """Akasha 英文队名 / 变体 / 武器 / 角色 → 中文。缺词走 phrases 替换。"""
    if not text:
        return text
    table = zh_table()
    for bucket in ("names", "shorts", "variants", "weapons", "chars", "parts", "types"):
        mapping = table[bucket] if bucket in table else {}
        if text in mapping:
            return mapping[text]
    phrases = table["phrases"] if "phrases" in table else {}
    out = text
    for en in sorted(phrases, key=len, reverse=True):
        zh = phrases[en]
        if en and en in out:
            out = out.replace(en, zh)
    return out


def fmt_roll(name: str, roll: float) -> str:
    if name in _PCT_ROLLS:
        return f"+{roll:.2f}"
    return f"+{int(round(roll))}"


def gain_class(value: float) -> str:
    if value > 0.005:
        return "gain"
    if value < -0.005:
        return "loss"
    return ""


def pick_priority_board(
    boards: list[Mapping[str, object]],
    preferred_id: str | None,
) -> Mapping[str, object] | None:
    """优先取与当前队伍榜 ``calculation_id`` 对上的那张收益表。"""
    if not boards:
        return None
    if preferred_id:
        found = match_calc_board(boards, preferred_id)
        if found is not None:
            return found
    return boards[0]


def _calc_key(calc_id: str) -> str:
    return calc_id[:CALC_KEY_LEN]


def _weapon_id_of(row: Mapping[str, object]) -> str:
    weapon = row["weapon"] if "weapon" in row and isinstance(row["weapon"], dict) else None
    if weapon is None:
        return ""
    return _as_str(weapon["weaponId"] if "weaponId" in weapon else "")


def pick_loadout_ids(
    rows: Sequence[Mapping[str, object]],
    limit: int = SIDE_LOADOUTS,
) -> list[str]:
    """按名次取最多 ``limit`` 套**不同武器**的榜 ID，用来对照伤害分布 / 副词条。"""
    if limit <= 0 or not rows:
        return []
    picked: list[str] = []
    seen_weapons: set[str] = set()
    for row in rows:
        cid = _as_str(row["calculation_id"] if "calculation_id" in row else "")
        if not cid:
            continue
        wid = _weapon_id_of(row)
        if wid and wid in seen_weapons:
            continue
        picked.append(cid)
        if wid:
            seen_weapons.add(wid)
        if len(picked) >= limit:
            return picked
    seen_keys = {_calc_key(cid) for cid in picked}
    for row in rows:
        cid = _as_str(row["calculation_id"] if "calculation_id" in row else "")
        if not cid:
            continue
        key = _calc_key(cid)
        if key in seen_keys:
            continue
        picked.append(cid)
        seen_keys.add(key)
        if len(picked) >= limit:
            break
    return picked


def match_calc_board(
    items: Sequence[Mapping[str, object]],
    calc_id: str,
) -> Mapping[str, object] | None:
    """按榜 ID 取值；``170er`` 后缀只比前 10 位。"""
    if not calc_id:
        return None
    key = _calc_key(calc_id)
    prefix: Mapping[str, object] | None = None
    for item in items:
        cid = _as_str(item["calculation_id"] if "calculation_id" in item else "")
        if cid == calc_id:
            return item
        if prefix is None and cid and _calc_key(cid) == key:
            prefix = item
    return prefix


def _max_dist_parts(dists: list[Mapping[str, object]]) -> int:
    n = 0
    for dist in dists:
        raw = dist["parts"] if "parts" in dist else None
        if isinstance(raw, list):
            n = max(n, len(raw))
    return n


def _gain_row_count(board: Mapping[str, object]) -> int:
    gains = board["gains"] if "gains" in board else None
    if not isinstance(gains, list):
        return 0
    return sum(1 for item in gains if isinstance(item, dict))


def estimate_side_used(n_dist_parts: int, gain_rows: list[int], n_teams: int) -> int:
    """右列去掉全球榜之后的 CSS 高度。"""
    h = 66 + 12 + 36
    if n_dist_parts:
        h += 32 + 8 + 96 + n_dist_parts * 18
        h += 12
    if gain_rows:
        h += 32 + 8
        for i, n in enumerate(gain_rows):
            if i:
                h += 8
            h += 58 + n * 26
        h += 12
    if n_teams:
        h += 32 + 8 + n_teams * 72
        h += 12
    return h


def type_key(ptype: str) -> str:
    return _TYPE_KEY[ptype] if ptype in _TYPE_KEY else ""


def reaction_tag(name: str, ptype: str) -> str:
    if ptype in _RX_TYPE:
        return _RX_TYPE[ptype]
    lower = name.lower()
    for en, zh in _RX_EN:
        if en.lower() in lower:
            return zh
    zh_name = zh_text(name)
    for tag in _RX_ZH:
        if tag in zh_name:
            return tag
    return ""


def fmt_con(value: int) -> str:
    if value >= 6:
        return "满命"
    return f"{value}命"


def fmt_ref(value: int) -> str:
    if value >= 5:
        return "满精"
    if 1 <= value < len(_REF_ZH):
        return f"精{_REF_ZH[value]}"
    return f"精{value}"


def fmt_ratio(value: float) -> str:
    pct = value * 100.0 if value <= 10 else value
    return f"{pct:.1f}"


def pick_nearby_ranks(
    rows: list[Mapping[str, object]],
    self_uid: str,
    limit: int = SIDE_RANK_MAX,
) -> list[Mapping[str, object]]:
    """围着自己开窗。名单里没有自己就空，避免把全服前三当成附近。"""
    if limit <= 0 or not rows:
        return []
    if not self_uid:
        return rows[:limit]
    idx = -1
    for i, row in enumerate(rows):
        uid = _as_str(row["uid"] if "uid" in row else "")
        if uid == self_uid:
            idx = i
            break
    if idx < 0:
        return []
    start = idx - limit // 2
    if start < 0:
        start = 0
    end = start + limit
    if end > len(rows):
        end = len(rows)
        start = end - limit
        if start < 0:
            start = 0
    return rows[start:end]


def count_rank_slots(target_h: int, used_h: int, available: int) -> int:
    leftover = target_h - used_h - RANK_HEADER_H
    n = leftover // RANK_ROW_H
    if n < 0:
        n = 0
    if n > available:
        n = available
    if n > SIDE_RANK_MAX:
        n = SIDE_RANK_MAX
    return n


def akasha_side_css(accent: str, side_w: int = SIDE_W) -> str:
    inner = side_w - SIDE_PAD * 2
    half = (inner - DD_GAP) // 2
    half_bar = half - 16
    return f"""
.side {{ width:{side_w}px; padding:0 0 12px; color:{INK}; font-family:{BODY_FONT}; }}
.sidehead {{ width:{side_w}px; height:66px; padding:14px 16px 0; background:rgba(8,10,16,0.38);
  box-sizing:border-box; }}
.shtitle {{ font-size:17px; font-weight:700; line-height:1.15; }}
.shsub {{ font-size:12px; color:{INK_2}; margin-top:3px; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }}
.sidein {{ width:{inner}px; margin:12px auto 0; }}
.smod {{ margin-top:12px; }}
.smod.first {{ margin-top:0; }}
.smod .sec {{ margin-bottom:8px; }}
.spbox {{ width:{inner}px; padding:6px 8px 8px; border-radius:12px; background:{SURFACE};
  border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; box-sizing:border-box; }}
.spbox + .spbox {{ margin-top:8px; }}
.sptab {{ width:100%; }}
.sgcap, .ddcap {{ font-size:12px; font-weight:700; line-height:1.2; margin-bottom:6px; color:{INK}; }}
.sgbase {{ height:28px; padding:0 4px; }}
.sgbname {{ display:inline-block; width:156px; font-size:12px; color:{INK_3}; vertical-align:middle; }}
.sgbval {{ display:inline-block; width:140px; font-family:{NUM_FONT}; font-size:15px; font-weight:700;
  text-align:right; vertical-align:middle; }}
.sgbrank {{ display:inline-block; width:288px; text-align:right; font-family:{NUM_FONT}; font-size:12px;
  color:{INK_2}; vertical-align:middle; }}
.sgrow {{ height:26px; padding:0 4px; }}
.sgrow.alt {{ background:rgba(0,0,0,0.22); border-radius:4px; }}
.sgname {{ display:inline-block; width:100px; font-size:12px; color:{INK}; vertical-align:middle; }}
.sgroll {{ display:inline-block; width:56px; font-family:{NUM_FONT}; font-size:11px; color:{INK_3};
  vertical-align:middle; }}
.sgdmg {{ display:inline-block; width:140px; font-family:{NUM_FONT}; font-size:13px; font-weight:700;
  text-align:right; vertical-align:middle; }}
.sgpct {{ display:inline-block; width:88px; font-family:{NUM_FONT}; font-size:13px; font-weight:700;
  text-align:right; vertical-align:middle; }}
.sgrank {{ display:inline-block; width:200px; font-family:{NUM_FONT}; font-size:12px; color:{INK_2};
  text-align:right; vertical-align:middle; }}
.gain {{ color:{UP}; }}
.loss {{ color:{DOWN}; }}
.lblist {{ width:{inner}px; }}
.lbcard {{ width:{inner}px; margin-top:4px; padding:6px 8px; border-radius:8px;
  background:{SURFACE}; border:1px solid {HAIR}; box-sizing:border-box; }}
.lbcard.on {{ border:1px solid {accent}; }}
.lb1, .lb2 {{ width:600px; height:28px; white-space:nowrap; }}
.lbrank {{ display:inline-block; width:118px; font-family:{NUM_FONT}; font-size:12px;
  font-weight:700; vertical-align:middle; }}
.lbtopn {{ display:inline-block; width:58px; font-size:11px; font-weight:700; text-align:center;
  vertical-align:middle; }}
.lbwpn {{ display:inline-block; width:200px; font-family:{NUM_FONT}; font-size:11px;
  color:{INK_2}; vertical-align:middle; }}
.lbwpn img {{ width:20px; height:20px; display:inline-block; vertical-align:middle; }}
.lbwpn span {{ vertical-align:middle; padding-left:3px; }}
.lbtms {{ display:inline-block; width:140px; vertical-align:middle; white-space:nowrap; }}
.tm {{ display:inline-block; position:relative; width:28px; height:28px; margin-right:4px;
  vertical-align:top; }}
.tmface {{ display:block; position:relative; width:28px; height:28px; border-radius:6px;
  overflow:hidden; border:1px solid {HAIR}; }}
.tmface.r5 {{ background:rgba(198,152,80,0.72); }}
.tmface.r4 {{ background:rgba(150,120,196,0.72); }}
.tmface.r3 {{ background:rgba(96,146,190,0.62); }}
.tmstar {{ position:absolute; left:0; bottom:0; width:28px; height:11px; }}
.tmface.r5 .tmstar {{ background:linear-gradient(180deg,rgba(198,152,80,0) 0%,rgba(198,152,80,0.95) 100%); }}
.tmface.r4 .tmstar {{ background:linear-gradient(180deg,rgba(150,120,196,0) 0%,rgba(150,120,196,0.95) 100%); }}
.tmface.r3 .tmstar {{ background:linear-gradient(180deg,rgba(96,146,190,0) 0%,rgba(96,146,190,0.92) 100%); }}
.tm img {{ width:28px; height:28px; object-fit:cover; }}
.tmph {{ display:block; width:28px; height:28px; line-height:28px; text-align:center;
  font-size:11px; font-weight:700; color:{INK_2}; }}
.tmc {{ position:absolute; left:0; bottom:-1px; height:11px; padding:0 2px; border-radius:2px;
  background:rgba(4,6,12,0.88); font-family:{NUM_FONT}; font-size:8px; color:{INK};
  line-height:11px; z-index:2; }}
.lbname {{ display:inline-block; width:280px; font-size:12px; color:{INK_2}; vertical-align:middle;
  white-space:nowrap; overflow:hidden; }}
.lbres {{ display:inline-block; width:160px; text-align:right; font-family:{NUM_FONT}; font-size:14px;
  font-weight:700; color:{INK}; vertical-align:middle; }}
.ddpair {{ width:{inner}px; white-space:nowrap; }}
.ddbox {{ width:{inner}px; padding:8px; border-radius:12px; background:{SURFACE};
  border:1px solid {HAIR}; border-top:1px solid {HAIR_TOP}; box-sizing:border-box;
  display:inline-block; vertical-align:top; }}
.ddbox.half {{ width:{half}px; }}
.ddbox.half + .ddbox.half {{ margin-left:{DD_GAP}px; }}
.ddhead {{ height:24px; white-space:nowrap; margin-bottom:6px; }}
.ddwpic {{ width:20px; height:20px; display:inline-block; vertical-align:middle; }}
.ddtitle {{ display:inline-block; width:560px; font-size:12px; font-weight:700;
  vertical-align:middle; padding-left:4px; overflow:hidden; }}
.ddbox.half .ddtitle {{ width:252px; }}
.ddbar {{ width:{DD_BAR_W}px; height:14px; border-radius:4px; overflow:hidden;
  background:rgba(0,0,0,0.35); white-space:nowrap; }}
.ddbox.half .ddbar {{ width:{half_bar}px; }}
.ddseg {{ display:inline-flex; align-items:center; justify-content:center; height:14px;
  font-size:7px; color:#0b0d12; font-weight:700; overflow:hidden; vertical-align:top;
  box-sizing:border-box; }}
.ddlegend {{ margin-top:6px; width:{DD_BAR_W}px; }}
.ddbox.half .ddlegend {{ width:{half_bar}px; }}
.ddleg {{ display:inline-flex; align-items:center; justify-content:center; height:16px;
  padding:0 6px; margin:0 3px 3px 0; border-radius:3px; font-size:8px; font-weight:700;
  vertical-align:middle; color:#0b0d12; box-sizing:border-box; line-height:1; }}
.akey {{ display:inline-flex; align-items:center; justify-content:center; width:14px; height:14px;
  font-family:{NUM_FONT}; font-size:8px; font-weight:700; border:1px solid; border-radius:3px;
  vertical-align:middle; margin-right:2px; box-sizing:border-box; line-height:1; }}
.ddrx {{ display:inline-flex; align-items:center; justify-content:center; height:14px;
  padding:0 4px; margin-right:2px; font-size:8px; border-radius:3px; line-height:1;
  background:rgba(196,142,240,0.28); color:#e8d6ff; vertical-align:middle; box-sizing:border-box; }}
.ddlist {{ margin-top:4px; width:{DD_BAR_W}px; }}
.ddbox.half .ddlist {{ width:{half_bar}px; }}
.ddrow {{ height:18px; padding:0 2px; white-space:nowrap; }}
.ddrow.alt {{ background:rgba(0,0,0,0.22); border-radius:3px; }}
.ddqty {{ display:inline-block; width:36px; font-family:{NUM_FONT}; font-size:11px;
  vertical-align:middle; }}
.ddbox.half .ddqty {{ width:24px; font-size:10px; }}
.ddnm {{ display:inline-block; width:400px; font-size:11px; vertical-align:middle;
  overflow:hidden; }}
.ddbox.half .ddnm {{ width:168px; font-size:10px; }}
.ddval {{ display:inline-block; width:148px; font-family:{NUM_FONT}; font-size:12px;
  font-weight:700; text-align:right; vertical-align:middle; }}
.ddbox.half .ddval {{ width:80px; font-size:11px; }}
.ddfoot {{ height:22px; margin-top:4px; padding:4px 2px 0; border-top:1px solid {HAIR};
  white-space:nowrap; }}
.ddftlab {{ display:inline-block; width:436px; font-size:12px; font-weight:700;
  vertical-align:middle; color:{INK_2}; }}
.ddbox.half .ddftlab {{ width:192px; }}
.ddftval {{ display:inline-block; width:148px; text-align:right; font-family:{NUM_FONT};
  font-size:14px; font-weight:700; vertical-align:middle; }}
.ddbox.half .ddftval {{ width:80px; font-size:13px; }}
.grlist {{ width:{inner}px; }}
.grcard {{ width:{inner}px; height:56px; margin-top:4px; padding:4px 8px; border-radius:8px;
  background:{SURFACE}; border:1px solid {HAIR}; box-sizing:border-box; white-space:nowrap; }}
.grcard.on {{ border:1px solid {accent}; background:rgba(12,18,28,0.72); }}
.gridx {{ display:inline-block; width:78px; height:48px; vertical-align:middle; }}
.grno {{ display:block; font-family:{NUM_FONT}; font-size:13px; font-weight:700; line-height:1.2; }}
.grreg {{ display:inline-flex; align-items:center; justify-content:center; height:14px;
  padding:0 5px; margin-top:4px; border-radius:3px; font-size:9px; font-weight:700;
  color:#fff; box-sizing:border-box; line-height:1; }}
.grwho {{ display:inline-block; width:128px; height:48px; vertical-align:middle; }}
.grnick {{ display:block; font-size:12px; font-weight:700; line-height:1.2; overflow:hidden; }}
.gruid {{ display:block; font-size:10px; color:{INK_3}; line-height:1.3; margin-top:3px; }}
.grface {{ display:inline-block; position:relative; width:40px; height:40px; vertical-align:middle;
  border-radius:8px; overflow:hidden; border:1px solid {HAIR}; }}
.grface img {{ width:40px; height:40px; object-fit:cover; }}
.grfc {{ position:absolute; left:0; bottom:0; height:12px; padding:0 3px; border-radius:0 4px 0 0;
  background:rgba(4,6,12,0.82); font-family:{NUM_FONT}; font-size:8px; color:{INK};
  display:flex; align-items:center; justify-content:center; box-sizing:border-box; line-height:1; }}
.grcrit {{ display:inline-block; width:96px; height:48px; vertical-align:middle; padding-left:8px; }}
.grcr {{ display:block; font-family:{NUM_FONT}; font-size:12px; font-weight:700; line-height:1.2; }}
.grcv {{ display:block; font-size:10px; color:#c48ef0; line-height:1.3; margin-top:3px; }}
.grst {{ display:inline-block; width:130px; height:48px; vertical-align:middle; }}
.grhp, .gratk {{ display:block; font-size:11px; line-height:1.35; color:{INK_2}; }}
.grst img {{ width:12px; height:12px; display:inline-block; vertical-align:middle; margin-right:3px; }}
.grst b {{ font-family:{NUM_FONT}; font-weight:700; color:{INK}; }}
.grbad {{ display:inline-block; width:88px; height:48px; text-align:right; vertical-align:middle;
  line-height:48px; }}
.grcon {{ display:inline-flex; align-items:center; justify-content:center; height:18px;
  padding:0 6px; border-radius:3px; font-size:10px; font-weight:700; background:#c43c3c;
  color:#fff; vertical-align:middle; box-sizing:border-box; line-height:1; }}
.grcon.dim {{ background:rgba(255,255,255,0.12); color:{INK_2}; }}
.grref {{ display:inline-flex; align-items:center; justify-content:center; height:18px;
  padding:0 6px; margin-left:4px; border-radius:3px; font-size:10px; font-weight:700;
  background:rgba(234,198,131,0.22); color:#eac683; vertical-align:middle;
  box-sizing:border-box; line-height:1; }}
.sidefoot {{ height:16px; text-align:center; font-size:10px; color:{INK_3}; margin-top:8px; }}
"""


def akasha_side_html(
    board: Mapping[str, object] | None,
    rows: list[Mapping[str, object]],
    *,
    accent: str,
    char_icons: Mapping[str, str],
    weapon_icons: Mapping[str, str],
    dist: Mapping[str, object] | None = None,
    boards: list[Mapping[str, object]] | None = None,
    dists: list[Mapping[str, object]] | None = None,
    ranks: list[Mapping[str, object]] | None = None,
    self_uid: str = "",
    target_height: int = 0,
    section_icons: Mapping[str, str] | None = None,
) -> str:
    """拼右侧整栏。``board`` / ``rows`` / 伤害拆分皆空则返回空串。"""
    board_list: list[Mapping[str, object]] = []
    if boards is not None:
        board_list = [item for item in boards if item is not None]
    elif board is not None:
        board_list = [board]
    dist_list: list[Mapping[str, object]] = []
    if dists is not None:
        dist_list = [item for item in dists if item is not None]
    elif dist is not None:
        dist_list = [dist]
    show_gain_cap = len(board_list) > 1
    gain_blocks: list[str] = []
    for item in board_list:
        tab = _substat_table(item, caption=show_gain_cap)
        if tab:
            gain_blocks.append(f'<div class="spbox">{tab}</div>')
    table = "".join(gain_blocks)
    compact = len(dist_list) >= 2
    dist_bits: list[str] = []
    for item in dist_list[:SIDE_LOADOUTS]:
        block = _dist_html(item, accent, weapon_icons=weapon_icons, compact=compact)
        if block:
            dist_bits.append(block)
    dist_html = "".join(dist_bits)
    if compact and dist_html:
        dist_html = f'<div class="ddpair">{dist_html}</div>'
    selected = {_calc_key(_as_str(item["calculation_id"])) for item in board_list if "calculation_id" in item}
    listing = _leaderboard_list(rows, selected, char_icons, weapon_icons, accent)
    rank_list = pick_nearby_ranks(ranks if ranks is not None else [], self_uid)
    if target_height > 0:
        used = estimate_side_used(
            _max_dist_parts(dist_list[:SIDE_LOADOUTS]),
            [_gain_row_count(item) for item in board_list],
            len(rows),
        )
        n_rank = count_rank_slots(target_height, used, len(rank_list))
        rank_list = rank_list[:n_rank]
    rank_html = _rank_list(rank_list, self_uid, section_icons if section_icons is not None else {})
    if not table and not listing and not dist_html and not rank_html:
        return ""
    icons = section_icons if section_icons is not None else {}
    head = _side_head(board_list[0] if board_list else None)
    parts = ['<div class="side">', head, '<div class="sidein">']
    first = " first"
    if dist_html:
        parts.append(f'<div class="smod{first}">')
        parts.append(_sec("伤害分布", "DMG", icons["dist"] if "dist" in icons else "", accent))
        parts.append(dist_html)
        parts.append("</div>")
        first = ""
    if table:
        parts.append(f'<div class="smod{first}">')
        parts.append(_sec("副词条收益", "GAIN", icons["gain"] if "gain" in icons else "", accent))
        parts.append(table)
        parts.append("</div>")
        first = ""
    if listing:
        parts.append(f'<div class="smod{first}">')
        parts.append(_sec("队伍榜", "TEAM", icons["teams"] if "teams" in icons else "", accent))
        parts.append(f'<div class="lblist">{listing}</div>')
        parts.append("</div>")
        first = ""
    if rank_html:
        parts.append(f'<div class="smod{first}">')
        parts.append(_sec("全球排名", "RANK", icons["rank"] if "rank" in icons else "", accent))
        parts.append(f'<div class="grlist">{rank_html}</div>')
        parts.append("</div>")
    parts.append("</div>")
    parts.append('<div class="sidefoot">akasha.cv</div>')
    parts.append("</div>")
    return "".join(parts)


def _esc(text: str) -> str:
    return html.escape(text)


def _as_str(raw: object, default: str = "") -> str:
    if isinstance(raw, str):
        return raw
    return default


def _as_float(raw: object) -> float | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    return None


def _as_int(raw: object) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer():
        return int(raw)
    return None


def _side_head(board: Mapping[str, object] | None) -> str:
    title = "Akasha"
    sub = "当前配装模拟"
    if board is not None:
        short = zh_text(_as_str(board["short"] if "short" in board else ""))
        variant = zh_text(_as_str(board["variant"] if "variant" in board else ""))
        weapon = zh_text(_as_str(board["weapon_name"] if "weapon_name" in board else ""))
        bits = [p for p in (short, variant, weapon) if p]
        if bits:
            sub = " · ".join(bits)
    return f'<div class="sidehead"><div class="shtitle">{_esc(title)}</div><div class="shsub">{_esc(sub)}</div></div>'


def _rgba(color: str, alpha: float) -> str:
    h = color.lstrip("#")
    if len(h) != 6:
        return color
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _sec(title: str, en: str, icon: str, accent: str) -> str:
    ic = f'<img class="secic" src="{icon}"/>' if icon else ""
    return (
        '<div class="sec">'
        f'<div class="secbar" style="background:{accent}"></div>'
        '<div class="secbox">'
        f"{ic}"
        f'<div class="sect">{_esc(title)}</div>'
        f'<div class="secen" style="color:{accent};background:{_rgba(accent, 0.16)};'
        f'border-color:{_rgba(accent, 0.42)}">{_esc(en)}</div>'
        "</div></div>"
    )


def _type_color(part_type: str) -> str:
    if part_type in _TYPE_COLOR:
        return _TYPE_COLOR[part_type]
    return "#8b919c"


def _akey_html(kind: str) -> str:
    if not kind or kind not in _AKEY_COLOR:
        return ""
    color = _AKEY_COLOR[kind]
    return f'<span class="akey" style="color:{color};border-color:{color}">{kind}</span>'


def _rx_html(tag: str) -> str:
    if not tag:
        return ""
    return f'<span class="ddrx">{_esc(tag)}</span>'


def _fmt_qty(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:g}"


def _part_label(name: str) -> str:
    zh = zh_text(name)
    for suffix in (" · 平均伤害", "平均伤害"):
        if zh.endswith(suffix):
            zh = zh[: -len(suffix)].rstrip(" ·")
            break
    return zh


def _loadout_cap(item: Mapping[str, object]) -> str:
    weapon = zh_text(_as_str(item["weapon_name"] if "weapon_name" in item else ""))
    short = zh_text(_as_str(item["short"] if "short" in item else ""))
    variant = zh_text(_as_str(item["variant"] if "variant" in item else ""))
    return " · ".join(p for p in (weapon, short, variant) if p)


def _dist_html(
    dist: Mapping[str, object],
    accent: str,
    *,
    weapon_icons: Mapping[str, str],
    compact: bool = False,
) -> str:
    raw_parts = dist["parts"] if "parts" in dist else None
    result = _as_float(dist["result"] if "result" in dist else None)
    if not isinstance(raw_parts, list) or result is None:
        return ""
    parts: list[Mapping[str, object]] = []
    for item in raw_parts:
        if isinstance(item, dict):
            parts.append(item)
    if not parts:
        return ""
    formula_sum = _as_float(dist["formula_sum"] if "formula_sum" in dist else None)
    if formula_sum is None or formula_sum <= 0:
        formula_sum = result
    bar_w = (SIDE_INNER - DD_GAP) // 2 - 16 if compact else DD_BAR_W
    rows: list[str] = []
    grouped: dict[str, float] = {}
    order: list[str] = []
    for part in parts:
        total = _as_float(part["total"] if "total" in part else None)
        qty = _as_float(part["quantity"] if "quantity" in part else None)
        ptype = _as_str(part["type"] if "type" in part else "")
        if total is None or qty is None or total <= 0:
            continue
        color = _type_color(ptype)
        raw_name = _as_str(part["name"] if "name" in part else "")
        pname = _part_label(raw_name)
        key = type_key(ptype)
        rx = reaction_tag(raw_name, ptype)
        prefix = f"{_akey_html(key)}{_rx_html(rx)}"
        alt = " alt" if len(rows) % 2 else ""
        rows.append(
            f'<div class="ddrow{alt}">'
            f'<span class="ddqty" style="color:{color}">{_esc(_fmt_qty(qty))}×</span>'
            f'<span class="ddnm" style="color:{color}">{prefix}{_esc(pname)}</span>'
            f'<span class="ddval" style="color:{color}">{_esc(fmt_result(total))}</span>'
            "</div>"
        )
        if ptype in grouped:
            grouped[ptype] = grouped[ptype] + total
        else:
            grouped[ptype] = total
            order.append(ptype)
    if not rows:
        return ""
    segs: list[str] = []
    used = 0
    n = len(order)
    for i, ptype in enumerate(order):
        total = grouped[ptype]
        if i == n - 1:
            px = max(0, bar_w - used)
        else:
            px = int(round(bar_w * total / formula_sum))
            left = n - i - 1
            px = max(2, min(px, bar_w - used - 2 * left))
            used += px
        color = _type_color(ptype)
        label = zh_text(ptype) if ptype else ""
        inner = _esc(label) if label and px >= 14 * max(2, len(label)) else ""
        segs.append(f'<span class="ddseg" style="width:{px}px;background:{color}">{inner}</span>')
    legend_bits: list[str] = []
    for ptype in order:
        pct = 100.0 * grouped[ptype] / formula_sum
        color = _type_color(ptype)
        legend_bits.append(f'<span class="ddleg" style="background:{color}">{_esc(zh_text(ptype))} {pct:.1f}%</span>')
    cap = _loadout_cap(dist)
    wid = _as_str(dist["weapon_id"] if "weapon_id" in dist else "")
    src = weapon_icons[wid] if wid in weapon_icons else ""
    img = f'<img class="ddwpic" src="{src}"/>' if src else ""
    title = cap if cap else "伤害分布"
    box = "ddbox half" if compact else "ddbox"
    return (
        f'<div class="{box}">'
        f'<div class="ddhead">{img}<span class="ddtitle">{_esc(title)}</span></div>'
        f'<div class="ddbar">{"".join(segs)}</div>'
        f'<div class="ddlegend">{"".join(legend_bits)}</div>'
        f'<div class="ddlist">{"".join(rows)}</div>'
        '<div class="ddfoot">'
        f'<span class="ddftlab">总伤</span>'
        f'<span class="ddftval" style="color:{accent}">{_esc(fmt_result(result))}</span>'
        "</div>"
        "</div>"
    )


def _gain_pct(item: Mapping[str, object]) -> float:
    raw = _as_float(item["pct_gain"] if "pct_gain" in item else None)
    if raw is None:
        return 0.0
    return raw


def _substat_table(board: Mapping[str, object], *, caption: bool = False) -> str:
    gains_raw = board["gains"] if "gains" in board else None
    if not isinstance(gains_raw, list) or not gains_raw:
        return ""
    gains: list[Mapping[str, object]] = []
    for item in gains_raw:
        if isinstance(item, dict):
            gains.append(item)
    if not gains:
        return ""
    base_result = _as_float(board["base_result"] if "base_result" in board else None)
    base_rank = _as_int(board["base_rank"] if "base_rank" in board else None)
    if base_result is None or base_rank is None:
        return ""
    ordered = sorted(gains, key=_gain_pct, reverse=True)
    rows = [
        '<div class="sgbase">'
        f'<span class="sgbname">{_esc(substat_zh("Base"))}</span>'
        f'<span class="sgbval">{_esc(fmt_result(base_result))}</span>'
        f'<span class="sgbrank">#{_esc(fmt_rank(base_rank))}</span>'
        "</div>"
    ]
    for i, gain in enumerate(ordered):
        name = _as_str(gain["name"] if "name" in gain else "")
        if not name:
            continue
        dmg = _as_float(gain["dmg_gain"] if "dmg_gain" in gain else None)
        pct = _as_float(gain["pct_gain"] if "pct_gain" in gain else None)
        new_rank = _as_int(gain["new_rank"] if "new_rank" in gain else None)
        roll = _as_float(gain["roll"] if "roll" in gain else None)
        if dmg is None or pct is None or new_rank is None:
            continue
        roll_s = fmt_roll(name, roll) if roll is not None else ""
        dmg_cls = gain_class(dmg)
        pct_cls = gain_class(pct)
        alt = " alt" if i % 2 == 0 else ""
        dmg_attr = f"sgdmg {dmg_cls}".strip()
        pct_attr = f"sgpct {pct_cls}".strip()
        rows.append(
            f'<div class="sgrow{alt}">'
            f'<span class="sgname">{_esc(substat_zh(name))}</span>'
            f'<span class="sgroll">{_esc(roll_s)}</span>'
            f'<span class="{dmg_attr}">{_esc(fmt_dmg_gain(dmg))}</span>'
            f'<span class="{pct_attr}">{_esc(fmt_pct_gain(pct))}</span>'
            f'<span class="sgrank">→ {_esc(fmt_rank(new_rank))}</span>'
            "</div>"
        )
    cap = _loadout_cap(board) if caption else ""
    cap_html = f'<div class="sgcap">{_esc(cap)}</div>' if cap else ""
    return f'{cap_html}<div class="sptab">{"".join(rows)}</div>'


def _leaderboard_list(
    rows: list[Mapping[str, object]],
    selected: set[str],
    char_icons: Mapping[str, str],
    weapon_icons: Mapping[str, str],
    accent: str,
) -> str:
    cards: list[str] = []
    for row in rows:
        card = _leaderboard_card(row, selected, char_icons, weapon_icons, accent)
        if card:
            cards.append(card)
    return "".join(cards)


def _leaderboard_card(
    row: Mapping[str, object],
    selected: set[str],
    char_icons: Mapping[str, str],
    weapon_icons: Mapping[str, str],
    accent: str,
) -> str:
    calc_id = _as_str(row["calculation_id"] if "calculation_id" in row else "")
    ranking = _as_int(row["ranking"] if "ranking" in row else None)
    out_of = _as_int(row["out_of"] if "out_of" in row else None)
    top_pct = _as_float(row["top_pct"] if "top_pct" in row else None)
    result = _as_float(row["result"] if "result" in row else None)
    name = _as_str(row["name"] if "name" in row else "")
    if ranking is None or out_of is None or top_pct is None or result is None or not name:
        return ""
    variant = _as_str(row["variant_display"] if "variant_display" in row else "")
    if not variant:
        variant = _as_str(row["variant_name"] if "variant_name" in row else "")
    weapon = row["weapon"] if "weapon" in row and isinstance(row["weapon"], dict) else None
    wpn_html = _weapon_cell(weapon, weapon_icons)
    portraits = _portraits(row, char_icons)
    on = " on" if calc_id and _calc_key(calc_id) in selected else ""
    name_zh = zh_text(name)
    var_zh = zh_text(variant)
    label = f"{name_zh} · {var_zh}" if var_zh else name_zh
    return (
        f'<div class="lbcard{on}">'
        '<div class="lb1">'
        f'<span class="lbrank">{_esc(fmt_rank(ranking))} / {_esc(fmt_out_of(out_of))}</span>'
        f'<span class="lbtopn" style="color:{top_pct_color(top_pct)}">{_esc(fmt_top_pct(top_pct))}</span>'
        f'<span class="lbwpn">{wpn_html}</span>'
        "</div>"
        '<div class="lb2">'
        f'<span class="lbtms">{portraits}</span>'
        f'<span class="lbname">{_esc(label)}</span>'
        f'<span class="lbres">{_esc(fmt_result(result))}</span>'
        "</div>"
        "</div>"
    )


def _weapon_cell(weapon: Mapping[str, object] | None, weapon_icons: Mapping[str, str]) -> str:
    if weapon is None:
        return ""
    refinement = _as_int(weapon["refinement"] if "refinement" in weapon else None)
    weapon_id = _as_str(weapon["weaponId"] if "weaponId" in weapon else "")
    src = weapon_icons[weapon_id] if weapon_id in weapon_icons else ""
    img = f'<img src="{src}"/>' if src else ""
    ref = f"R{refinement}" if refinement is not None else ""
    wname = zh_text(_as_str(weapon["name"] if "name" in weapon else ""))
    bits = [p for p in (img, ref, _esc(wname)) if p]
    return "<span>" + " ".join(bits) + "</span>"


def _portraits(row: Mapping[str, object], char_icons: Mapping[str, str]) -> str:
    raw = row["teammates"] if "teammates" in row else None
    mates: list[Mapping[str, object]] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                mates.append(item)
    slots: list[str] = []
    for mate in mates[:TEAM_SLOTS]:
        slots.append(_portrait(mate, char_icons))
    return "".join(slots)


def _portrait(mate: Mapping[str, object], char_icons: Mapping[str, str]) -> str:
    character = mate["character"] if "character" in mate and isinstance(mate["character"], dict) else None
    if character is None:
        return ""
    name = _as_str(character["name"] if "name" in character else "")
    src = char_icons[name] if name in char_icons else ""
    letter = zh_text(name)[:1] if name else "?"
    face = f'<img src="{src}"/>' if src else f'<span class="tmph">{_esc(letter)}</span>'
    rarity = _as_int(character["rarity"] if "rarity" in character else None)
    rcls = " r5"
    if rarity == 4:
        rcls = " r4"
    elif rarity == 3:
        rcls = " r3"
    badge = ""
    constellation = _as_int(character["constellation"] if "constellation" in character else None)
    if constellation is not None:
        badge = f'<span class="tmc">C{constellation}</span>'
    return f'<span class="tm"><span class="tmface{rcls}">{face}<span class="tmstar"></span></span>{badge}</span>'


def _rank_list(
    rows: list[Mapping[str, object]],
    self_uid: str,
    icons: Mapping[str, str],
) -> str:
    cards: list[str] = []
    for row in rows:
        card = _rank_card(row, self_uid, icons)
        if card:
            cards.append(card)
    return "".join(cards)


def _rank_card(
    row: Mapping[str, object],
    self_uid: str,
    icons: Mapping[str, str],
) -> str:
    rank = _as_int(row["rank"] if "rank" in row else None)
    uid = _as_str(row["uid"] if "uid" in row else "")
    if rank is None:
        return ""
    nickname = _as_str(row["nickname"] if "nickname" in row else "")
    region = _as_str(row["region"] if "region" in row else "")
    constellation = _as_int(row["constellation"] if "constellation" in row else None)
    if constellation is None:
        constellation = 0
    refinement = _as_int(row["refinement"] if "refinement" in row else None)
    if refinement is None:
        refinement = 1
    crit_rate = _as_float(row["crit_rate"] if "crit_rate" in row else None)
    crit_dmg = _as_float(row["crit_dmg"] if "crit_dmg" in row else None)
    cv = _as_float(row["cv"] if "cv" in row else None)
    hp = _as_float(row["hp"] if "hp" in row else None)
    atk = _as_float(row["atk"] if "atk" in row else None)
    face = icons["face"] if "face" in icons else ""
    hp_ic = icons["hp"] if "hp" in icons else ""
    atk_ic = icons["atk"] if "atk" in icons else ""
    img = f'<img src="{face}"/>' if face else ""
    hp_img = f'<img src="{hp_ic}"/>' if hp_ic else ""
    atk_img = f'<img src="{atk_ic}"/>' if atk_ic else ""
    on = " on" if self_uid and uid == self_uid else ""
    nick = nickname if nickname else uid
    reg_bg = _REGION_BG[region] if region in _REGION_BG else "rgba(255,255,255,0.18)"
    reg = f'<span class="grreg" style="background:{reg_bg}">{_esc(region)}</span>' if region else ""
    con_cls = "grcon" if constellation >= 6 else "grcon dim"
    cr_s = f"{fmt_ratio(crit_rate)}:{fmt_ratio(crit_dmg)}" if crit_rate is not None and crit_dmg is not None else ""
    cv_s = f"{cv:.1f} cv" if cv is not None and cv > 0 else ""
    hp_s = str(int(round(hp))) if hp is not None and hp > 0 else "—"
    atk_s = str(int(round(atk))) if atk is not None and atk > 0 else "—"
    return (
        f'<div class="grcard{on}">'
        f'<span class="gridx"><span class="grno">#{rank}名</span>{reg}</span>'
        f'<span class="grwho"><span class="grnick">{_esc(nick)}</span>'
        f'<span class="gruid">UID {uid}</span></span>'
        f'<span class="grface">{img}<span class="grfc">C{constellation}</span></span>'
        f'<span class="grcrit"><span class="grcr">{_esc(cr_s)}</span>'
        f'<span class="grcv">{_esc(cv_s)}</span></span>'
        f'<span class="grst"><span class="grhp">{hp_img}生命: <b>{_esc(hp_s)}</b></span>'
        f'<span class="gratk">{atk_img}攻击: <b>{_esc(atk_s)}</b></span></span>'
        f'<span class="grbad"><span class="{con_cls}">{_esc(fmt_con(constellation))}</span>'
        f'<span class="grref">{_esc(fmt_ref(refinement))}</span></span>'
        "</div>"
    )
