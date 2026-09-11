from __future__ import annotations

import sys
import json
import types
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_CV = _ROOT / "GenshinUID" / "utils" / "api" / "cv"
_SIDE = _ROOT / "GenshinUID" / "genshinuid_enka" / "akasha_side.py"
_FIXTURE = _ROOT / "test_output" / "gs_detail" / "akasha_side.json"

_MODELS_SPEC = spec_from_file_location("akasha_cv_models", _CV / "models.py")
assert _MODELS_SPEC is not None and _MODELS_SPEC.loader is not None
_MODELS = module_from_spec(_MODELS_SPEC)
sys.modules["akasha_cv_models"] = _MODELS
_MODELS_SPEC.loader.exec_module(_MODELS)

_pkg = types.ModuleType("akasha_cv")
_pkg.models = _MODELS
sys.modules["akasha_cv"] = _pkg
sys.modules["akasha_cv.models"] = _MODELS

_SP_SPEC = spec_from_file_location(
    "akasha_cv.substat_priority",
    _CV / "substat_priority.py",
    submodule_search_locations=[str(_CV)],
)
assert _SP_SPEC is not None and _SP_SPEC.loader is not None
_SP = module_from_spec(_SP_SPEC)
sys.modules["akasha_cv.substat_priority"] = _SP
_SP_SPEC.loader.exec_module(_SP)

_LB_SPEC = spec_from_file_location(
    "akasha_cv.build_leaderboards",
    _CV / "build_leaderboards.py",
    submodule_search_locations=[str(_CV)],
)
assert _LB_SPEC is not None and _LB_SPEC.loader is not None
_LB = module_from_spec(_LB_SPEC)
sys.modules["akasha_cv.build_leaderboards"] = _LB
_LB_SPEC.loader.exec_module(_LB)

_DD_SPEC = spec_from_file_location(
    "akasha_cv.damage_distribution",
    _CV / "damage_distribution.py",
    submodule_search_locations=[str(_CV)],
)
assert _DD_SPEC is not None and _DD_SPEC.loader is not None
_DD = module_from_spec(_DD_SPEC)
sys.modules["akasha_cv.damage_distribution"] = _DD
_DD_SPEC.loader.exec_module(_DD)

_SIDE_SPEC = spec_from_file_location("akasha_side", _SIDE)
assert _SIDE_SPEC is not None and _SIDE_SPEC.loader is not None
_MOD = module_from_spec(_SIDE_SPEC)
sys.modules["akasha_side"] = _MOD
_SIDE_SPEC.loader.exec_module(_MOD)

parse_substat_priority_payload = _SP.parse_substat_priority_payload
compute_substat_priority_boards = _SP.compute_substat_priority_boards
parse_build_leaderboards_payload = _LB.parse_build_leaderboards_payload
list_visible_leaderboards = _LB.list_visible_leaderboards
extract_build_md5 = _LB.extract_build_md5
parse_damage_distribution_payload = _DD.parse_damage_distribution_payload
find_damage_distribution = _DD.find_damage_distribution

akasha_side_html = _MOD.akasha_side_html
akasha_side_css = _MOD.akasha_side_css
pick_priority_board = _MOD.pick_priority_board
pick_loadout_ids = _MOD.pick_loadout_ids
match_calc_board = _MOD.match_calc_board
count_rank_slots = _MOD.count_rank_slots
pick_nearby_ranks = _MOD.pick_nearby_ranks
type_key = _MOD.type_key
reaction_tag = _MOD.reaction_tag
fmt_con = _MOD.fmt_con
fmt_ref = _MOD.fmt_ref
SIDE_RANK_MAX = _MOD.SIDE_RANK_MAX
substat_zh = _MOD.substat_zh
fmt_pct_gain = _MOD.fmt_pct_gain
fmt_top_pct = _MOD.fmt_top_pct
top_pct_color = _MOD.top_pct_color
zh_text = _MOD.zh_text
SIDE_W = _MOD.SIDE_W
_DD_FIXTURE = _ROOT / "test_output" / "gs_detail" / "akasha_dd_10000120.json"


def _fixture() -> dict[str, object]:
    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    return raw


def _board_and_rows() -> tuple[object, list[object]]:
    raw = _fixture()
    items = parse_substat_priority_payload(raw["substatPriority"])
    parsed_rows = parse_build_leaderboards_payload(raw["leaderboards"])
    assert items is not None
    assert parsed_rows is not None
    boards = compute_substat_priority_boards(items)
    rows = list_visible_leaderboards(parsed_rows)
    board = pick_priority_board(boards, rows[0]["calculation_id"])
    assert board is not None
    return board, rows


