from __future__ import annotations

import sys
import json
import types
import asyncio
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_WIKI = _ROOT / "GenshinUID" / "genshinuid_wikitext"
_CHAR = _ROOT / "GenshinUID" / "tools" / "gs_data" / "char" / "10000052.json"
_WEAPON = _ROOT / "GenshinUID" / "tools" / "gs_data" / "weapon" / "15502.json"
_REL = _ROOT / "GenshinUID" / "tools" / "gs_data" / "reliquary" / "15047.json"

_PKG = "GenshinUID.genshinuid_wikitext"
if _PKG not in sys.modules:
    _fake = types.ModuleType(_PKG)
    _fake.__path__ = [str(_WIKI)]
    sys.modules[_PKG] = _fake

_SPEC = spec_from_file_location(f"{_PKG}.wiki_data", _WIKI / "wiki_data.py")
assert _SPEC is not None and _SPEC.loader is not None
_MOD = module_from_spec(_SPEC)
sys.modules[f"{_PKG}.wiki_data"] = _MOD
_SPEC.loader.exec_module(_MOD)

parse_query = _MOD.parse_query
parse_voice_query = _MOD.parse_voice_query
merge_refinements = _MOD.merge_refinements
strip_ambr_text = _MOD.strip_ambr_text
parse_char_wiki = _MOD.parse_char_wiki
parse_weapon_wiki = _MOD.parse_weapon_wiki
parse_artifact_wiki = _MOD.parse_artifact_wiki
parse_char_story = _MOD.parse_char_story
char_ai_text = _MOD.char_ai_text
char_const_text = _MOD.char_const_text
char_talent_text = _MOD.char_talent_text
char_profile_text = _MOD.char_profile_text
char_material_text = _MOD.char_material_text
story_ai_text = _MOD.story_ai_text
quote_ai_text = _MOD.quote_ai_text
quote_line_text = _MOD.quote_line_text
_match_voice_url = _MOD._match_voice_url
_parse_obc_voice_tab = _MOD._parse_obc_voice_tab
resolve_char_id = _MOD.resolve_char_id
_weapon_hits = _MOD._weapon_hits
_artifact_hits = _MOD._artifact_hits


def test_parse_query_level_and_alias_digits() -> None:
    assert parse_query("七七90") == ("七七", 90)
    assert parse_query("西风剑90") == ("西风剑", 90)
    assert parse_query("申鹤2") == ("申鹤", 90)
    assert parse_query("可莉") == ("可莉", 90)
    assert parse_query("甘雨1") == ("甘雨", 1)


def test_parse_voice_query_index() -> None:
    assert parse_voice_query("可莉") == ("可莉", None)
    assert parse_voice_query("可莉3") == ("可莉", 3)
    assert parse_voice_query("雷神 12") == ("雷神", 12)
    assert parse_voice_query("甘雨1") == ("甘雨", 1)


def test_merge_refinements_joins_numbers() -> None:
    texts = (
        "伤害提升12%；每0.1秒再提升8%。",
        "伤害提升15%；每0.1秒再提升10%。",
        "伤害提升18%；每0.1秒再提升12%。",
        "伤害提升21%；每0.1秒再提升14%。",
        "伤害提升24%；每0.1秒再提升16%。",
    )
    out = merge_refinements(texts)
    assert "12%/15%/18%/21%/24%" in out
    assert "8%/10%/12%/14%/16%" in out


def test_strip_ambr_color() -> None:
    raw = "<color=#FFD780FF>雷罚恶曜之眼</color>造成<color=#FFACFFFF>雷元素伤害</color>。"
    assert strip_ambr_text(raw) == "雷罚恶曜之眼造成雷元素伤害。"


def test_parse_raiden_local_json() -> None:
    raw = json.loads(_CHAR.read_text(encoding="utf-8"))
    data = parse_char_wiki(raw, 90)
    assert data.name == "雷电将军"
    assert data.element == "Electro"
    assert data.weapon == "长柄武器"
    assert data.rarity == 5
    assert data.hp > 10000
    assert data.atk > 200
    assert data.substat == "元素充能效率"
    assert data.substat_value.endswith("%")
    assert len(data.consts) == 6
    assert data.consts[0].name == "恶曜卜词"
    slots = [t.slot for t in data.talents]
    assert "A" in slots and "E" in slots and "Q" in slots and "P" in slots
    names = [t.name for t in data.talents]
    assert "神变·恶曜开眼" in names
    assert "奥义·梦想真说" in names
    assert data.mora_ascend > 0
    assert data.ascend_items
    text = char_ai_text(data)
    assert "原神角色 雷电将军" in text
    assert "天下人座" in text
    assert "恶曜卜词" in text
    assert "神变·恶曜开眼" in text
    assert "突破" in char_material_text(data)
    assert "恶曜卜词" in char_const_text(data)
    assert "突破" not in char_const_text(data)
    assert "神变·恶曜开眼" in char_talent_text(data)
    assert "命座" not in char_talent_text(data)
    assert "HP" in char_profile_text(data)
    assert "C1" not in char_profile_text(data)


