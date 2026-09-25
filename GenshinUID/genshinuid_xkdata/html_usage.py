"""深渊 / 危战使用率 HTML，栏位结构对齐深渊信息。"""

from __future__ import annotations

from pathlib import Path

from .usage_rank import (
    SHOW_TEAM_SLOTS,
    UsageSide,
    UsageSnapshot,
    pct,
    visible_characters,
    hard_difficulty_samples,
)
from ..genshinuid_guide.html_endgame import _esc, _chips, _render, _file_uri

_PAGE_W = 890
_ABYSS_W = 846

_ABYSS_BANNER = Path(__file__).parent / "texture2d" / "abyss_banner.png"
_HARD_BANNER = Path(__file__).resolve().parents[1] / "genshinuid_hard_challenge" / "texture2d" / "bg.jpg"

_EXTRA = """
<style>
.lane { display:flex; flex-direction:column; gap:4px; }
.lanerow { display:flex; gap:8px; align-items:flex-start; }
.laneleft, .laneright { flex:0 0 auto; }
.cgrid { display:grid; grid-template-columns:repeat(3, 172px); justify-content:start; gap:4px 18px; }
.ccell { display:flex; align-items:center; gap:4px; width:172px; height:34px; }
.umeta { flex:0 0 auto; display:grid; grid-template-columns:64px 66px; grid-template-rows:auto auto;
  column-gap:4px; row-gap:0; align-items:center; }
.umeta .uname { font-size:12px; line-height:14px; font-weight:700; white-space:nowrap;
  overflow:hidden; text-overflow:ellipsis; }
.umeta .side { text-align:left; line-height:12px; font-size:10px; }
.umeta .use { width:100%; text-align:right; line-height:12px; font-size:10px; white-space:nowrap;
  color:rgba(242,245,251,0.62); }
.umeta .chg { justify-self:end; }
.urow { display:flex; align-items:center; gap:6px; margin-top:6px; }
.uface { width:32px; height:32px; border-radius:8px; object-fit:cover; flex-shrink:0;
  background:rgba(0,0,0,0.35); border:1px solid rgba(255,255,255,0.16); }
.uface.s5 { border-color:#eac683; }
.uface.s4 { border-color:#b98cf5; }
.uname { font-size:12px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.usub { font-size:10px; line-height:1.35; color:rgba(242,245,251,0.62); }
.glab { margin:8px 0 12px; font-size:15px; font-weight:700; font-style:italic; letter-spacing:1px; }
.glab .gt, .half .gt { color:#fff; }
.glab.char .brk { color:#c59bff; }
.glab.team .brk { color:#f0a04a; }
.half { display:flex; align-items:center; gap:12px; margin:16px 2px 14px;
  font-size:22px; font-weight:700; font-style:italic; letter-spacing:1px; color:#fff; }
.half .brk { color:#ec6a48; }
.hline { flex:1; height:1px; background:rgba(255,255,255,0.28); }
.ubanner { position:relative; overflow:hidden; border-radius:14px; min-height:168px;
  border:1px solid rgba(255,255,255,0.08); border-top:1px solid rgba(255,255,255,0.18); }
.ubg { position:absolute; left:0; top:0; width:100%; height:100%; object-fit:cover; z-index:0; }
.ubg.abyss { object-position:center 42%; }
.ubg.hard { object-fit:cover; object-position:center 13%; filter:brightness(1.35) saturate(1.25); }
.uveil { position:absolute; left:0; right:0; top:0; bottom:0; z-index:1;
  background:linear-gradient(90deg,rgba(5,6,12,0.78) 0%,rgba(5,6,12,0.28) 42%,rgba(5,6,12,0.05) 100%); }
.uin { position:relative; z-index:2; min-height:168px; display:flex; flex-direction:row;
  align-items:flex-end; justify-content:space-between; gap:18px; padding:16px 20px; }
.uleft { min-width:0; flex:1; }
.uright { margin-left:auto; max-width:58%; display:flex; flex-direction:column;
  align-items:flex-end; text-align:right; gap:8px; }
.uright .hchips { justify-content:flex-end; }
.uright .hdesc { text-align:right; }
.ukicker { font-size:13px; font-style:italic; letter-spacing:2px; }
.utitle { font-size:40px; font-weight:700; font-style:italic; letter-spacing:1px; line-height:1.15; margin-top:2px; }
.usubline { margin-top:6px; font-size:18px; font-weight:700; font-style:italic; color:#eac683; }
.tlist { display:flex; flex-direction:column; gap:4px; }
.trow { display:flex; align-items:center; gap:10px; height:34px; }
.tmeta { width:68px; flex:0 0 68px; text-align:right; line-height:1.05; font-size:11px;
  white-space:nowrap; color:rgba(242,245,251,0.78); }
.tmeta.wide { width:112px; flex-basis:112px; }
.tmeta .num { font-size:13px; }
.ticons { display:flex; gap:4px; }
.chg { flex:0 0 auto; padding:0 4px; border-radius:4px; font-size:10px; font-weight:700; line-height:14px; }
.chg.up { color:#ec6a48; background:rgba(236,106,72,0.18); }
.chg.down { color:#79d4ec; background:rgba(121,212,236,0.16); }
.chg.new { color:#eac683; background:rgba(234,198,131,0.18); }
.lag { color:#ec6a48; font-weight:700; }
</style>
"""


def _mark(kind: str, text: str) -> str:
    return (
        f'<div class="glab {kind}"><span class="brk">[</span>'
        f'<span class="gt"> {text} </span><span class="brk">]</span></div>'
    )