def test_substat_zh_and_pct_format() -> None:
    assert substat_zh("Crit DMG") == "暴击伤害"
    assert substat_zh("Flat HP") == "生命值"
    assert substat_zh("Energy Recharge") == "充能"
    assert fmt_pct_gain(3.033).startswith("+3.03")
    assert fmt_pct_gain(0.0) == "—"
    assert fmt_top_pct(4.0) == "前4%"


def test_side_html_table_and_teams() -> None:
    board, rows = _board_and_rows()
    html = akasha_side_html(
        board,
        rows,
        accent="#b98cf5",
        char_icons={"Columbina": "data:c", "Xiangling": "data:x"},
        weapon_icons={"14401": "data:w", "15501": "data:h"},
    )
    assert "副词条收益" in html
    assert "队伍榜" in html
    assert 'class="sec"' in html
    assert ">GAIN<" in html
    assert ">TEAM<" in html
    assert "smod" in html
    assert "tmface r" in html
    assert "tmstar" in html
    assert "暴击伤害" in html
    assert "生命%" in html
    assert "精通" in html
    assert "充能" in html
    assert "攻击%" not in html
    assert "gain" in html
    assert "+3.03%" in html
    assert "19,955" in html
    assert "610k" in html
    assert "前4%" in html
    assert "170% 充能" in html
    assert "月结晶队" in html
    assert "国际蒸发队" in html
    assert "超绽放队" in html
    assert "国家队" in html
    assert "On-Field Main DPS" not in html
    assert "data:c" in html
    assert "tmface" in html
    assert "lbcard on" in html
    assert akasha_side_html(None, [], accent="#b98cf5", char_icons={}, weapon_icons={}) == ""


def test_side_css_is_fixed_width() -> None:
    css = akasha_side_css("#43b6ee", SIDE_W)
    assert f"width:{SIDE_W}px" in css
    assert "sptab" in css
    assert "lbcard" in css
    assert ".smod" in css
    assert "margin-top:12px" in css
    assert ".tmface.r5" in css
    assert ".ddbar" in css
    assert ".ddleg" in css
    assert "align-items:center" in css
    assert ".grcon" in css


def test_zh_covers_live_akasha_team_names() -> None:
    assert zh_text("Lunar-Crystallize Team, Avg DMG") == "月结晶队 · 平均伤害"
    assert zh_text("Childe International, Avg DMG").startswith("公子国际队")
    assert zh_text("STELLAR") == "星极"
    assert zh_text("Bennett") == "班尼特"
    assert zh_text("Favonius Codex") == "西风秘典"
    assert zh_text("170% ER") == "170% 充能"
    assert zh_text("Northland Spearstorm Avg DMG") == "北国枪阵 · 平均伤害"
    assert zh_text("LC") == "月感电"
    assert zh_text("E") == "战技"
    table = _MOD.zh_table()
    names = table["names"]
    assert len(names) >= 124
    cat_path = _ROOT / "test_output" / "gs_detail" / "akasha_categories.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    live_names: set[str] = set()
    live_shorts: set[str] = set()
    live_weapons: set[str] = set()
    for item in cat["data"]:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("name"), str):
            live_names.add(item["name"])
        if isinstance(item.get("short"), str):
            live_shorts.add(item["short"])
        weapons = item["weapons"] if "weapons" in item and isinstance(item["weapons"], list) else []
        for wpn in weapons:
            if isinstance(wpn, dict) and isinstance(wpn.get("name"), str):
                live_weapons.add(wpn["name"])
    missing_n = sorted(n for n in live_names if n not in names)
    missing_s = sorted(s for s in live_shorts if s not in table["shorts"])
    missing_w = sorted(w for w in live_weapons if w not in table["weapons"])
    assert missing_n == [], missing_n
    assert missing_s == [], missing_s
    assert missing_w == [], missing_w
    assert zh_text(next(iter(live_names))) != next(iter(live_names))


