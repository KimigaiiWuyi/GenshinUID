"""Wiki 图鉴数据：本地元数据 / gs_data / ambr，不再走 MiniGG。"""

from __future__ import annotations

import re
import json
from pathlib import Path
from dataclasses import dataclass
from collections.abc import Mapping, Callable, Awaitable

import aiofiles
from httpx import AsyncClient

from gsuid_core.utils.api.utils import _HEADER
from gsuid_core.utils.api.ambr.api import AMBR_BASE_URL
from gsuid_core.utils.api.ambr.request import (
    get_ambr_char_data,
    get_ambr_weapon_data,
    get_ambr_monster_data,
    get_ambr_monster_list,
    get_ambr_reliquary_data,
)

from ..utils.ambr_to_minigg import PROP_MAP, ELEMENT_MAP, WEAPON_TYPE
from ..utils.map.grow_curve import GROW_CURVE_LIST, WEAPON_GROW_CURVE
from ..utils.map.GS_MAP_PATH import (
    charList,
    weaponList,
    reliquaryList,
    ex_monster_data,
)
from ..utils.map.name_covert import name_to_avatar_id, alias_to_char_name
from ..utils.resource.RESOURCE_PATH import (
    WIKI_DATA_REL,
    WIKI_DATA_CHAR,
    WIKI_DATA_FOOD,
    WIKI_DATA_WEAPON,
    WIKI_DATA_MONSTER,
)

