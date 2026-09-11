import sys
import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_MOD_PATH = _ROOT / "GenshinUID" / "genshinuid_enka" / "artifact_times.py"
_FIXTURE = _ROOT / "test_output" / "gs_detail"

_SPEC = spec_from_file_location("artifact_times", _MOD_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MOD = module_from_spec(_SPEC)
sys.modules["artifact_times"] = _MOD
_SPEC.loader.exec_module(_MOD)

apply_substat_affix = _MOD.apply_substat_affix
apply_substat_times = _MOD.apply_substat_times
collect_affix_rolls = _MOD.collect_affix_rolls
count_affix_times = _MOD.count_affix_times
infer_is_max = _MOD.infer_is_max
max_sub_roll = _MOD.max_sub_roll
substat_is_max = _MOD.substat_is_max
substat_rolls = _MOD.substat_rolls
substat_times = _MOD.substat_times

_MYS_TYPE = {
    2: "FIGHT_PROP_HP",
    5: "FIGHT_PROP_ATTACK",
    6: "FIGHT_PROP_ATTACK_PERCENT",
    8: "FIGHT_PROP_DEFENSE",
    9: "FIGHT_PROP_DEFENSE_PERCENT",
    20: "FIGHT_PROP_CRITICAL",
    22: "FIGHT_PROP_CRITICAL_HURT",
    23: "FIGHT_PROP_CHARGE_EFFICIENCY",
    28: "FIGHT_PROP_ELEMENT_MASTERY",
}

# 菲林斯生之花（enka.json itemId 41544），与米游社 times 对齐
FLOWER_ROLLS = [501081, 501221, 501202, 501063, 501204, 501223, 501222, 501201, 501062]
FLOWER_MYS = {
    "FIGHT_PROP_DEFENSE": 0,
    "FIGHT_PROP_CRITICAL_HURT": 2,
    "FIGHT_PROP_CRITICAL": 2,
    "FIGHT_PROP_ATTACK_PERCENT": 1,
}

PLUME_ROLLS = [501083, 501224, 501202, 501062, 501222, 501061, 501062, 501064]
PLUME_MYS = {
    "FIGHT_PROP_DEFENSE": 0,
    "FIGHT_PROP_CRITICAL_HURT": 1,
    "FIGHT_PROP_CRITICAL": 0,
    "FIGHT_PROP_ATTACK_PERCENT": 3,
}


def test_count_affix_times_matches_mihoyo_flower() -> None:
    assert count_affix_times(FLOWER_ROLLS) == FLOWER_MYS


def test_count_affix_times_matches_mihoyo_plume() -> None:
    assert count_affix_times(PLUME_ROLLS) == PLUME_MYS


def test_apply_substat_times_writes_known_props() -> None:
    subs: list[dict[str, object]] = [
        {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 9.7},
        {"appendPropId": "FIGHT_PROP_DEFENSE", "statValue": 16},
    ]
    apply_substat_times(subs, FLOWER_MYS)
    assert subs[0]["times"] == 2
    assert subs[1]["times"] == 0


def test_apply_substat_times_skips_unknown_prop() -> None:
    subs: list[dict[str, object]] = [{"appendPropId": "FIGHT_PROP_HP", "statValue": 4780}]
    apply_substat_times(subs, FLOWER_MYS)
    assert "times" not in subs[0]


def test_substat_times_compat() -> None:
    assert substat_times({"statValue": 1}) is None
    assert substat_times({"times": 2}) == 2
    assert substat_times({"times": 0}) == 0
    assert substat_times({"times": -1}) is None
    assert substat_times({"times": True}) is None


def test_collect_affix_rolls_keeps_rank_order() -> None:
    rolls = collect_affix_rolls(FLOWER_ROLLS)
    assert rolls["FIGHT_PROP_CRITICAL_HURT"] == [1, 3, 2]
    assert rolls["FIGHT_PROP_CRITICAL"] == [2, 4, 1]
    assert rolls["FIGHT_PROP_ATTACK_PERCENT"] == [3, 2]
    assert rolls["FIGHT_PROP_DEFENSE"] == [1]


def test_apply_substat_affix_writes_rolls_and_is_max() -> None:
    subs: list[dict[str, object]] = [
        {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 18.7},
        {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 9.7},
    ]
    apply_substat_affix(subs, collect_affix_rolls(FLOWER_ROLLS))
    assert subs[0]["times"] == 2
    assert subs[0]["rolls"] == [1, 3, 2]
    assert subs[0]["isMax"] is False
    assert subs[1]["times"] == 2
    assert subs[1]["rolls"] == [2, 4, 1]
    assert subs[1]["isMax"] is False


def test_apply_substat_affix_all_rank4_is_max() -> None:
    subs: list[dict[str, object]] = [{"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 11.7}]
    apply_substat_affix(subs, {"FIGHT_PROP_CRITICAL": [4, 4, 4]})
    assert subs[0]["times"] == 2
    assert subs[0]["isMax"] is True


def test_max_sub_roll_by_zh_name() -> None:
    assert max_sub_roll("暴击率") == 3.89
    assert max_sub_roll("暴击伤害") == 7.77
    assert max_sub_roll("百分比攻击力") == 5.83
    assert max_sub_roll("元素精通") == 23.31
    assert max_sub_roll("攻击力", 4) == 15.56
    assert max_sub_roll("治疗加成") == 0.0


def test_infer_is_max_from_value() -> None:
    assert infer_is_max("FIGHT_PROP_CRITICAL_HURT", 23.31, 2, 5) is True
    assert infer_is_max("FIGHT_PROP_CRITICAL_HURT", 18.7, 2, 5) is False
    assert infer_is_max("FIGHT_PROP_ATTACK_PERCENT", 23.3, 3, 5) is True
    assert infer_is_max("FIGHT_PROP_ATTACK_PERCENT", 19.2, 3, 5) is False


def test_substat_rolls_and_is_max_compat() -> None:
    assert substat_rolls({"statValue": 1}) is None
    assert substat_rolls({"rolls": [1, 4, 2]}) == [1, 4, 2]
    assert substat_rolls({"rolls": [0, 4]}) is None
    assert substat_is_max({"statValue": 1}) is None
    assert substat_is_max({"isMax": True}) is True
    assert substat_is_max({"isMax": False}) is False


def test_enka_and_mys_fixture_times_align() -> None:
    enka = json.loads((_FIXTURE / "enka.json").read_text(encoding="utf-8"))
    mys = json.loads((_FIXTURE / "miyoushe_feilinsi.json").read_text(encoding="utf-8"))
    avatar = None
    for item in enka["avatarInfoList"]:
        if item["avatarId"] == 10000120:
            avatar = item
            break
    assert avatar is not None
    enka_arts = [eq for eq in avatar["equipList"] if eq["flat"]["itemType"] == "ITEM_RELIQUARY"]
    mys_arts = mys["data"]["list"][0]["relics"]
    assert len(enka_arts) == len(mys_arts) == 5
    for left, right in zip(enka_arts, mys_arts):
        got = count_affix_times(left["reliquary"]["appendPropIdList"])
        expect: dict[str, int] = {}
        for su in right["sub_property_list"]:
            expect[_MYS_TYPE[su["property_type"]]] = su["times"]
        assert got == expect