def test_zh_sandrone_damage_parts() -> None:
    assert zh_text("SSC") == "星超导"
    assert zh_text("Sweeping Fire Avg DMG") == "扫射 · 平均伤害"
    assert zh_text("Prism Shot Avg DMG") == "棱晶弹 · 平均伤害"
    assert zh_text("Prism Shot Stellar-Conduct Avg DMG") == "棱晶弹星超导 · 平均伤害"
    assert zh_text("Condensed Beam Stellar-Conduct Avg DMG") == "冷凝射线星超导 · 平均伤害"
    assert zh_text("Bombardment Avg DMG") == "轰炸 · 平均伤害"
    assert zh_text("Convective Inhibition Ray Avg DMG") == "负温聚能光束 · 平均伤害"
    assert reaction_tag("Condensed Beam Stellar-Conduct Avg DMG", "SSC") == "星超导"


def test_all_harvested_akasha_parts_translated() -> None:
    harvest = _ROOT / "test_output" / "gs_detail" / "akasha_part_names.json"
    raw = json.loads(harvest.read_text(encoding="utf-8"))
    names = raw["names"]
    assert isinstance(names, list)
    leftover: list[str] = []
    for name in names:
        if not isinstance(name, str):
            continue
        zh = zh_text(name)
        if zh == name:
            leftover.append(name)
    assert leftover == []
    assert zh_text("Sweeping Fire Avg DMG") == "扫射 · 平均伤害"
    assert zh_text("Musou no Hitotachi Avg DMG") == "梦想一刀 · 平均伤害"


def test_top_pct_color_tiers() -> None:
    assert top_pct_color(0.4) == "#ef6b6b"
    assert top_pct_color(1) == "#ef6b6b"
    assert top_pct_color(5) == "#ffb056"
    assert top_pct_color(10) == "#c48ef0"
    assert top_pct_color(30) == "#8fb4ff"
    assert top_pct_color(50) == "#f2f5fb"
    assert top_pct_color(51) == "#8b919c"


def test_side_html_damage_distribution() -> None:
    board, rows = _board_and_rows()
    raw = json.loads(_DD_FIXTURE.read_text(encoding="utf-8"))
    parsed = parse_damage_distribution_payload(raw)
    assert parsed is not None
    dist = find_damage_distribution(parsed, "1000012002")
    assert dist is not None
    html = akasha_side_html(
        board,
        rows,
        accent="#b98cf5",
        char_icons={},
        weapon_icons={},
        dist=dist,
        section_icons={"dist": "data:d", "gain": "data:g", "teams": "data:t"},
    )
    assert "伤害分布" in html
    assert ">DMG<" in html
    assert "data:d" in html
    assert "北国枪阵" in html
    assert "北国枪阵 · 平均伤害" not in html
    assert "战技" in html
    assert "月感电" in html
    assert "普攻" in html
    assert "ddbar" in html
    assert "ddrow" in html
    assert "akey" in html
    assert "ddrx" in html
    assert "月感电" in html
    assert "总伤" in html
    assert "1,389,283" in html
    assert "ddformula" not in html
    only_dist = akasha_side_html(
        None,
        [],
        accent="#b98cf5",
        char_icons={},
        weapon_icons={},
        dist=dist,
    )
    assert "伤害分布" in only_dist
    assert "副词条收益" not in only_dist


def test_pick_loadout_ids_prefers_different_weapons() -> None:
    raw = json.loads((_ROOT / "test_output" / "gs_detail" / "akasha_lb_10000120.json").read_text(encoding="utf-8"))
    parsed = parse_build_leaderboards_payload(raw)
    assert parsed is not None
    rows = list_visible_leaderboards(parsed)
    ids = pick_loadout_ids(rows)
    assert len(ids) == 2
    assert ids[0].startswith("1000012002")
    assert ids[1].startswith("1000012004")
    assert match_calc_board(rows, "1000012002170er") is not None


def test_side_html_two_loadouts() -> None:
    board, rows = _board_and_rows()
    raw = json.loads(_DD_FIXTURE.read_text(encoding="utf-8"))
    parsed = parse_damage_distribution_payload(raw)
    assert parsed is not None
    d1 = find_damage_distribution(parsed, "1000012002")
    d2 = find_damage_distribution(parsed, "1000012004")
    assert d1 is not None and d2 is not None
    html = akasha_side_html(
        board,
        rows,
        accent="#b98cf5",
        char_icons={},
        weapon_icons={"13501": "data:homa", "13433": "data:shovel"},
        boards=[board, board],
        dists=[d1, d2],
    )
    assert "ddpair" in html
    assert html.count("ddbox half") == 2
    assert html.count('class="spbox"') == 2
    assert html.count("sgcap") == 2
    assert html.count("总伤") == 2
    assert html.count("ddwpic") == 2
    assert "data:homa" in html
    assert "护摩之杖" in html
    assert "掘金之锹" in html
    assert "sgbval" in html
    assert "2×" in html
    assert html.count("当前") == 2