_SEED_DATA = Path(__file__).resolve().parents[1] / "tools" / "gs_data"
_AMBR_FOOD_LIST = f"{AMBR_BASE_URL}/api/v2/chs/food"
_AMBR_FOOD_URL = AMBR_BASE_URL + "/api/v2/chs/food/{}"
_NUM_IN_TEXT = re.compile(r"\d+")
_ZH_NAME = re.compile(r"[\u4e00-\u9fa5]+")
_PARAM_RE = re.compile(r"\{param(\d+):([A-Za-z0-9]+)\}")
_COLOR_RE = re.compile(r"</?color(?:=#[0-9A-Fa-f]+)?[^>]*>")
_HTML_RE = re.compile(r"<[^>]+>")
_REFINE_NUM = re.compile(r"\d+(?:\.\d+)?%?")
_TRAVELER_ID: dict[str, str] = {
    "旅行者": "10000007-anemo",
    "旅行者风": "10000007-anemo",
    "旅行者岩": "10000007-geo",
    "旅行者雷": "10000007-electro",
    "旅行者草": "10000007-dendro",
    "旅行者水": "10000007-hydro",
    "旅行者火": "10000007-pyro",
    "旅行者冰": "10000007-cryo",
}
_ELEM_EN: dict[str, str] = {
    "Wind": "Anemo",
    "Ice": "Cryo",
    "Grass": "Dendro",
    "Water": "Hydro",
    "Electric": "Electro",
    "Rock": "Geo",
    "Fire": "Pyro",
    "Anemo": "Anemo",
    "Cryo": "Cryo",
    "Dendro": "Dendro",
    "Hydro": "Hydro",
    "Electro": "Electro",
    "Geo": "Geo",
    "Pyro": "Pyro",
}
_REGION_ZH: dict[str, str] = {
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
_MONSTER_TYPE_ZH: dict[str, str] = {
    "ELEMENTAL": "元素生命",
    "HILICHURL": "丘丘部族",
    "ABYSS": "深渊",
    "FATUI": "愚人众",
    "AUTOMATRON": "自律机关",
    "HUMAN": "其他人类势力",
    "BEAST": "异种魔兽",
    "BOSS": "值得铭记的强敌",
    "AVIARY": "禽鸟",
    "ANIMAL": "走兽",
    "FISH": "游鱼",
    "CRITTER": "其他",
}
_BASE_SUB: dict[str, float] = {
    "暴击率": 0.05,
    "暴击伤害": 0.5,
    "元素充能效率": 1.0,
}
_FLAT_SUB = {"元素精通", "基础生命值", "基础攻击力", "基础防御力"}
_RES_KEYS: tuple[tuple[str, str], ...] = (
    ("physicalSubHurt", "物"),
    ("fireSubHurt", "火"),
    ("waterSubHurt", "水"),
    ("elecSubHurt", "雷"),
    ("iceSubHurt", "冰"),
    ("windSubHurt", "风"),
    ("rockSubHurt", "岩"),
    ("grassSubHurt", "草"),
)
_SUIT_ORDER: tuple[tuple[str, str], ...] = (
    ("EQUIP_BRACER", "生之花"),
    ("EQUIP_NECKLACE", "死之羽"),
    ("EQUIP_SHOES", "时之沙"),
    ("EQUIP_RING", "空之杯"),
    ("EQUIP_DRESS", "理之冠"),
)
_WEAPON_ORE = {5: 907, 4: 605, 3: 399, 2: 108, 1: 72}


@dataclass(frozen=True)
class WikiItem:
    item_id: str
    name: str
    icon: str
    count: int
    rank: int


@dataclass(frozen=True)
class CharTalent:
    slot: str
    name: str
    icon: str
    description: str
    cooldown: int
    cost: int
    rows: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class CharConst:
    index: int
    name: str
    icon: str
    description: str


@dataclass(frozen=True)
class CharWiki:
    char_id: str
    name: str
    title: str
    element: str
    element_zh: str
    weapon: str
    rarity: int
    region: str
    birthday: str
    constellation: str
    native: str
    cv: str
    description: str
    icon: str
    level: int
    hp: int
    atk: int
    defense: int
    substat: str
    substat_value: str
    talents: tuple[CharTalent, ...]
    consts: tuple[CharConst, ...]
    ascend_items: tuple[WikiItem, ...]
    talent_items: tuple[WikiItem, ...]
    mora_ascend: int
    mora_talent: int


@dataclass(frozen=True)
class WeaponWiki:
    weapon_id: str
    name: str
    weapon_type: str
    rarity: int
    description: str
    icon: str
    level: int
    atk_base: int
    atk_max: int
    substat: str
    sub_base: str
    sub_max: str
    effect_name: str
    effect: str
    refinements: tuple[str, ...]
    items: tuple[WikiItem, ...]
    mora: int
    ore: int


@dataclass(frozen=True)
class ArtifactPiece:
    slot: str
    name: str
    description: str
    icon: str


@dataclass(frozen=True)
class ArtifactWiki:
    set_id: str
    name: str
    rarity: tuple[int, ...]
    icon: str
    effect2: str
    effect4: str
    effect1: str
    pieces: tuple[ArtifactPiece, ...]
    source: str


@dataclass(frozen=True)
class FoodWiki:
    food_id: str
    name: str
    rarity: int
    kind: str
    icon: str
    effect_icon: str
    effect: str
    description: str
    ingredients: tuple[WikiItem, ...]
    source: str


@dataclass(frozen=True)
class MonsterAffix:
    name: str
    description: str


@dataclass(frozen=True)
class MonsterEntry:
    entry_id: str
    resists: tuple[tuple[str, float], ...]
    rewards: tuple[WikiItem, ...]
    affixes: tuple[MonsterAffix, ...]


@dataclass(frozen=True)
class MonsterWiki:
    monster_id: str
    name: str
    title: str
    special_name: str
    kind: str
    icon: str
    description: str
    tips: str
    entries: tuple[MonsterEntry, ...]


def parse_query(text: str) -> tuple[str, int]:
    """抽出中文名；≥20 的数字当等级，默认 90。1–6 留给命座别名，不当等级。"""
    name = "".join(_ZH_NAME.findall(text)).strip()
    level = 90
    nums = _NUM_IN_TEXT.findall(text)
    if len(nums) == 1:
        n = int(nums[0])
        if 20 <= n <= 90:
            level = n
        elif n == 1:
            level = 1
    return name, level


def strip_ambr_text(text: str) -> str:
    raw = text.replace("\\n", "\n")
    raw = _COLOR_RE.sub("", raw)
    raw = _HTML_RE.sub("", raw)
    return raw.strip()


def ambr_keep_color(text: str) -> str:
    raw = text.replace("\\n", "\n")
    raw = re.sub(r"</?i>", "", raw)
    return raw.strip()


def merge_refinements(texts: tuple[str, ...]) -> str:
    cleaned = tuple(strip_ambr_text(t) for t in texts if t)
    if not cleaned:
        return "无特效"
    if len(cleaned) == 1:
        return cleaned[0]
    groups = tuple(_REFINE_NUM.findall(t) for t in cleaned)
    n0 = len(groups[0])
    if n0 == 0 or any(len(g) != n0 for g in groups):
        return cleaned[-1]
    pos = 0

    def _repl(_m: re.Match[str]) -> str:
        nonlocal pos
        chunk = "/".join(g[pos] for g in groups)
        pos += 1
        return chunk

    return _REFINE_NUM.sub(_repl, cleaned[0])


def _as_map(raw: object, label: str) -> Mapping[str, object]:
    if not isinstance(raw, dict):
        raise TypeError(label)
    return raw


def _req_str(data: Mapping[str, object], key: str) -> str:
    if key not in data:
        raise KeyError(key)
    val = data[key]
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return str(val)
    raise TypeError(key)


def _opt_str(data: Mapping[str, object], key: str) -> str:
    if key not in data:
        return ""
    val = data[key]
    if val is None:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return str(val)
    return ""


def _req_int(data: Mapping[str, object], key: str) -> int:
    if key not in data:
        raise KeyError(key)
    val = data[key]
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(key)
    return int(val)


def _opt_int(data: Mapping[str, object], key: str) -> int:
    if key not in data:
        return 0
    val = data[key]
    if val is None:
        return 0
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(key)
    return int(val)


def _req_float(data: Mapping[str, object], key: str) -> float:
    if key not in data:
        raise KeyError(key)
    val = data[key]
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(key)
    return float(val)


def _opt_float(data: Mapping[str, object], key: str) -> float:
    if key not in data:
        return 0.0
    val = data[key]
    if val is None:
        return 0.0
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(key)
    return float(val)


def _opt_map(data: Mapping[str, object], key: str) -> Mapping[str, object] | None:
    if key not in data:
        return None
    val = data[key]
    if val is None:
        return None
    if not isinstance(val, dict):
        raise TypeError(key)
    return val


async def _read_json(path: Path) -> Mapping[str, object] | None:
    if not path.exists():
        return None
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    if not text.strip() or text.strip() == "null":
        return None
    raw = json.loads(text)
    if not isinstance(raw, dict):
        return None
    return raw


async def _write_json(path: Path, data: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False))


async def _load_id_json(
    file_id: str,
    cache_dir: Path,
    fetch: Callable[[str], Awaitable[object | None]],
    seed_subdir: str = "",
) -> Mapping[str, object] | None:
    cached = await _read_json(cache_dir / f"{file_id}.json")
    if cached is not None:
        return cached
    if seed_subdir:
        seed = await _read_json(_SEED_DATA / seed_subdir / f"{file_id}.json")
        if seed is not None:
            await _write_json(cache_dir / f"{file_id}.json", seed)
            return seed
    raw = await fetch(file_id)
    if raw is None:
        return None
    data = _as_map(raw, file_id)
    await _write_json(cache_dir / f"{file_id}.json", data)
    return data