def test_parse_amos_local_json() -> None:
    raw = json.loads(_WEAPON.read_text(encoding="utf-8"))
    data = parse_weapon_wiki(raw, 90)
    assert data.name == "阿莫斯之弓"
    assert data.weapon_type == "弓"
    assert data.rarity == 5
    assert data.atk_max > data.atk_base
    assert data.effect_name == "矢志不忘"
    assert "/" in data.effect
    assert data.items


def test_parse_artifact_local_json() -> None:
    raw = json.loads(_REL.read_text(encoding="utf-8"))
    data = parse_artifact_wiki(raw)
    assert data.name == "血红之证"
    assert 5 in data.rarity
    assert "攻击力" in data.effect2
    assert len(data.pieces) == 5
    assert data.pieces[0].slot == "生之花"


def test_weapon_and_artifact_hits() -> None:
    homa = _weapon_hits("护摩")
    assert len(homa) == 1
    assert homa[0][1] == "护摩之杖"
    sky = _weapon_hits("天空")
    assert len(sky) > 1
    paradise = _artifact_hits("乐园")
    assert len(paradise) == 1
    assert "乐园" in paradise[0][1]


def test_resolve_raiden_alias() -> None:
    found = asyncio.run(resolve_char_id("雷神"))
    assert found == "10000052"
    miss = asyncio.run(resolve_char_id("这不是一个角色名xyz"))
    assert miss == []


def test_parse_char_story_fetter() -> None:
    raw = {
        "story": {
            "0": {"title": "角色详细", "text": "阿兰会叫她「小玛丽安」。", "tips": ""},
            "1": {"title": "角色故事1", "text": "她清楚地记得自己的出生。", "tips": "好感等级达到2后开启"},
        },
        "quotes": {
            "0": {"title": "初次见面…", "text": "我讨厌做自我介绍。", "tips": "", "audio": "1000"},
            "1": {"title": "闲聊·冒险", "text": "要和可莉一起去炸鱼吗？", "tips": "", "audio": "1102"},
        },
    }
    data = parse_char_story(raw, "10000133", None)
    assert data.char_id == "10000133"
    assert len(data.stories) == 2
    assert data.stories[0].title == "角色详细"
    assert "小玛丽安" in data.stories[0].text
    assert data.stories[1].tips.startswith("好感")
    assert len(data.quotes) == 2
    assert data.quotes[0].audio == "1000"
    text = story_ai_text(data)
    assert "原神角色故事" in text
    assert "角色故事1" in text
    assert "初次见面" not in text
    voice = quote_ai_text(data)
    assert "原神角色语音" in voice
    assert "1. 初次见面" in voice
    assert "2. 闲聊·冒险" in voice
    assert "角色故事1" not in voice
    line = quote_line_text(data, data.quotes[1], 2)
    assert line.startswith("原神角色语音")
    assert "2. 闲聊·冒险" in line


def test_obc_voice_tab_and_title_match() -> None:
    html = (
        '<div data-data="%5B%7B%22tmplKey%22%3A%22character%22%2C%22partKey%22%3A%22voiceTab%22'
        "%2C%22data%22%3A%7B%22attr%22%3A%5B%7B%22name_%22%3A%22%E6%B1%89%E8%AF%AD%22%2C%22items%22%3A%5B"
        "%7B%22name%22%3A%22%E5%88%9D%E6%AC%A1%E8%A7%81%E9%9D%A2%E2%80%A6%22%2C%22audio%22%3A%22https%3A%2F%2Fx.mp3%22%7D"
        '%5D%7D%5D%7D%7D%5D"></div>'
    )
    voices = _parse_obc_voice_tab(html)
    assert voices["初次见面…"] == "https://x.mp3"
    assert _match_voice_url("初次见面...", voices) == "https://x.mp3"
    assert _match_voice_url("没有这条", voices) == ""