def test_side_html_global_ranks() -> None:
    ranks = [
        {
            "rank": 5522,
            "out_of": 398000,
            "top_pct": 2.0,
            "uid": "100740568",
            "nickname": "Wuyi无疑",
            "region": "CN",
            "constellation": 3,
            "weapon_name": "Staff of Homa",
            "weapon_id": "13501",
            "refinement": 1,
            "result": 630450.0,
            "crit_rate": 0.745,
            "crit_dmg": 1.935,
            "cv": 218.4,
            "hp": 17883.0,
            "atk": 2028.0,
            "character_id": "10000033",
        }
    ]
    html = akasha_side_html(
        None,
        [],
        accent="#b98cf5",
        char_icons={},
        weapon_icons={"13501": "data:h"},
        ranks=ranks,
        self_uid="100740568",
        section_icons={"face": "data:face", "hp": "data:hp", "atk": "data:atk"},
    )
    assert "全球排名" in html
    assert ">RANK<" in html
    assert "Wuyi无疑" in html
    assert "UID 100740568" in html
    assert "#5522名" in html
    assert "3命" in html
    assert "精一" in html
    assert "218.4 cv" in html
    assert "74.5:193.5" in html
    assert "生命" in html
    assert "17883" in html
    assert "data:face" in html
    assert "grcard on" in html
    assert count_rank_slots(1700, 1400, 20) == SIDE_RANK_MAX
    assert count_rank_slots(100, 200, 20) == 0


def test_type_key_and_reaction() -> None:
    assert type_key("NA") == "A"
    assert type_key("CA") == "B"
    assert type_key("Q") == "Q"
    assert type_key("Plunge") == "C"
    assert reaction_tag("Burst Vape Avg DMG", "Q") == "蒸发"
    assert reaction_tag("Stance Avg DMG", "E") == ""
    assert reaction_tag("Lunar-Charged DMG", "LC") == "月感电"
    assert fmt_con(6) == "满命"
    assert fmt_con(3) == "3命"
    assert fmt_ref(1) == "精一"
    assert fmt_ref(5) == "满精"


def test_rank_slots_never_exceed_three() -> None:
    twenty = [{"rank": i, "uid": str(i)} for i in range(1, 21)]
    html = akasha_side_html(
        None,
        [],
        accent="#b98cf5",
        char_icons={},
        weapon_icons={},
        ranks=twenty,
        target_height=4000,
    )
    assert html.count("grcard") == SIDE_RANK_MAX


def test_pick_nearby_ranks_windows_self() -> None:
    rows = [{"rank": i, "uid": str(i)} for i in range(1, 21)]
    picked = pick_nearby_ranks(rows, "10", 3)
    assert [row["uid"] for row in picked] == ["9", "10", "11"]
    assert pick_nearby_ranks(rows, "1", 3)[0]["uid"] == "1"
    assert pick_nearby_ranks(rows, "missing", 3) == []
    html = akasha_side_html(
        None,
        [],
        accent="#b98cf5",
        char_icons={},
        weapon_icons={},
        ranks=rows,
        self_uid="10",
    )
    assert ">UID 10<" in html or "UID 10</span>" in html
    assert "UID 9</span>" in html
    assert "UID 2</span>" not in html
    assert html.count("grcard") == 3
    hidden = akasha_side_html(
        None,
        [],
        accent="#b98cf5",
        char_icons={},
        weapon_icons={},
        ranks=rows,
        self_uid="999",
    )
    assert "全球排名" not in hidden


def test_pick_priority_board_prefers_matching_id() -> None:
    board, rows = _board_and_rows()
    assert board["calculation_id"] == "1000012514170er"
    assert pick_priority_board([board], "missing") is board
    assert pick_priority_board([], "x") is None


def test_extract_build_md5_prefers_current() -> None:
    raw = _fixture()
    assert extract_build_md5(raw["builds"], "10000120") == "fixture-md5-flins"
    assert extract_build_md5(raw["builds"], "10000033") == "fixture-md5-childe"
    assert extract_build_md5(raw["builds"], "999") is None
    assert extract_build_md5("nope", "10000120") is None
