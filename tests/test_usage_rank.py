"""深渊 / 危战使用率解析、滞后和缓存。不走包 __init__，避免拉起整插件。"""

import sys
import json
import types
import asyncio
from pathlib import Path


def _load():
    pkg = "GenshinUID.genshinuid_xkdata"
    if pkg not in sys.modules:
        stub = types.ModuleType(pkg)
        stub.__path__ = [str(Path(__file__).resolve().parents[1] / "GenshinUID" / "genshinuid_xkdata")]
        stub.__package__ = pkg
        sys.modules[pkg] = stub
    from GenshinUID.genshinuid_xkdata.usage_rank import (
        StoredUsage,
        alignment,
        list_usage,
        save_usage,
        parse_usage,
        history_lines,
        usage_ai_text,
        hard_difficulty_samples,
    )

    return (
        StoredUsage,
        alignment,
        hard_difficulty_samples,
        history_lines,
        list_usage,
        parse_usage,
        save_usage,
        usage_ai_text,
    )


(
    StoredUsage,
    alignment,
    hard_difficulty_samples,
    history_lines,
    list_usage,
    parse_usage,
    save_usage,
    usage_ai_text,
) = _load()


def _member(avatar: str, star: int = 5) -> dict[str, object]:
    return {"avatar": avatar, "star": star}


def _abyss_payload() -> dict[str, object]:
    return {
        "version": "当前版本：7.0(第二期)",
        "title": "7.0深渊使用率统计(第二期)",
        "last_update": "2026-09-19 2:00",
        "update": "深渊时间：2026-09-16起",
        "top_own": 100,
        "tips": "数据还在更新",
        "tips2": "仅供参考",
        "history_list": [
            {"title": "v7.0(第二期)", "value": 63},
            {"title": "v7.0(第二期11层)", "value": 62},
        ],
        "result": [
            [
                {
                    "rank_name": "S+",
                    "list": [{"name": "哥伦比娅", "avatar": "http://img/a.png", "star": 5, "use_rate": 1}],
                }
            ],
            [
                {
                    "name": "哥伦比娅",
                    "avatar": "http://img/a.png",
                    "star": 5,
                    "use_rate": 89.6,
                    "use_rate_change": 46.7,
                },
                {
                    "name": "菲林斯",
                    "avatar": "http://img/b.png",
                    "star": 5,
                    "use_rate": 80,
                    "use_rate_change": -1.2,
                },
            ],
            [],
            [
                {
                    "role": [_member("http://img/a.png")],
                    "use_rate": 12,
                    "up_use": 99,
                    "down_use": 1,
                    "up_use_num": 99,
                    "down_use_num": 0,
                },
                {
                    "role": [_member("http://img/b.png")],
                    "use_rate": 56,
                    "up_use": 2,
                    "down_use": 98,
                    "up_use_num": 0,
                    "down_use_num": 98,
                },
            ],
        ],
    }


def _hard_payload() -> dict[str, object]:
    payload = _abyss_payload()
    payload["version"] = "当前版本：7.0"
    payload["update"] = "统计时间：2026-08-19开启"
    payload["top_own"] = "8728"
    teams = payload["result"]
    assert isinstance(teams, list)
    block = teams[3]
    assert isinstance(block, list)
    block.append(
        {
            "role": [_member("http://img/a.png")],
            "use_rate": "25.3",
            "use": "10",
            "up_use": 4,
            "mid_use": 90,
            "down_use": 6,
            "up_use_num": 1,
            "mid_use_num": 90,
            "down_use_num": 2,
            "time": 80.9,
        }
    )
    return payload


def test_visible_characters_uses_a_fixed_slot_count() -> None:
    from GenshinUID.genshinuid_xkdata.usage_rank import SHOW_CHAR_SLOTS, UsageChar, visible_characters

    chars: list[UsageChar] = []
    for index in range(30):
        row: UsageChar = {
            "name": f"c{index}",
            "star": 5,
            "avatar": "",
            "use_rate": 10.0,
            "use_rate_change": 0.0,
            "side_rate": float(30 - index),
        }
        chars.append(row)
    shown = visible_characters(chars)
    assert len(shown) == SHOW_CHAR_SLOTS
    assert shown[0]["name"] == "c0"
    assert len(visible_characters(chars[:2])) == 2