def _lane_title(name: str) -> str:
    label = _esc(name)
    return (
        '<div class="half"><span class="hline"></span>'
        f'<span class="brk">[</span><span class="gt"> {label} </span><span class="brk">]</span>'
        '<span class="hline"></span></div>'
    )


def _face(name: str, star: int, faces: dict[str, str]) -> str:
    kind = "s5" if star >= 5 else "s4"
    uri = faces[name] if name in faces else ""
    if uri:
        return f'<img class="uface {kind}" src="{uri}" alt="{_esc(name)}"/>'
    return f'<div class="uface {kind}"></div>'


def _change_html(value: float) -> str:
    if value > 0:
        return f'<span class="chg up">↑{pct(value)}%</span>'
    if value < 0:
        return f'<span class="chg down">↓{pct(abs(value))}%</span>'
    return '<span class="chg new">NEW!</span>'


def _side_panel(side: UsageSide, faces: dict[str, str]) -> str:
    chars: list[str] = []
    for char in visible_characters(side["characters"]):
        chars.append(
            '<div class="ccell">'
            f"{_face(char['name'], char['star'], faces)}"
            '<div class="umeta">'
            f'<div class="uname">{_esc(char["name"])}</div>'
            f"{_change_html(char['use_rate_change'])}"
            f'<span class="side num">{pct(char["side_rate"])}%</span>'
            f'<span class="use">使用{pct(char["use_rate"])}%</span>'
            "</div></div>"
        )
    teams: list[str] = []
    for team in side["teams"][:SHOW_TEAM_SLOTS]:
        icons = "".join(_face(member["name"], member["star"], faces) for member in team["members"])
        clock = f" {pct(team['time'])}s" if team["time"] > 0 else ""
        wide = " wide" if clock else ""
        teams.append(
            f'<div class="trow"><div class="ticons">{icons}</div>'
            f'<div class="tmeta{wide}">'
            f'<div><span class="num">{pct(team["use_rate"])}%</span>{clock}</div>'
            f"<div>本侧{team['side_pct']}%</div></div></div>"
        )
    char_html = (
        f'<div class="cgrid">{"".join(chars)}</div>' if chars else '<div class="empty">这一侧没有角色样本。</div>'
    )
    empty = '<div class="empty">这一侧没有队伍样本。</div>'
    team_html = f'<div class="tlist">{"".join(teams)}</div>' if teams else empty
    char_lab = _mark("char", "角色出场")
    team_lab = _mark("team", "热门队伍")
    return (
        '<div class="lane">'
        f"{_lane_title(side['name'])}"
        '<div class="lanerow">'
        f'<div class="panel laneleft">{char_lab}{char_html}</div>'
        f'<div class="panel laneright">{team_lab}{team_html}</div>'
        "</div></div>"
    )


def _banner(kind: str, title: str, sub: str, chips: str, desc: str) -> str:
    hard = kind == "hard"
    path = _HARD_BANNER if hard else _ABYSS_BANNER
    uri = _file_uri(path)
    mark = "hard" if hard else "abyss"
    art = f'<img class="ubg {mark}" src="{uri}"/>' if uri else ""
    veil = '<div class="uveil"></div>' if uri else ""
    kicker = "STYGIAN ONSLAUGHT" if hard else "SPIRAL ABYSS"
    accent = "#7dcea0" if hard else "#eac683"
    body = f'<div class="hdesc">{desc}</div>' if desc else ""
    return (
        f'<div class="ubanner">{art}{veil}<div class="uin">'
        '<div class="uleft">'
        f'<div class="ukicker" style="color:{accent}">{_esc(kicker)}</div>'
        f'<div class="utitle">{_esc(title)}</div>'
        f'<div class="usubline">{_esc(sub)}</div></div>'
        f'<div class="uright">{chips}{body}</div></div></div>'
    )


def _sample_chips(snapshot: UsageSnapshot) -> list[tuple[str, bool]]:
    if snapshot["kind"] == "hard":
        pair = hard_difficulty_samples(snapshot["tips"])
        if pair is not None:
            level5, level6 = pair
            return [(f"N5 {level5}", False), (f"N6 {level6}", False)]
    text = f"样本 {snapshot['sample']}" if snapshot["sample"] else ""
    return [(text, False)]


def usage_inner(snapshot: UsageSnapshot, align: str, lagged: bool, faces: dict[str, str]) -> str:
    hard = snapshot["kind"] == "hard"
    chips = _chips(
        [
            (snapshot["last_update"], False),
            (snapshot["window_text"], False),
            *_sample_chips(snapshot),
            ("滞后" if lagged else "", True),
        ]
    )
    desc = ""
    if lagged:
        lag = f'<span class="lag">{_esc(align)}</span>'
        desc = f"{desc}<br>{lag}" if desc else lag
    hero = _banner(
        snapshot["kind"],
        "危战使用率" if hard else "深渊使用率",
        snapshot["title"] or snapshot["version_label"],
        chips,
        desc,
    )
    lanes = "".join(_side_panel(side, faces) for side in snapshot["sides"])
    return f'{_EXTRA}<div class="mod">{hero}{lanes}</div>'


async def render_usage_image(
    snapshot: UsageSnapshot,
    align: str,
    lagged: bool,
    faces: dict[str, str],
) -> bytes:
    accent = "#7dcea0" if snapshot["kind"] == "hard" else "#e7c27a"
    page_w = _PAGE_W if snapshot["kind"] == "hard" else _ABYSS_W
    return await _render(accent, usage_inner(snapshot, align, lagged, faces), page_w)
