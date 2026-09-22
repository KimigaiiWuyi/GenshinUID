"""把全部武器写入 weapon_alias.json。

别名只许三类：角色专武、中文缩略、容易打错的中文。
不写英文全称。简单英文简称才可以进 ENGLISH_SHORT，目前不收。
重跑按这三张表重写，不把旧 JSON 里的英文名带回来。
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_WEAPON_DIR = _ROOT / "tools" / "gs_data" / "weapon"
_CHAR_DIR = _ROOT / "tools" / "gs_data" / "char"
_OUT = _ROOT / "utils" / "map" / "data" / "weapon_alias.json"

# 中文缩略。键必须是武器正式名。
SHORT: dict[str, list[str]] = {
    "天空之刃": ["天空剑"],
    "天空之傲": ["天空大剑"],
    "天空之翼": ["天空弓"],
    "天空之卷": ["天空书", "天空法器"],
    "天空之脊": ["天空枪"],
    "风鹰剑": ["风鹰"],
    "狼的末路": ["狼末"],
    "和璞鸢": ["鸟枪", "绿枪"],
    "护摩之杖": ["护摩"],
    "雾切之回光": ["雾切"],
    "磐岩结绿": ["绿剑"],
    "苍古自由之誓": ["苍古"],
    "终末嗟叹之诗": ["终末"],
    "薙草之稻光": ["剃草"],
    "赤沙之杖": ["赤沙"],
    "阿莫斯之弓": ["阿莫斯"],
    "四风原典": ["四风"],
    "冬极白星": ["冬极"],
    "飞雷之弦振": ["飞雷"],
    "静水流涌之辉": ["静水"],
    "裁叶萃光": ["裁叶"],
    "波乱月白经津": ["波乱", "经津"],
    "有乐御簾切": ["有乐"],
    "千夜浮梦": ["千夜"],
    "图莱杜拉的回忆": ["图莱杜拉", "陀螺"],
    "万世流涌大典": ["万世"],
    "不灭月华": ["月华"],
    "神乐之真意": ["神乐"],
    "尘世之锁": ["尘世"],
    "贯虹之槊": ["贯虹", "呆枪"],
    "松籁响起之时": ["松籁"],
    "赤角石溃杵": ["赤角"],
    "苇海信标": ["苇海"],
    "赤月之形": ["赤月"],
    "碧落之珑": ["碧落"],
    "金流监督": ["金流"],
    "焚曜千阳": ["千阳"],
    "山王长牙": ["山王"],
    "岩峰巡歌": ["巡歌"],
    "最初的大魔术": ["大魔术"],
    "猎人之径": ["猎人弓"],
    "白雨心弦": ["白雨"],
    "星鹫赤羽": ["赤羽"],
    "鹤鸣余音": ["鹤鸣"],
    "祭星者之望": ["祭星"],
    "匣里龙吟": ["匣里"],
    "匣里灭辰": ["灭辰"],
    "试作斩岩": ["斩岩"],
    "试作星镰": ["星镰"],
    "试作金珀": ["金珀"],
    "试作澹月": ["澹月"],
    "试作古华": ["古华"],
    "讨龙英杰谭": ["讨龙"],
    "绝弦": ["绿弓"],
    "腐殖之剑": ["腐殖"],
    "辰砂之纺锤": ["辰砂", "纺锤"],
    "天目影打刀": ["天目"],
    "西福斯的月光": ["西福斯"],
    "黑岩长剑": ["黑岩剑"],
    "黑岩斩刀": ["黑岩大剑"],
    "黑岩刺枪": ["黑岩枪"],
    "黑岩战弓": ["黑岩弓"],
    "黑岩绯玉": ["黑岩书"],
    "宗室长剑": ["宗室剑"],
    "宗室猎枪": ["宗室枪"],
    "宗室长弓": ["宗室弓"],
    "宗室秘法录": ["宗室书"],
    "祭礼残章": ["祭礼书"],
    "流浪乐章": ["流浪"],
    "白影剑": ["白影"],
    "千岩古剑": ["千岩剑"],
    "千岩长枪": ["千岩枪"],
    "桂木斩长正": ["桂木"],
    "恶王丸": ["恶王"],
    "断浪长鳍": ["断浪"],
    "曚云之月": ["蒙云"],
    "证誓之明瞳": ["证誓"],
    "决斗之枪": ["决斗"],
    "龙脊长枪": ["龙脊"],
    "流月针": ["流月"],
    "喜多院十文字": ["喜多院"],
    "铁蜂刺": ["铁蜂"],
    "「渔获」": ["渔获"],
}

# 容易打错的中文。不是缩写，是错字或异体。
TYPO: dict[str, list[str]] = {
    "银釭": ["银缸"],
    "试作澹月": ["淡月"],
    "鹮穿之喙": ["环穿之喙"],
    "有乐御簾切": ["有乐御帘切"],
    "薙草之稻光": ["剃草之稻光"],
    "曚云之月": ["蒙云之月"],
    "朏魄含光": ["非魄含光"],
    "猰貐": ["亚雨"],
    "猰貐·真化": ["亚雨真化"],
    "玛海菈的水色": ["玛海拉的水色"],
}

# 简单英文简称（单个词、无空格）。英文全称不放这里。
ENGLISH_SHORT: dict[str, list[str]] = {}

# 角色专武。JSON 里只写「正式名专武」。别名展开在查武器名时做。
SIGNATURE: dict[str, str] = {
    "风鹰剑": "琴",
    "狼的末路": "迪卢克",
    "和璞鸢": "魈",
    "阿莫斯之弓": "甘雨",
    "四风原典": "可莉",
    "尘世之锁": "凝光",
    "磐岩结绿": "刻晴",
    "斫峰之刃": "阿贝多",
    "苍古自由之誓": "枫原万叶",
    "雾切之回光": "神里绫华",
    "波乱月白经津": "神里绫人",
    "圣显之钥": "妮露",
    "裁叶萃光": "艾尔海森",
    "静水流涌之辉": "芙宁娜",
    "有乐御簾切": "千织",
    "赦罪": "克洛琳德",
    "岩峰巡歌": "希诺宁",
    "苍耀": "丝柯克",
    "护摩之杖": "胡桃",
    "贯虹之槊": "钟离",
    "息灾": "申鹤",
    "薙草之稻光": "雷电将军",
    "赤沙之杖": "赛诺",
    "赤月之形": "阿蕾奇诺",
    "柔灯挽歌": "艾梅莉埃",
    "香韵奏者": "爱可菲",
    "支离轮光": "伊涅芙",
    "松籁响起之时": "优菈",
    "赤角石溃杵": "荒泷一斗",
    "苇海信标": "迪希雅",
    "裁断": "娜维娅",
    "山王长牙": "基尼奇",
    "焚曜千阳": "玛薇卡",
    "不灭月华": "珊瑚宫心海",
    "神乐之真意": "八重神子",
    "千夜浮梦": "纳西妲",
    "图莱杜拉的回忆": "流浪者",
    "万世流涌大典": "那维莱特",
    "鹤鸣余音": "闲云",
    "冲浪时光": "玛拉妮",
    "祭星者之望": "茜特菈莉",
    "寝正月初晴": "梦见月瑞希",
    "碧落之珑": "白术",
    "金流监督": "莱欧斯利",
    "溢彩心念": "瓦雷莎",
    "终末嗟叹之诗": "温迪",
    "冬极白星": "达达利亚",
    "若水": "夜兰",
    "飞雷之弦振": "宵宫",
    "猎人之径": "提纳里",
    "最初的大魔术": "林尼",
    "白雨心弦": "希格雯",
    "星鹫赤羽": "恰斯卡",
    "幽夜华尔兹": "菲谢尔",
}


def _load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"不是对象：{path}")
    return data


def _weapon_rows() -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for path in sorted(_WEAPON_DIR.glob("*.json")):
        data = _load_json(path)
        name = data["name"] if "name" in data else ""
        raw_id = data["id"] if "id" in data else 0
        if not isinstance(name, str) or not name:
            continue
        weapon_id = raw_id if isinstance(raw_id, int) else 0
        rows.append((weapon_id, name))
    if not rows:
        raise SystemExit(f"没有武器 JSON：{_WEAPON_DIR}")
    return rows


def _playable_names() -> set[str]:
    names: set[str] = set()
    for path in _CHAR_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "name" not in data:
            continue
        name = data["name"]
        if isinstance(name, str) and name:
            names.add(name)
    return names


def _signature_aliases(weapon: str, characters: set[str]) -> list[str]:
    if weapon not in SIGNATURE:
        return []
    character = SIGNATURE[weapon]
    if character not in characters:
        raise SystemExit(f"专武角色不在角色表里：{character} → {weapon}")
    return [f"{character}专武"]


def _latin_letter(text: str) -> bool:
    return any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in text)


def build_alias_map(previous: dict[str, list[str]] | None = None) -> dict[str, list[str]]:
    _ = previous
    rows = _weapon_rows()
    characters = _playable_names()
    names = {name for _weapon_id, name in rows}
    tables = (SHORT, TYPO, ENGLISH_SHORT, SIGNATURE)
    for table in tables:
        for weapon in table:
            if weapon not in names:
                raise SystemExit(f"别名表里的武器不存在：{weapon}")
    for weapon, aliases in ENGLISH_SHORT.items():
        for alias in aliases:
            if (not alias) or (" " in alias) or (not _latin_letter(alias)):
                raise SystemExit(f"英文简称必须是单个英文词：{weapon} → {alias}")

    by_id: dict[str, int] = {}
    for weapon_id, name in rows:
        if name not in by_id or weapon_id < by_id[name]:
            by_id[name] = weapon_id

    owner: dict[str, str] = {}
    result: dict[str, list[str]] = {}
    ordered = sorted(names, key=lambda item: (by_id[item], item))
    for name in ordered:
        aliases: list[str] = []
        aliases.extend(_signature_aliases(name, characters))
        if name in SHORT:
            aliases.extend(SHORT[name])
        if name in TYPO:
            aliases.extend(TYPO[name])
        if name in ENGLISH_SHORT:
            aliases.extend(ENGLISH_SHORT[name])
        cleaned: list[str] = []
        for alias in aliases:
            text = alias.strip()
            if not text or text == name or text in cleaned:
                continue
            if text in names and text != name:
                raise SystemExit(f"别名与另一把武器同名：{text} → {name}")
            if text in owner and owner[text] != name:
                raise SystemExit(f"别名冲突：{text} 同时指向 {owner[text]} 和 {name}")
            owner[text] = name
            cleaned.append(text)
        result[name] = cleaned
    return result


def main() -> None:
    merged = build_alias_map()
    _OUT.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    filled = sum(1 for aliases in merged.values() if aliases)
    print(f"wrote {len(merged)} weapons, {filled} with aliases → {_OUT}")


if __name__ == "__main__":
    main()