def test_abyss_splits_upper_and_lower() -> None:
    parsed = parse_usage(_abyss_payload(), "abyss")
    assert not isinstance(parsed, str)
    assert parsed["history_id"] == 63
    assert parsed["window_date"] == "2026-09-16"
    assert [side["name"] for side in parsed["sides"]] == ["上半", "下半"]
    upper = parsed["sides"][0]
    lower = parsed["sides"][1]
    assert upper["teams"][0]["members"][0]["name"] == "哥伦比娅"
    assert lower["teams"][0]["members"][0]["name"] == "菲林斯"
    assert lower["characters"][0]["name"] == "菲林斯"
    assert upper["characters"][0]["name"] == "哥伦比娅"
    assert upper["characters"][0]["use_rate_change"] == 46.7


def test_hard_difficulty_samples_split_total() -> None:
    pair = hard_difficulty_samples("数据总结：难度5&6总有效样本8728份，难度6有效样本2292份。")
    assert pair == (6436, 2292)
    assert hard_difficulty_samples("数据还在更新") is None


def test_hard_has_three_lanes() -> None:
    parsed = parse_usage(_hard_payload(), "hard")
    assert not isinstance(parsed, str)
    assert [side["name"] for side in parsed["sides"]] == ["上路", "中路", "下路"]
    assert parsed["sample"] == "8728"
    mid = parsed["sides"][1]
    assert mid["teams"][0]["time"] == 80.9
    assert mid["teams"][0]["members"][0]["name"] == "哥伦比娅"


def test_alignment_uses_schedule_dates_before_version_labels() -> None:
    matched, lagged = alignment("2026-09-16", "2026-09-16", "7.0(第二期)", "7.1.0")
    assert matched == "与当期日程对齐"
    assert lagged is False
    behind, is_behind = alignment("2026-09-16", "2026-10-16", "7.0(第二期)", "7.1.0")
    assert is_behind is True
    assert "2026-09-16" in behind
    fallback, fallback_lag = alignment("", "", "7.0(第二期)", "7.1.0")
    assert fallback_lag is True
    assert "7.1.0" in fallback


def test_ai_text_marks_stale_samples() -> None:
    parsed = parse_usage(_abyss_payload(), "abyss")
    assert not isinstance(parsed, str)
    text = usage_ai_text(
        parsed,
        "滞后：使用率仍是 2026-09-16 的样本，当期从 2026-10-16 开始",
        True,
        "日程20098 上半：岩盔王",
        "日程20097 上半：遗迹重机",
        ["- 7.0(第二期) 窗口2026-09-16 日程20097"],
        "",
    )
    assert "状态：滞后" in text
    assert "不能直接当当期配队" in text
    assert "岩盔王" in text
    assert "遗迹重机" in text
    assert "上半角色：" in text
    assert "下半队伍：" in text
    assert "箱子" in text


def test_cache_keeps_each_version(tmp_path: Path) -> None:
    first = parse_usage(_abyss_payload(), "abyss")
    assert not isinstance(first, str)
    second_raw = _abyss_payload()
    second_raw["version"] = "当前版本：7.1(第一期)"
    second_raw["update"] = "深渊时间：2026-10-16起"
    history = second_raw["history_list"]
    assert isinstance(history, list)
    history.insert(0, {"title": "v7.1(第一期)", "value": 64})
    second = parse_usage(second_raw, "abyss")
    assert not isinstance(second, str)

    async def _round() -> None:
        await save_usage(StoredUsage(snapshot=first, monster_brief="旧怪", fetched_at="2026-09-19"), tmp_path)
        await save_usage(StoredUsage(snapshot=second, monster_brief="新怪", fetched_at="2026-10-16"), tmp_path)
        rows = await list_usage("abyss", tmp_path)
        assert [row["snapshot"]["history_id"] for row in rows] == [64, 63]
        assert "旧怪" in history_lines(rows)[1]

    asyncio.run(_round())
    saved = json.loads((tmp_path / "abyss_63.json").read_text(encoding="utf-8"))
    assert saved["monster_brief"] == "旧怪"
