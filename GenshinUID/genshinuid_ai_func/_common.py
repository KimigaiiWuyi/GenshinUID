"""原神 AI 工具公共解析：UID、元素/武器映射、面板 JSON 读取。"""

from __future__ import annotations

import json
from pathlib import Path

from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind

from ..utils.map.GS_MAP_PATH import avatarName2Weapon
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH

ELEMENT_ZH: dict[str, str] = {
    "Anemo": "风",
    "Cryo": "冰",
    "Dendro": "草",
    "Electro": "雷",
    "Geo": "岩",
    "Hydro": "水",
    "Pyro": "火",
    "Wind": "风",
    "Ice": "冰",
    "Grass": "草",
    "Electric": "雷",
    "Rock": "岩",
    "Water": "水",
    "Fire": "火",
}

ELEMENT_INPUT: dict[str, str] = {
    "风": "风",
    "火": "火",
    "水": "水",
    "雷": "雷",
    "冰": "冰",
    "岩": "岩",
    "草": "草",
    "anemo": "风",
    "pyro": "火",
    "hydro": "水",
    "electro": "雷",
    "cryo": "冰",
    "geo": "岩",
    "dendro": "草",
}

WEAPON_TYPE_ZH: dict[str, str] = {
    "WEAPON_SWORD_ONE_HAND": "单手剑",
    "WEAPON_CLAYMORE": "双手剑",
    "WEAPON_POLE": "长柄武器",
    "WEAPON_CATALYST": "法器",
    "WEAPON_BOW": "弓",
    "单手剑": "单手剑",
    "双手剑": "双手剑",
    "长柄武器": "长柄武器",
    "法器": "法器",
    "弓": "弓",
}

WEAPON_INPUT: dict[str, str] = {
    "单手剑": "单手剑",
    "剑": "单手剑",
    "双手剑": "双手剑",
    "大剑": "双手剑",
    "长柄武器": "长柄武器",
    "长柄": "长柄武器",
    "枪": "长柄武器",
    "法器": "法器",
    "书": "法器",
    "弓": "弓",
}

REGION_ZH: dict[str, str] = {
    "MONDSTADT": "蒙德",
    "LIYUE": "璃月",
    "INAZUMA": "稻妻",
    "SUMERU": "须弥",
    "FONTAINE": "枫丹",
    "NATLAN": "纳塔",
    "NODKRAI": "挪德卡莱",
    "FATUI": "愚人众",
    "MAINACTOR": "主角",
    "SNEZHNAYA": "至冬",
    "SNEZHNAYA_STAR": "至冬",
    "RANGER": "游侠",
    "HVISION": "其它",
    "OMNI_SCOURGE": "其它",
    "NODKRAI_ZIBAI": "挪德卡莱",
}


def is_master(ev: Event | None) -> bool:
    return ev is not None and ev.user_pm == 0


def valid_uid(uid: str | None) -> bool:
    if uid is None:
        return False
    return uid.isdigit() and len(uid) == 9


def element_zh(raw: str) -> str:
    if raw in ELEMENT_ZH:
        return ELEMENT_ZH[raw]
    return raw


def weapon_type_zh(raw: str) -> str:
    if raw in WEAPON_TYPE_ZH:
        return WEAPON_TYPE_ZH[raw]
    return raw


def region_zh(raw: str) -> str:
    if raw in REGION_ZH:
        return REGION_ZH[raw]
    return raw


def normalize_element(text: str) -> str:
    key = text.strip()
    if key in ELEMENT_INPUT:
        return ELEMENT_INPUT[key]
    low = key.casefold()
    if low in ELEMENT_INPUT:
        return ELEMENT_INPUT[low]
    return key


def normalize_weapon_type(text: str) -> str:
    key = text.strip()
    if key in WEAPON_INPUT:
        return WEAPON_INPUT[key]
    return key


def char_weapon_type(name: str) -> str:
    if name in avatarName2Weapon:
        return avatarName2Weapon[name]
    return "-"


async def resolve_uid(ev: Event | None, uid: str = "") -> str:
    if uid.strip():
        raw = uid.strip()
        if valid_uid(raw):
            if ev is not None and not is_master(ev):
                bound = await GsBind.get_uid_list_by_game(ev.user_id, ev.bot_id)
                if bound is None or raw not in bound:
                    return ""
            return raw
        return ""
    if ev is None:
        return ""
    found = await GsBind.get_uid_by_game(ev.user_id, ev.bot_id)
    return found if found is not None else ""


def player_dir(uid: str) -> Path:
    return PLAYER_PATH / uid


def _is_char_json(path: Path) -> bool:
    if path.suffix != ".json" or not path.is_file():
        return False
    name = path.stem
    if not name:
        return False
    return "\u4e00" <= name[0] <= "\u9fff"


def list_cached_char_paths(uid: str) -> list[Path]:
    folder = player_dir(uid)
    if not folder.is_dir():
        return []
    paths: list[Path] = []
    for item in folder.iterdir():
        if _is_char_json(item):
            paths.append(item)
    self_dir = folder / "SELF"
    if self_dir.is_dir():
        for item in self_dir.iterdir():
            if _is_char_json(item):
                paths.append(item)
    return paths


def load_json_obj(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        return raw
    return None


def as_str(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    return ""


def as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def as_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    return 0.0


def pct(value: object) -> str:
    return f"{as_float(value) * 100:.1f}%"