async def _ambr_payload(url: str) -> Mapping[str, object] | None:
    async with AsyncClient(timeout=30) as client:
        req = await client.get(url, headers=_HEADER)
        raw = req.json()
    if not isinstance(raw, dict):
        return None
    code: object = None
    if "code" in raw:
        code = raw["code"]
    elif "response" in raw:
        code = raw["response"]
    if code != 200:
        return None
    if "data" not in raw:
        return None
    payload = raw["data"]
    if not isinstance(payload, dict):
        return None
    return payload


def _weapon_zh(raw: str) -> str:
    if raw in WEAPON_TYPE:
        return WEAPON_TYPE[raw]
    return raw


def _element_pair(raw: str) -> tuple[str, str]:
    if raw in _ELEM_EN:
        en = _ELEM_EN[raw]
    else:
        en = "Cryo"
    if raw in ELEMENT_MAP:
        zh = ELEMENT_MAP[raw]
    elif en == "Anemo":
        zh = "风"
    elif en == "Cryo":
        zh = "冰"
    elif en == "Dendro":
        zh = "草"
    elif en == "Hydro":
        zh = "水"
    elif en == "Electro":
        zh = "雷"
    elif en == "Geo":
        zh = "岩"
    elif en == "Pyro":
        zh = "火"
    else:
        zh = raw
    return en, zh


def _region_zh(raw: str) -> str:
    if raw in _REGION_ZH:
        return _REGION_ZH[raw]
    return raw


def _prop_zh(raw: str) -> str:
    if raw in PROP_MAP:
        return PROP_MAP[raw]
    return raw


def _fmt_sub(name: str, value: float) -> str:
    total = value
    if name in _BASE_SUB:
        total = _BASE_SUB[name] + value
    if name in _FLAT_SUB:
        return str(int(round(total)))
    return f"{total * 100:.1f}%"


def _fmt_param(kind: str, value: float) -> str:
    if kind in {"F1P", "F2P", "P"}:
        pct = value * 100
        if kind == "F1P":
            return f"{pct:.1f}%"
        if kind == "F2P":
            return f"{pct:.2f}%"
        return f"{round(pct)}%"
    if kind == "F1":
        return f"{value:.1f}"
    if kind == "F2":
        return f"{value:.2f}"
    if kind == "I":
        return str(int(round(value)))
    return f"{value:.2f}"


def _char_curve(level: int, curve_type: str) -> float:
    if level < 1 or level > len(GROW_CURVE_LIST):
        raise ValueError(level)
    row = GROW_CURVE_LIST[level - 1]
    if "curveInfos" not in row:
        raise KeyError("curveInfos")
    infos = row["curveInfos"]
    if not isinstance(infos, list):
        raise TypeError("curveInfos")
    for info in infos:
        if not isinstance(info, dict):
            continue
        if "type" not in info or "value" not in info:
            continue
        if info["type"] != curve_type:
            continue
        val = info["value"]
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            continue
        return float(val)
    raise KeyError(curve_type)


def _weapon_curve(level: int, curve_type: str) -> float:
    key = str(level)
    if key not in WEAPON_GROW_CURVE:
        raise KeyError(key)
    row = WEAPON_GROW_CURVE[key]
    if "curveInfos" not in row:
        raise KeyError("curveInfos")
    infos = row["curveInfos"]
    if not isinstance(infos, dict):
        raise TypeError("curveInfos")
    if curve_type not in infos:
        raise KeyError(curve_type)
    val = infos[curve_type]
    if isinstance(val, bool) or not isinstance(val, (int, float)):
        raise TypeError(curve_type)
    return float(val)


def _pick_promote(promotes: list[Mapping[str, object]], level: int) -> Mapping[str, object]:
    chosen = promotes[0]
    for item in promotes:
        unlock = _opt_int(item, "unlockMaxLevel")
        if unlock <= level:
            chosen = item
    return chosen


def _multi_msg(kind: str, names: list[str]) -> str:
    shown = names[:12]
    extra = f" 等{len(names)}个" if len(names) > 12 else ""
    return f"找到多个{kind}：{('、'.join(shown))}{extra}。请输入更完整的名称。"


async def resolve_char_id(name: str) -> str | list[str]:
    alias = await alias_to_char_name(name)
    if alias in _TRAVELER_ID:
        return _TRAVELER_ID[alias]
    cid = await name_to_avatar_id(alias)
    if cid and not cid.startswith("10000005") and not cid.startswith("10000007"):
        return cid
    hits: list[tuple[str, str]] = []
    for kid, raw in charList.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        cname = raw["name"]
        if not isinstance(cname, str) or cname.startswith("奇偶"):
            continue
        if cname == "旅行者":
            continue
        if alias == cname or name == cname:
            return str(kid)
        if alias in cname or name in cname:
            hits.append((str(kid), cname))
    if len(hits) == 1:
        return hits[0][0]
    if hits:
        return [h[1] for h in hits]
    if cid:
        return cid
    return []


def _item_from_bag(
    bag: Mapping[str, object] | None,
    item_id: str,
    count: int,
) -> WikiItem:
    name = item_id
    icon = f"UI_ItemIcon_{item_id}"
    rank = 1
    if bag is not None and item_id in bag:
        entry = bag[item_id]
        if isinstance(entry, dict):
            name = _opt_str(entry, "name") or name
            icon = _opt_str(entry, "icon") or icon
            rank = _opt_int(entry, "rank") or rank
    return WikiItem(item_id=item_id, name=name, icon=icon, count=count, rank=rank)


def _sum_costs(
    cost_maps: list[Mapping[str, object]],
    bag: Mapping[str, object] | None,
) -> tuple[tuple[WikiItem, ...], int]:
    totals: dict[str, int] = {}
    mora = 0
    for block in cost_maps:
        for kid, raw in block.items():
            if kid == "coinCost":
                continue
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                continue
            n = int(raw)
            if kid in totals:
                totals[kid] += n
            else:
                totals[kid] = n
        mora += _opt_int(block, "coinCost")
    items = tuple(_item_from_bag(bag, kid, totals[kid]) for kid in totals)
    return items, mora


def _parse_talent_rows(promote: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    if "description" not in promote or "params" not in promote:
        return ()
    desc = promote["description"]
    params = promote["params"]
    if not isinstance(desc, list) or not isinstance(params, list):
        return ()
    values: list[float] = []
    for p in params:
        if isinstance(p, bool) or not isinstance(p, (int, float)):
            values.append(0.0)
        else:
            values.append(float(p))
    rows: list[tuple[str, str]] = []
    for line in desc:
        if not isinstance(line, str) or not line.strip():
            continue
        if "|" not in line:
            continue
        label, spec = line.split("|", 1)
        bits: list[str] = []
        last = 0
        for m in _PARAM_RE.finditer(spec):
            bits.append(spec[last : m.start()])
            idx = int(m.group(1)) - 1
            kind = m.group(2)
            if 0 <= idx < len(values):
                bits.append(_fmt_param(kind, values[idx]))
            else:
                bits.append("—")
            last = m.end()
        bits.append(spec[last:])
        rows.append((label, "".join(bits)))
    return tuple(rows)


def _parse_talents(talent_raw: Mapping[str, object]) -> tuple[tuple[CharTalent, ...], list[Mapping[str, object]]]:
    combat: list[tuple[int, Mapping[str, object]]] = []
    passive: list[tuple[int, Mapping[str, object]]] = []
    for key, raw in talent_raw.items():
        if not isinstance(raw, dict):
            continue
        ttype = _opt_int(raw, "type")
        name = _opt_str(raw, "name")
        icon = _opt_str(raw, "icon")
        if not name or name == "暂缺":
            continue
        order = int(key) if key.isdigit() else 99
        if ttype in {0, 1} and "promote" in raw:
            combat.append((order, raw))
        elif ttype == 2 and icon:
            passive.append((order, raw))
    combat.sort(key=lambda x: x[0])
    passive.sort(key=lambda x: x[0])
    slots = ("A", "E", "Q", "特")
    out: list[CharTalent] = []
    per_skill_costs: list[list[Mapping[str, object]]] = []
    for i, (_order, skill) in enumerate(combat[:4]):
        promote_map = _opt_map(skill, "promote")
        rows: tuple[tuple[str, str], ...] = ()
        this_costs: list[Mapping[str, object]] = []
        if promote_map is not None:
            lv = promote_map["10"] if "10" in promote_map else None
            if lv is None:
                for pk, pv in promote_map.items():
                    if str(pk) == "10" and isinstance(pv, dict):
                        lv = pv
                        break
            if isinstance(lv, dict):
                rows = _parse_talent_rows(lv)
            for pk, pv in promote_map.items():
                if not isinstance(pv, dict):
                    continue
                costs = _opt_map(pv, "costItems")
                block: dict[str, object] = {}
                if costs is not None:
                    block.update(costs)
                coin = _opt_int(pv, "coinCost")
                if coin:
                    block["coinCost"] = coin
                if block:
                    this_costs.append(block)
        if this_costs:
            per_skill_costs.append(this_costs)
        out.append(
            CharTalent(
                slot=slots[i] if i < len(slots) else "特",
                name=_req_str(skill, "name"),
                icon=_opt_str(skill, "icon"),
                description=ambr_keep_color(_opt_str(skill, "description")),
                cooldown=_opt_int(skill, "cooldown"),
                cost=_opt_int(skill, "cost"),
                rows=rows,
            )
        )
    for _order, skill in passive:
        out.append(
            CharTalent(
                slot="P",
                name=_req_str(skill, "name"),
                icon=_opt_str(skill, "icon"),
                description=ambr_keep_color(_opt_str(skill, "description")),
                cooldown=0,
                cost=0,
                rows=(),
            )
        )
    cost_blocks: list[Mapping[str, object]] = []
    if per_skill_costs:
        cost_blocks = max(per_skill_costs, key=len)
    return tuple(out), cost_blocks


def _parse_consts(raw: Mapping[str, object]) -> tuple[CharConst, ...]:
    items: list[tuple[int, Mapping[str, object]]] = []
    for key, val in raw.items():
        if not isinstance(val, dict):
            continue
        idx = _opt_int(val, "id") if "id" in val else (int(key) if key.isdigit() else -1)
        items.append((idx, val))
    items.sort(key=lambda x: x[0])
    out: list[CharConst] = []
    n = 1
    for idx, val in items:
        name = _opt_str(val, "name")
        if not name:
            continue
        out.append(
            CharConst(
                index=n,
                name=name,
                icon=_opt_str(val, "icon"),
                description=ambr_keep_color(_opt_str(val, "description")),
            )
        )
        n += 1
        if n > 6:
            break
    return tuple(out)


def _char_stats(
    upgrade: Mapping[str, object],
    level: int,
) -> tuple[int, int, int, str, str]:
    props_raw = upgrade["prop"] if "prop" in upgrade else []
    if not isinstance(props_raw, list) or len(props_raw) < 3:
        raise TypeError("upgrade.prop")
    promote_raw = upgrade["promote"] if "promote" in upgrade else []
    if not isinstance(promote_raw, list) or not promote_raw:
        raise TypeError("upgrade.promote")
    promotes = [_as_map(p, "promote") for p in promote_raw if isinstance(p, dict)]
    picked = _pick_promote(promotes, level)
    add = _opt_map(picked, "addProps")
    hp_p = _as_map(props_raw[0], "hp")
    atk_p = _as_map(props_raw[1], "atk")
    def_p = _as_map(props_raw[2], "def")

    def _stat(prop: Mapping[str, object], add_key: str) -> int:
        init = _req_float(prop, "initValue")
        curve = _req_str(prop, "type")
        extra = 0.0
        if add is not None and add_key in add:
            extra = _opt_float(add, add_key)
        return int(_char_curve(level, curve) * init + extra)

    hp = _stat(hp_p, "FIGHT_PROP_BASE_HP")
    atk = _stat(atk_p, "FIGHT_PROP_BASE_ATTACK")
    defense = _stat(def_p, "FIGHT_PROP_BASE_DEFENSE")
    sub_name = "—"
    sub_val = "—"
    if add is not None:
        for key, val in add.items():
            if key in {"FIGHT_PROP_BASE_HP", "FIGHT_PROP_BASE_ATTACK", "FIGHT_PROP_BASE_DEFENSE"}:
                continue
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                continue
            sub_name = _prop_zh(key)
            sub_val = _fmt_sub(sub_name, float(val))
            break
    return hp, atk, defense, sub_name, sub_val


def parse_char_wiki(raw: Mapping[str, object], level: int) -> CharWiki:
    fetter = _as_map(raw["fetter"], "fetter") if "fetter" in raw else {}
    upgrade = _as_map(raw["upgrade"], "upgrade")
    talent_raw = _opt_map(raw, "talent")
    const_raw = _opt_map(raw, "constellation")
    bag = _opt_map(raw, "items")
    element_raw = _opt_str(raw, "element")
    en, zh = _element_pair(element_raw)
    birthday_s = "—"
    if "birthday" in raw and isinstance(raw["birthday"], list) and len(raw["birthday"]) >= 2:
        m, d = raw["birthday"][0], raw["birthday"][1]
        if isinstance(m, int) and isinstance(d, int) and m > 0 and d > 0:
            birthday_s = f"{m}月{d}日"
    cv = ""
    if "cv" in fetter and isinstance(fetter["cv"], dict):
        cv_map = fetter["cv"]
        if "CHS" in cv_map and isinstance(cv_map["CHS"], str):
            cv = cv_map["CHS"]
    talents, talent_costs = _parse_talents(talent_raw) if talent_raw is not None else ((), [])
    consts = _parse_consts(const_raw) if const_raw is not None else ()
    hp, atk, defense, sub_name, sub_val = _char_stats(upgrade, level)
    ascend_blocks: list[Mapping[str, object]] = []
    mora_a = 0
    if "promote" in upgrade and isinstance(upgrade["promote"], list):
        for p in upgrade["promote"]:
            if not isinstance(p, dict):
                continue
            costs = _opt_map(p, "costItems")
            block: dict[str, object] = {}
            if costs is not None:
                block.update(costs)
            coin = _opt_int(p, "coinCost")
            if coin:
                block["coinCost"] = coin
                mora_a += coin
            if block:
                ascend_blocks.append(block)
    ascend_items, _mora_from_items = _sum_costs(ascend_blocks, bag)
    talent_items, mora_t = _sum_costs(talent_costs, bag)
    return CharWiki(
        char_id=str(raw["id"]) if "id" in raw else "",
        name=_req_str(raw, "name"),
        title=_opt_str(fetter, "title"),
        element=en,
        element_zh=zh,
        weapon=_weapon_zh(_opt_str(raw, "weaponType")),
        rarity=_opt_int(raw, "rank") or 4,
        region=_region_zh(_opt_str(raw, "region")),
        birthday=birthday_s,
        constellation=_opt_str(fetter, "constellation"),
        native=_opt_str(fetter, "native"),
        cv=cv,
        description=strip_ambr_text(_opt_str(fetter, "detail")),
        icon=_opt_str(raw, "icon"),
        level=level,
        hp=hp,
        atk=atk,
        defense=defense,
        substat=sub_name,
        substat_value=sub_val,
        talents=talents,
        consts=consts,
        ascend_items=ascend_items,
        talent_items=talent_items,
        mora_ascend=mora_a,
        mora_talent=mora_t,
    )


def parse_weapon_wiki(raw: Mapping[str, object], level: int) -> WeaponWiki:
    upgrade = _as_map(raw["upgrade"], "upgrade")
    bag = _opt_map(raw, "items")
    props_raw = upgrade["prop"] if "prop" in upgrade else []
    if not isinstance(props_raw, list) or not props_raw:
        raise TypeError("upgrade.prop")
    atk_p = _as_map(props_raw[0], "atk")
    atk_init = _req_float(atk_p, "initValue")
    atk_curve = _req_str(atk_p, "type")
    sub_name = "无副词条"
    sub_init = 0.0
    sub_curve = ""
    if len(props_raw) > 1:
        sub_p = _as_map(props_raw[1], "sub")
        if "propType" in sub_p:
            sub_name = _prop_zh(_req_str(sub_p, "propType"))
            sub_init = _opt_float(sub_p, "initValue")
            sub_curve = _opt_str(sub_p, "type")
    promote_raw = upgrade["promote"] if "promote" in upgrade else []
    promotes = (
        [_as_map(p, "promote") for p in promote_raw if isinstance(p, dict)] if isinstance(promote_raw, list) else []
    )
    picked = _pick_promote(promotes, level) if promotes else {}
    add = _opt_map(picked, "addProps") if picked else None
    extra_atk = 0.0
    if add is not None and "FIGHT_PROP_BASE_ATTACK" in add:
        extra_atk = _opt_float(add, "FIGHT_PROP_BASE_ATTACK")
    atk_max = int(_weapon_curve(level, atk_curve) * atk_init + extra_atk)
    sub_max_s = "—"
    sub_base_s = "—"
    if sub_curve:
        sub_base_s = _fmt_sub(sub_name, sub_init)
        sub_max_s = _fmt_sub(sub_name, sub_init * _weapon_curve(level, sub_curve))
    effect_name = "无特效"
    refinements: list[str] = []
    affix = _opt_map(raw, "affix")
    if affix:
        first = next(iter(affix.values()))
        if isinstance(first, dict):
            effect_name = _opt_str(first, "name") or "无特效"
            up = _opt_map(first, "upgrade")
            if up is not None:
                for i in range(5):
                    k = str(i)
                    if k not in up:
                        continue
                    val = up[k]
                    if isinstance(val, str):
                        refinements.append(val)
    effect = merge_refinements(tuple(refinements))
    blocks: list[Mapping[str, object]] = []
    mora = 0
    for p in promotes:
        costs = _opt_map(p, "costItems")
        block: dict[str, object] = {}
        if costs is not None:
            block.update(costs)
        coin = _opt_int(p, "coinCost")
        if coin:
            block["coinCost"] = coin
            mora += coin
        if block:
            blocks.append(block)
    items, _m = _sum_costs(blocks, bag)
    rarity = _opt_int(raw, "rank") or 1
    ore = _WEAPON_ORE[rarity] if rarity in _WEAPON_ORE else 0
    return WeaponWiki(
        weapon_id=str(raw["id"]) if "id" in raw else "",
        name=_req_str(raw, "name"),
        weapon_type=_weapon_zh(_opt_str(raw, "type")),
        rarity=rarity,
        description=strip_ambr_text(_opt_str(raw, "description")),
        icon=_opt_str(raw, "icon"),
        level=level,
        atk_base=int(round(atk_init)),
        atk_max=atk_max,
        substat=sub_name,
        sub_base=sub_base_s,
        sub_max=sub_max_s,
        effect_name=effect_name,
        effect=effect,
        refinements=tuple(strip_ambr_text(t) for t in refinements),
        items=items,
        mora=mora,
        ore=ore,
    )


def parse_artifact_wiki(raw: Mapping[str, object]) -> ArtifactWiki:
    rarity: list[int] = []
    if "levelList" in raw and isinstance(raw["levelList"], list):
        for x in raw["levelList"]:
            if isinstance(x, int):
                rarity.append(x)
    effect1 = ""
    effect2 = ""
    effect4 = ""
    affix = _opt_map(raw, "affixList")
    if affix is not None:
        texts = [v for v in affix.values() if isinstance(v, str)]
        if len(texts) == 1:
            effect1 = texts[0]
        elif len(texts) >= 2:
            effect2 = texts[0]
            effect4 = texts[1]
    pieces: list[ArtifactPiece] = []
    suit = _opt_map(raw, "suit")
    if suit is not None:
        for key, slot_zh in _SUIT_ORDER:
            if key not in suit:
                continue
            piece = suit[key]
            if not isinstance(piece, dict):
                continue
            pieces.append(
                ArtifactPiece(
                    slot=slot_zh,
                    name=_opt_str(piece, "name"),
                    description=strip_ambr_text(_opt_str(piece, "description")),
                    icon=_opt_str(piece, "icon"),
                )
            )
    return ArtifactWiki(
        set_id=str(raw["id"]) if "id" in raw else "",
        name=_req_str(raw, "name"),
        rarity=tuple(rarity),
        icon=_opt_str(raw, "icon"),
        effect2=effect2,
        effect4=effect4,
        effect1=effect1,
        pieces=tuple(pieces),
        source=_opt_str(raw, "source"),
    )


def parse_food_wiki(raw: Mapping[str, object], food_id: str) -> FoodWiki:
    recipe = _opt_map(raw, "recipe")
    effect = ""
    effect_icon = ""
    ings: list[WikiItem] = []
    if recipe is not None:
        effect_icon = _opt_str(recipe, "effectIcon")
        eff = _opt_map(recipe, "effect")
        if eff is not None and "0" in eff and isinstance(eff["0"], str):
            effect = ambr_keep_color(eff["0"])
        inputs = _opt_map(recipe, "input")
        if inputs is not None:
            for kid, val in inputs.items():
                if not isinstance(val, dict):
                    continue
                ings.append(
                    WikiItem(
                        item_id=kid,
                        name=_opt_str(val, "name") or kid,
                        icon=_opt_str(val, "icon") or f"UI_ItemIcon_{kid}",
                        count=_opt_int(val, "count") or 1,
                        rank=_opt_int(val, "rank") or 1,
                    )
                )
    icon = _opt_str(raw, "icon")
    source = ""
    if "source" in raw and isinstance(raw["source"], list) and raw["source"]:
        first = raw["source"][0]
        if isinstance(first, dict):
            source = _opt_str(first, "name")
    if not effect_icon:
        effect_icon = _opt_str(raw, "effectIcon")
    return FoodWiki(
        food_id=food_id,
        name=_req_str(raw, "name"),
        rarity=_opt_int(raw, "rank") or 1,
        kind=_opt_str(raw, "type") or "食物",
        icon=icon,
        effect_icon=effect_icon,
        effect=effect,
        description=strip_ambr_text(_opt_str(raw, "description")),
        ingredients=tuple(ings),
        source=source,
    )


def parse_monster_wiki(raw: Mapping[str, object]) -> MonsterWiki:
    kind_raw = _opt_str(raw, "type")
    kind = _MONSTER_TYPE_ZH[kind_raw] if kind_raw in _MONSTER_TYPE_ZH else kind_raw
    entries_out: list[MonsterEntry] = []
    entries = _opt_map(raw, "entries")
    if entries is not None:
        for eid, val in entries.items():
            if not isinstance(val, dict):
                continue
            res_map = _opt_map(val, "resistance")
            resists: list[tuple[str, float]] = []
            if res_map is not None:
                for key, label in _RES_KEYS:
                    resists.append((label, _opt_float(res_map, key)))
            rewards: list[WikiItem] = []
            reward = _opt_map(val, "reward")
            if reward is not None:
                for kid, item in reward.items():
                    if not isinstance(item, dict):
                        continue
                    count_s = _opt_str(item, "count")
                    count = int(count_s) if count_s.isdigit() else 0
                    rewards.append(
                        WikiItem(
                            item_id=kid,
                            name=_opt_str(item, "name") or kid,
                            icon=_opt_str(item, "icon") or f"UI_ItemIcon_{kid}",
                            count=count,
                            rank=_opt_int(item, "rank") or 1,
                        )
                    )
            affixes: list[MonsterAffix] = []
            if "affix" in val and isinstance(val["affix"], list):
                for af in val["affix"]:
                    if not isinstance(af, dict):
                        continue
                    an = _opt_str(af, "name")
                    if not an:
                        continue
                    affixes.append(MonsterAffix(name=an, description=strip_ambr_text(_opt_str(af, "description"))))
            entries_out.append(
                MonsterEntry(
                    entry_id=str(eid),
                    resists=tuple(resists),
                    rewards=tuple(rewards),
                    affixes=tuple(affixes),
                )
            )
    return MonsterWiki(
        monster_id=str(raw["id"]) if "id" in raw else "",
        name=_req_str(raw, "name"),
        title=_opt_str(raw, "title"),
        special_name=_opt_str(raw, "specialName"),
        kind=kind,
        icon=_opt_str(raw, "icon"),
        description=strip_ambr_text(_opt_str(raw, "description")),
        tips=strip_ambr_text(_opt_str(raw, "tips")),
        entries=tuple(entries_out),
    )


async def load_char_wiki(name: str, level: int) -> CharWiki | str:
    if not name:
        return "请输入角色名。"
    found = await resolve_char_id(name)
    if isinstance(found, list):
        if not found:
            return f"未找到角色「{name}」。"
        return _multi_msg("角色", found)
    raw = await _load_id_json(found, WIKI_DATA_CHAR, get_ambr_char_data, "char")
    if raw is None:
        return f"未找到角色「{name}」的图鉴数据。"
    return parse_char_wiki(raw, level)


def _weapon_hits(name: str) -> list[tuple[str, str]]:
    exact: list[tuple[str, str]] = []
    part: list[tuple[str, str]] = []
    for kid, raw in weaponList.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        if "isWeaponSkin" in raw and raw["isWeaponSkin"] is True:
            continue
        wname = raw["name"]
        if not isinstance(wname, str):
            continue
        if wname == name:
            exact.append((str(kid), wname))
        elif name in wname:
            part.append((str(kid), wname))
    if exact:
        return exact
    return part


async def load_weapon_wiki(name: str, level: int) -> WeaponWiki | str:
    if not name:
        return "请输入武器名。"
    hits = _weapon_hits(name)
    if not hits:
        return f"未找到武器「{name}」。"
    if len(hits) > 1:
        return _multi_msg("武器", [h[1] for h in hits])
    wid = hits[0][0]
    raw = await _load_id_json(wid, WIKI_DATA_WEAPON, get_ambr_weapon_data, "weapon")
    if raw is None:
        return f"未找到武器「{name}」的图鉴数据。"
    return parse_weapon_wiki(raw, level)


def _artifact_hits(name: str) -> list[tuple[str, str]]:
    exact: list[tuple[str, str]] = []
    part: list[tuple[str, str]] = []
    for kid, raw in reliquaryList.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        aname = raw["name"]
        if not isinstance(aname, str):
            continue
        if aname == name:
            exact.append((str(kid), aname))
        elif name in aname:
            part.append((str(kid), aname))
    if exact:
        return exact
    return part


async def load_artifact_wiki(name: str) -> ArtifactWiki | str:
    if not name:
        return "请输入圣遗物套装名。"
    hits = _artifact_hits(name)
    if not hits:
        return f"未找到圣遗物「{name}」。"
    if len(hits) > 1:
        return _multi_msg("圣遗物", [h[1] for h in hits])
    sid = hits[0][0]
    raw = await _load_id_json(sid, WIKI_DATA_REL, get_ambr_reliquary_data, "reliquary")
    if raw is None:
        listed = reliquaryList[sid] if sid in reliquaryList and isinstance(reliquaryList[sid], dict) else None
        if listed is None:
            return f"未找到圣遗物「{name}」的图鉴数据。"
        return parse_artifact_wiki(listed)
    return parse_artifact_wiki(raw)


def _pick_food_id(hits: list[str], items: Mapping[str, object]) -> str:
    best = hits[0]
    best_score = -1
    for hid in hits:
        if hid not in items or not isinstance(items[hid], dict):
            continue
        entry = items[hid]
        icon = _opt_str(entry, "icon")
        score = 0
        if icon and "Recipe" not in icon:
            score += 20
        if hid.isdigit():
            n = int(hid)
            if n >= 108000:
                score += 10
            score += 1 if n > 10000 else 0
        if score > best_score:
            best_score = score
            best = hid
    return best


async def _food_list() -> Mapping[str, object]:
    cached = await _read_json(WIKI_DATA_FOOD / "_list.json")
    if cached is not None:
        return cached
    payload = await _ambr_payload(_AMBR_FOOD_LIST)
    if payload is None or "items" not in payload:
        return {}
    items = payload["items"]
    if not isinstance(items, dict):
        return {}
    await _write_json(WIKI_DATA_FOOD / "_list.json", items)
    return items


async def load_food_wiki(name: str) -> FoodWiki | str:
    if not name:
        return "请输入食物名。"
    items = await _food_list()
    if not items:
        return "食物图鉴列表获取失败。"
    exact: list[str] = []
    part: list[str] = []
    names: dict[str, str] = {}
    for kid, raw in items.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        fname = raw["name"]
        if not isinstance(fname, str):
            continue
        names[str(kid)] = fname
        if fname == name:
            exact.append(str(kid))
        elif name in fname:
            part.append(str(kid))
    hits = exact or part
    if not hits:
        return f"未找到食物「{name}」。"
    if exact:
        fid = _pick_food_id(exact, items)
    elif len({names[i] for i in part if i in names}) == 1:
        fid = _pick_food_id(part, items)
    elif len(part) > 1:
        return _multi_msg("食物", [names[i] for i in part if i in names])
    else:
        fid = part[0]

    async def _fetch(file_id: str) -> Mapping[str, object] | None:
        return await _ambr_payload(_AMBR_FOOD_URL.format(file_id))

    raw = await _load_id_json(fid, WIKI_DATA_FOOD, _fetch)
    if raw is None:
        return f"未找到食物「{name}」的图鉴数据。"
    return parse_food_wiki(raw, fid)


async def _monster_index() -> dict[str, tuple[str, str]]:
    """name -> (id, icon)，合并 ExtraMonster 与 ambr 列表。"""
    out: dict[str, tuple[str, str]] = {}
    for kid, raw in ex_monster_data.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        n = raw["name"]
        if not isinstance(n, str):
            continue
        icon = raw["icon"] if "icon" in raw and isinstance(raw["icon"], str) else ""
        out[n] = (str(kid), icon)
    cached = await _read_json(WIKI_DATA_MONSTER / "_list.json")
    items: Mapping[str, object] | None = cached
    if items is None:
        listed = await get_ambr_monster_list()
        if listed is not None and "items" in listed:
            raw_items = listed["items"]
            if isinstance(raw_items, dict):
                await _write_json(WIKI_DATA_MONSTER / "_list.json", raw_items)
                items = raw_items
    if items is None:
        return out
    for kid, raw in items.items():
        if not isinstance(raw, dict) or "name" not in raw:
            continue
        n = raw["name"]
        if not isinstance(n, str):
            continue
        icon = raw["icon"] if "icon" in raw and isinstance(raw["icon"], str) else ""
        out[n] = (str(kid), icon)
    return out


async def load_monster_wiki(name: str) -> MonsterWiki | str:
    if not name:
        return "请输入原魔名。"
    index = await _monster_index()
    exact = [n for n in index if n == name]
    part = [n for n in index if name in n]
    hits = exact or part
    if not hits:
        return f"未找到原魔「{name}」。"
    if len(hits) > 1:
        return _multi_msg("原魔", hits)
    mid = index[hits[0]][0]
    raw = await _load_id_json(mid, WIKI_DATA_MONSTER, get_ambr_monster_data)
    if raw is None:
        return f"未找到原魔「{name}」的图鉴数据。"
    return parse_monster_wiki(raw)


def char_ai_text(data: CharWiki) -> str:
    talent_n = "；".join(f"{t.slot} {t.name}" for t in data.talents if t.slot != "P")
    cons = "；".join(f"C{c.index} {c.name}" for c in data.consts)
    return (
        f"原神角色 {data.name}（{data.title}）{data.rarity}星 {data.element_zh} {data.weapon}\n"
        f"命之座 {data.constellation} 生日 {data.birthday} CV {data.cv} 地区 {data.region}\n"
        f"Lv{data.level} HP {data.hp} 攻击 {data.atk} 防御 {data.defense} {data.substat} {data.substat_value}\n"
        f"{data.description}\n天赋：{talent_n}\n命座：{cons}"
    )


def weapon_ai_text(data: WeaponWiki) -> str:
    return (
        f"原神武器 {data.name} {data.rarity}星 {data.weapon_type}\n"
        f"攻击力 {data.atk_base}/{data.atk_max} {data.substat} {data.sub_base}/{data.sub_max}\n"
        f"{data.effect_name}：{data.effect}\n{data.description}"
    )


def artifact_ai_text(data: ArtifactWiki) -> str:
    stars = "/".join(str(s) for s in data.rarity)
    if data.effect1:
        fx = f"1件套：{data.effect1}"
    else:
        fx = f"2件套：{data.effect2}\n4件套：{data.effect4}"
    return f"原神圣遗物 {data.name} {stars}星\n{fx}"


def food_ai_text(data: FoodWiki) -> str:
    ings = "、".join(f"{i.name}×{i.count}" for i in data.ingredients)
    return (
        f"原神食物 {data.name} {data.rarity}星\n效果：{strip_ambr_text(data.effect)}\n材料：{ings}\n{data.description}"
    )


def monster_ai_text(data: MonsterWiki) -> str:
    res = ""
    if data.entries:
        bits = [f"{lab} {val:.0%}" for lab, val in data.entries[0].resists]
        res = "抗性 " + " ".join(bits)
    return f"原神原魔 {data.name}（{data.special_name}）{data.kind}\n{data.description}\n{res}"
