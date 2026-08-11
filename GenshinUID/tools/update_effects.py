"""
从 yatta changelog 更新 genshinuid_enka/effect 下全部配置。

覆盖:
  - skill_add.json       全自动 (C3/C5 → A/E/Q)
  - weapon_effect.json   缺项 scaffold + 简单 buff 启发式填充
  - artifact_effect.json 缺项 scaffold + 2 件套简单属性启发式
  - char_effect.json     缺项空壳
  - value_attr.json      缺项按突破副词条启发式
  - char_action.json     缺项从天赋 promote 倍率表生成
  - dmg_map.json         缺项空列表占位 (参考面板需人工)

用法:
  python GenshinUID/tools/update_effects.py -v 7.0
  python GenshinUID/tools/update_effects.py -v 7.0 --dry-run
  python GenshinUID/tools/update_effects.py -v 7.0 --only skill_add,weapon_effect
"""

from __future__ import annotations

import re
import json
import argparse
from copy import deepcopy
from time import sleep
from typing import Any, Dict, List, Tuple, Optional, Sequence
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
EFFECT_PATH = ROOT / "genshinuid_enka" / "effect"
MAP_PATH = ROOT / "utils" / "map" / "data"
CHAR_CACHE = Path(__file__).resolve().parent / "gs_data" / "char"
WEAPON_CACHE = Path(__file__).resolve().parent / "gs_data" / "weapon"
RELIQ_CACHE = Path(__file__).resolve().parent / "gs_data" / "reliquary"

API_BASE = "https://gi.yatta.moe/api/v2"
DEFAULT_VH = "70F0"
DEFAULT_VERSION = "7.0"

ALL_TARGETS = [
    "skill_add",
    "weapon_effect",
    "artifact_effect",
    "char_effect",
    "value_attr",
    "char_action",
    "dmg_map",
]

# ---------- 空模板 ----------

EMPTY_WEAPON_EFFECT: Dict[str, Any] = {
    "normal": {
        "normal_effect": {"1": "", "2": "", "3": "", "4": "", "5": ""},
    },
    "fight": {
        "fight_effect": {"1": "", "2": "", "3": "", "4": "", "5": ""},
        "group_effect": {"1": "", "2": "", "3": "", "4": "", "5": ""},
        "time": 0,
        "extra": {},
    },
}

EMPTY_ARTIFACT_EFFECT: Dict[str, Any] = {
    "normal_effect": {"2": "", "4": ""},
    "fight_effect": {"2": "", "4": ""},
    "group_effect": {"2": "", "4": ""},
}

EMPTY_CHAR_EFFECT: Dict[str, Any] = {
    "normal": {
        "normal_skill": {"50": "", "70": ""},
        "normal_talent": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": ""},
    },
    "fight": {
        "fight_skill": {"50": "", "70": ""},
        "fight_talent": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": ""},
        "group_skill": {"50": "", "70": ""},
        "group_talent": {"1": "", "2": "", "3": "", "4": "", "5": "", "6": ""},
    },
}

# specialProp → value_attr 启发式
SPECIAL_TO_VALUE_ATTR: Dict[str, List[str]] = {
    "FIGHT_PROP_CRITICAL_HURT": ["攻击力", "暴击率", "暴击伤害"],
    "FIGHT_PROP_CRITICAL": ["攻击力", "暴击率", "暴击伤害"],
    "FIGHT_PROP_ATTACK_PERCENT": ["攻击力", "暴击率", "暴击伤害"],
    "FIGHT_PROP_HP_PERCENT": ["血量", "暴击率", "暴击伤害"],
    "FIGHT_PROP_DEFENSE_PERCENT": ["防御力", "暴击率", "暴击伤害"],
    "FIGHT_PROP_ELEMENT_MASTERY": ["元素精通", "暴击率", "暴击伤害"],
    "FIGHT_PROP_CHARGE_EFFICIENCY": ["攻击力", "暴击率", "暴击伤害", "元素充能效率"],
    "FIGHT_PROP_HEAL_ADD": ["血量", "元素充能效率"],
    "FIGHT_PROP_PHYSICAL_ADD_HURT": ["攻击力", "暴击率", "暴击伤害"],
}

# 中文属性 → DSL
STAT_CN_TO_DSL = [
    # 「攻击力提高18%」/「获得…攻击力加成」/「最低18%、最高36%的攻击力加成」
    (r"攻击力(?:提高|提升|加成)\s*(?:最低\s*)?(\d+(?:\.\d+)?)\s*%", "addAtk", True),
    (r"(?:最低\s*)?(\d+(?:\.\d+)?)\s*%[^。；]{0,24}攻击力(?:提高|提升|加成)?", "addAtk", True),
    (r"生命值(?:上限)?(?:提高|提升|加成)\s*(\d+(?:\.\d+)?)\s*%", "addHp", True),
    (r"(\d+(?:\.\d+)?)\s*%[^。；]{0,16}生命值(?:上限)?(?:提高|提升|加成)?", "addHp", True),
    (r"防御力(?:提高|提升|加成)\s*(\d+(?:\.\d+)?)\s*%", "addDef", True),
    (r"元素精通(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*点?", "elementalMastery", False),
    (r"(\d+(?:\.\d+)?)\s*点[^。；]{0,12}元素精通", "elementalMastery", False),
    (r"元素充能效率(?:提高|提升|加成)\s*(\d+(?:\.\d+)?)\s*%", "energyRecharge", True),
    (r"暴击率(?:提高|提升|加成)\s*(\d+(?:\.\d+)?)\s*%", "critRate", True),
    (r"暴击伤害(?:提高|提升|加成)\s*(\d+(?:\.\d+)?)\s*%", "critDmg", True),
    (r"治疗加成(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "healBonus", True),
    (r"造成的伤害(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "dmgBonus", True),
    (r"全元素伤害加成(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "dmgBonus", True),
    (r"物理伤害加成(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "physicalDmgBonus", True),
    # 星烁反应增伤（无冒号：stellarDmgBonus+xx）
    (r"星烁反应伤害(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "stellarDmgBonus", True),
    (r"造成的星烁反应伤害(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "stellarDmgBonus", True),
    (r"星扩散反应伤害(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "stellarSpreadDmgBonus", True),
    (r"星烁反应伤害的暴击伤害(?:提高|提升)\s*(\d+(?:\.\d+)?)\s*%", "stellarCritDmg", True),
]

COND_PREFIX = [
    (r"施放元素战技|使用元素战技|元素战技命中", "E"),
    (r"施放元素爆发|使用元素爆发|元素爆发命中", "Q"),
    (r"普通攻击命中|进行普通攻击", "A"),
    (r"重击命中|进行重击", "B"),
]

INDEX_MAP = ["", "A", "E", "Q"]
LABEL_TYPE_LIST = {
    "普通攻击": "A",
    "重击": "B",
    "下落攻击": "C",
    "攻击": "attack",
    "充能效率": "ce",
    "生命值": "hp",
    "防御": "defense",
    "暴击率": "critrate",
    "暴击伤害": "critDmg",
    "元素精通": "em",
}

_client: Optional[httpx.Client] = None
REPORT: List[str] = []


def log(msg: str) -> None:
    print(msg)
    REPORT.append(msg)


def get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(timeout=90, follow_redirects=True)
    return _client


def with_vh(url: str, vh: str = "") -> str:
    if not vh:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}vh={vh}"


def fetch_json(url: str, retries: int = 5) -> Any:
    last: Optional[Exception] = None
    for i in range(retries):
        try:
            r = get_client().get(url)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            sleep(2 + i * 2)
    raise RuntimeError(f"fetch failed {url}: {last}")


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any, dry_run: bool) -> None:
    if dry_run:
        log(f"[dry-run] 跳过写入 {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    log(f"已写入 {path}")


def strip_html(text: str) -> str:
    text = re.sub(r"\{LINK#[^}]+\}", "", text)
    text = re.sub(r"\{/LINK\}", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.replace("\\n", "\n")


def parse_version_key(version: str) -> Tuple[int, ...]:
    nums = re.findall(r"\d+", version)
    return tuple(int(x) for x in nums) if nums else (0,)


def get_changelog(vh: str) -> Dict[str, Any]:
    url = with_vh(f"{API_BASE}/static/changelog", vh)
    log(f"changelog: {url}")
    data = fetch_json(url)
    return data.get("data", data)


def pick_entry(changelog: Dict[str, Any], version: str) -> Tuple[str, Dict[str, Any]]:
    entries: List[Tuple[str, Dict[str, Any], Tuple[int, ...]]] = []
    for key, val in changelog.items():
        if isinstance(val, dict):
            ver = str(val.get("version", key))
            entries.append((key, val, parse_version_key(ver)))
    if not entries:
        raise RuntimeError("empty changelog")
    entries.sort(key=lambda x: x[2])
    if not version or version.lower() in {"latest", "new", "max"}:
        return entries[-1][0], entries[-1][1]
    target = version.strip()
    for key, val, _ in entries:
        if str(val.get("version", "")) == target or key == target:
            return key, val
    for key, val, _ in reversed(entries):
        ver = str(val.get("version", ""))
        if ver.startswith(target) or target.startswith(ver):
            return key, val
    raise RuntimeError(f"version not found: {target}")


def load_local_list(prefix: str) -> Dict[str, Any]:
    files = sorted(MAP_PATH.glob(f"{prefix}_*.json"), reverse=True)
    for path in files:
        try:
            data = load_json(path)
            if isinstance(data, dict) and data:
                log(f"本地列表 {path.name} ({len(data)})")
                return data
        except Exception as e:  # noqa: BLE001
            log(f"读本地列表失败 {path}: {e}")
    return {}


def find_item(items: Dict[str, Any], item_id: str) -> Optional[Dict[str, Any]]:
    sid = str(item_id)
    hit = items.get(sid)
    if isinstance(hit, dict):
        return hit
    for k, v in items.items():
        if isinstance(v, dict) and (str(k) == sid or str(v.get("id", "")) == sid):
            return v
    return None


def cache_get(path: Path, url: str) -> Dict[str, Any]:
    if path.exists():
        try:
            return load_json(path)
        except Exception:  # noqa: BLE001
            pass
    data = fetch_json(url)
    payload = data.get("data", data) if isinstance(data, dict) else data
    if not isinstance(payload, dict):
        raise RuntimeError(f"unexpected payload from {url}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def fetch_avatar(avatar_id: str, vh: str) -> Dict[str, Any]:
    aid = str(avatar_id)
    path = CHAR_CACHE / f"{aid}.json"
    url = with_vh(f"{API_BASE}/chs/avatar/{aid}", vh)
    return cache_get(path, url)


def fetch_weapon(weapon_id: str, vh: str) -> Dict[str, Any]:
    wid = str(weapon_id)
    path = WEAPON_CACHE / f"{wid}.json"
    url = with_vh(f"{API_BASE}/chs/weapon/{wid}", vh)
    return cache_get(path, url)


def fetch_reliquary(rel_id: str, vh: str) -> Dict[str, Any]:
    rid = str(rel_id)
    path = RELIQ_CACHE / f"{rid}.json"
    url = with_vh(f"{API_BASE}/chs/reliquary/{rid}", vh)
    return cache_get(path, url)


# ---------- skill_add ----------


def icon_kind(icon: str) -> Optional[str]:
    if not icon:
        return None
    if icon.startswith("Skill_A"):
        return "A"
    if icon.startswith("Skill_S"):
        return "E"
    if icon.startswith("Skill_E"):
        return "Q"
    return None


def build_talent_name_map(avatar: Dict[str, Any]) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for v in (avatar.get("talent") or {}).values():
        if not isinstance(v, dict):
            continue
        kind = icon_kind(str(v.get("icon") or ""))
        if not kind:
            continue
        name = strip_html(str(v.get("name") or ""))
        m[name] = kind
        bare = re.sub(r"^普通攻击[·・]", "", name)
        m[bare] = kind
    return m


def parse_skill_add_from_avatar(avatar: Dict[str, Any]) -> Optional[List[str]]:
    name_map = build_talent_name_map(avatar)
    cons = avatar.get("constellation") or {}
    result: List[str] = []
    for idx in ("2", "4"):  # C3, C5
        c = cons.get(idx) or cons.get(int(idx))
        if not isinstance(c, dict):
            return None
        desc = strip_html(str(c.get("description") or ""))
        kind: Optional[str] = None
        # 优先显式 元素战技/爆发/普攻
        cands: List[Tuple[int, str]] = []
        for kw, k in (("元素战技", "E"), ("元素爆发", "Q"), ("普通攻击", "A")):
            m = re.search(rf"{kw}.{{0,40}}?技能等级[提高升]{{1,2}}\s*3", desc)
            if m:
                cands.append((m.start(), k))
        if cands:
            cands.sort()
            kind = cands[0][1]
        else:
            m = re.search(r"([^。\n]+?)的技能等级[提高升]{1,2}\s*3\s*级", desc)
            if m:
                skill = m.group(1).strip()
                skill = re.sub(r"^元素战技|^元素爆发|^普通攻击", "", skill).strip()
                skill = skill.strip("：: ")
                if skill in name_map:
                    kind = name_map[skill]
                else:
                    for n, k in name_map.items():
                        if skill in n or n in skill:
                            kind = k
                            break
        if not kind:
            return None
        result.append(kind)
    return result if len(result) == 2 else None


def update_skill_add(
    avatar_ids: Sequence[str],
    vh: str,
    dry_run: bool,
    fix_known: bool = True,
) -> None:
    path = EFFECT_PATH / "skill_add.json"
    data: Dict[str, List[str]] = load_json(path)
    changed = 0

    for aid in avatar_ids:
        if "10000005" in str(aid) or "10000007" in str(aid):
            # 旅行者按元素变体，默认 E/Q
            continue
        try:
            avatar = fetch_avatar(str(aid), vh)
        except Exception as e:  # noqa: BLE001
            log(f"skill_add 拉角色失败 {aid}: {e}")
            continue
        name = str(avatar.get("name") or aid)
        parsed = parse_skill_add_from_avatar(avatar)
        if not parsed:
            log(f"skill_add 解析失败: {name} ({aid})")
            continue
        old = data.get(name)
        if old != parsed:
            log(f"skill_add {name}: {old} -> {parsed}")
            data[name] = parsed
            changed += 1
        else:
            log(f"skill_add 已是最新: {name} = {parsed}")

    if fix_known:
        # 与天赋文案对齐的已知纠错
        fixes = {
            "流浪者": ["Q", "E"],
            "茜特菈莉": ["E", "Q"],
        }
        for n, v in fixes.items():
            if n in data and data[n] != v:
                log(f"skill_add 纠错 {n}: {data[n]} -> {v}")
                data[n] = v
                changed += 1

    if changed or not dry_run:
        save_json(path, data, dry_run)
    log(f"skill_add 变更 {changed} 条")


# ---------- 简单 DSL 启发式 ----------


def extract_simple_buffs(text: str) -> List[str]:
    """
    从中文描述提取可直接落地的简单属性 buff。
    策略：一律取最高——「最低A%、最高B%」取 B；「至多叠加N层」按 N 层满层计。
    """
    plain = strip_html(text)
    buffs: List[str] = []

    # 最低 x%、最高 y% 的攻击力加成 → 只取最高
    for m in re.finditer(
        r"最低\s*(\d+(?:\.\d+)?)\s*%\s*[、,，]?\s*最高\s*(\d+(?:\.\d+)?)\s*%[^。；]{0,20}攻击力",
        plain,
    ):
        buffs.append(f"addAtk+{m.group(2)}")

    # 至多叠加 N 层 + 每层属性
    stack_m = re.search(r"至多叠加\s*(\d+)\s*层", plain)
    stacks = int(stack_m.group(1)) if stack_m else 1

    for pat, attr, _is_pct in STAT_CN_TO_DSL:
        m = re.search(pat, plain)
        if not m:
            continue
        val = m.group(1)
        if val.endswith(".0"):
            val = val[:-2]
        # 若存在叠层且该句在叠层描述附近，乘层数（简单启发式）
        try:
            num = float(val)
        except ValueError:
            buffs.append(f"{attr}+{val}")
            continue
        if stacks > 1 and attr in {"addAtk", "addHp", "addDef", "critRate", "critDmg", "dmgBonus"}:
            # 仅当「提升X%…至多叠加」同段时乘层
            window = plain[max(0, (m.start() or 0) - 20) : (m.end() or 0) + 40]
            if "叠加" in window or "层" in window:
                num = num * stacks
        if abs(num - round(num)) < 1e-9:
            val_s = str(int(round(num)))
        else:
            val_s = f"{num:.4f}".rstrip("0").rstrip(".")
        buffs.append(f"{attr}+{val_s}")

    seen = set()
    out = []
    for b in buffs:
        if b not in seen:
            seen.add(b)
            out.append(b)
    return out


def detect_condition_prefix(text: str) -> str:
    plain = strip_html(text)
    for pat, pref in COND_PREFIX:
        if re.search(pat, plain):
            return pref
    return ""


def scale_buff_line(line: str, ratio: float) -> str:
    """按精炼比例缩放 buff 数值（仅简单 +数字）。"""
    parts = []
    for seg in line.split(";"):
        if "+" not in seg:
            parts.append(seg)
            continue
        attr, val = seg.split("+", 1)
        try:
            num = float(val)
            scaled = num * ratio
            if abs(scaled - round(scaled)) < 1e-6:
                parts.append(f"{attr}+{int(round(scaled))}")
            else:
                parts.append(f"{attr}+{scaled:.2f}".rstrip("0").rstrip("."))
        except ValueError:
            parts.append(seg)
    return ";".join(parts)


def build_refine_effects(upgrade_texts: List[str]) -> Dict[str, str]:
    """
    upgrade_texts: R1..R5 原文。
    对每个精炼提取简单 buff；无法提取则空串。
    """
    result = {"1": "", "2": "", "3": "", "4": "", "5": ""}
    parsed: List[List[str]] = []
    for t in upgrade_texts:
        parsed.append(extract_simple_buffs(t))

    # 若 R1 无结果则全空
    if not any(parsed):
        return result

    # 若每档都能提出相同 attr 集合，按档写入
    for i, buffs in enumerate(parsed):
        if not buffs:
            continue
        pref = detect_condition_prefix(upgrade_texts[i])
        line = ";".join(buffs)
        if pref:
            # 条件 buff 前缀加在整段
            line = ";".join(f"{pref}:{b}" if ":" not in b else b for b in buffs)
        result[str(i + 1)] = line

    # 若仅 R1 有值，用常见 1.0~1.x 比例估 R2-5（弱启发式，仅当其它档为空）
    if result["1"] and not any(result[str(i)] for i in range(2, 6)):
        # 尝试从各档文本提第一个百分比序列
        nums_per_refine: List[List[float]] = []
        for t in upgrade_texts:
            nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", strip_html(t))]
            nums_per_refine.append(nums)
        if all(len(n) == len(nums_per_refine[0]) and len(n) > 0 for n in nums_per_refine):
            # 重新按 R1 模板的 attr 顺序，用每档百分比替换
            r1_buffs = extract_simple_buffs(upgrade_texts[0])
            r1_nums = re.findall(r"(\d+(?:\.\d+)?)", ";".join(r1_buffs))
            if len(r1_nums) == len(nums_per_refine[0]):
                for ri, nums in enumerate(nums_per_refine):
                    buffs = []
                    for b, n in zip(r1_buffs, nums):
                        attr = b.split("+")[0]
                        val = str(int(n)) if float(n).is_integer() else str(n)
                        buffs.append(f"{attr}+{val}")
                    pref = detect_condition_prefix(upgrade_texts[ri])
                    if pref:
                        result[str(ri + 1)] = ";".join(f"{pref}:{b}" for b in buffs)
                    else:
                        result[str(ri + 1)] = ";".join(buffs)
    return result


def classify_normal_vs_fight(text: str, line: str) -> Tuple[str, str]:
    """返回 (normal_line, fight_line)。无条件进 normal，有条件进 fight。"""
    if not line:
        return "", ""
    plain = strip_html(text)
    conditional = bool(
        re.search(
            r"后|时|每|命中|施放|使用|触发|处于|队伍中|造成伤害后|倒下",
            plain,
        )
    )
    # 若 line 已有 E:/Q: 前缀，进 fight
    if re.search(r"(^|;)[A-Z]{1,4}:", line) or conditional:
        return "", line
    return line, ""


# ---------- weapon_effect ----------


def update_weapon_effect(
    weapon_ids: Sequence[str],
    weapon_list: Dict[str, Any],
    vh: str,
    dry_run: bool,
    skip_skin: bool = True,
) -> None:
    path = EFFECT_PATH / "weapon_effect.json"
    data: Dict[str, Any] = load_json(path)
    added = 0
    filled = 0

    for wid in weapon_ids:
        info = find_item(weapon_list, str(wid))
        try:
            detail = fetch_weapon(str(wid), vh)
        except Exception as e:  # noqa: BLE001
            log(f"weapon 详情失败 {wid}: {e}")
            detail = info or {}
        if detail.get("isWeaponSkin") or (info or {}).get("isWeaponSkin"):
            if skip_skin:
                log(f"跳过武器皮肤 {detail.get('name', wid)}")
                continue
        name = str(detail.get("name") or (info or {}).get("name") or wid)
        # 仅当全部精炼槽位都已有内容时跳过；空壳允许重试启发式
        if name in data:
            has_any = any(
                data[name].get("normal", {}).get("normal_effect", {}).get(str(i))
                or data[name].get("fight", {}).get("fight_effect", {}).get(str(i))
                for i in range(1, 6)
            )
            if has_any:
                log(f"weapon_effect 已有非空: {name}")
                continue

        # 解析 affix
        affix = detail.get("affix") or {}
        upgrade_texts: List[str] = []
        if isinstance(affix, dict) and affix:
            first = next(iter(affix.values()))
            up = (first or {}).get("upgrade") or {}
            for i in range(5):
                upgrade_texts.append(str(up.get(str(i), up.get(i, ""))))
        while len(upgrade_texts) < 5:
            upgrade_texts.append(upgrade_texts[-1] if upgrade_texts else "")

        effects = build_refine_effects(upgrade_texts)
        entry = deepcopy(EMPTY_WEAPON_EFFECT)
        # 分类 normal / fight
        for i in range(1, 6):
            key = str(i)
            nline, fline = classify_normal_vs_fight(upgrade_texts[i - 1], effects[key])
            # 若 classify 拆开，用拆后的；否则全进原桶
            if nline or fline:
                entry["normal"]["normal_effect"][key] = nline
                entry["fight"]["fight_effect"][key] = fline
            else:
                entry["normal"]["normal_effect"][key] = effects[key]

        # 粗略 time：文案里「持续Xs」
        m = re.search(r"持续\s*(\d+)\s*秒", strip_html(upgrade_texts[0]))
        if m:
            entry["fight"]["time"] = int(m.group(1))

        is_new = name not in data
        data[name] = entry
        added += 1 if is_new else 0
        if any(effects.values()):
            filled += 1
            log(
                f"weapon_effect {'新增' if is_new else '更新'} {name}: "
                f"normal={entry['normal']['normal_effect']['1']!r} "
                f"fight={entry['fight']['fight_effect']['1']!r}"
            )
            log(f"  原文R1: {strip_html(upgrade_texts[0])[:120]}")
        else:
            log(f"weapon_effect scaffold 空壳 {name} (需人工填 DSL)")
            log(f"  原文R1: {strip_html(upgrade_texts[0])[:160]}")

    save_json(path, data, dry_run)
    log(f"weapon_effect 处理 {added} 条(含更新), 启发式填入 {filled}")


# ---------- artifact_effect ----------


def update_artifact_effect(reliq_ids: Sequence[str], vh: str, dry_run: bool) -> None:
    path = EFFECT_PATH / "artifact_effect.json"
    data: Dict[str, Any] = load_json(path)
    added = 0

    for rid in reliq_ids:
        try:
            detail = fetch_reliquary(str(rid), vh)
        except Exception as e:  # noqa: BLE001
            log(f"reliquary 失败 {rid}: {e}")
            continue
        name = str(detail.get("name") or rid)
        affix_list = detail.get("affixList") or {}
        # affix keys typically ...0 = 2pc, ...1 = 4pc
        texts = list(affix_list.values()) if isinstance(affix_list, dict) else []
        text_2 = str(texts[0]) if len(texts) > 0 else ""
        text_4 = str(texts[1]) if len(texts) > 1 else ""

        entry = deepcopy(EMPTY_ARTIFACT_EFFECT)
        b2 = extract_simple_buffs(text_2)
        b4 = extract_simple_buffs(text_4)
        n2, f2 = classify_normal_vs_fight(text_2, ";".join(b2))
        n4, f4 = classify_normal_vs_fight(text_4, ";".join(b4))
        entry["normal_effect"]["2"] = n2
        entry["normal_effect"]["4"] = n4
        entry["fight_effect"]["2"] = f2
        entry["fight_effect"]["4"] = f4
        # group 默认跟 fight 的可共享部分（弱默认：仅非条件 4 件伤害类放到 group 需人工）
        entry["group_effect"]["2"] = ""
        entry["group_effect"]["4"] = ""

        existed = name in data
        # 已有非空则跳过覆盖
        if existed:
            old = data[name]
            has_val = any(
                old.get(k, {}).get(s) for k in ("normal_effect", "fight_effect", "group_effect") for s in ("2", "4")
            )
            if has_val:
                log(f"artifact_effect 已有非空: {name}")
                continue

        data[name] = entry
        added += 1
        log(f"artifact_effect {'新增' if not existed else '填充'} {name}: 2n={n2!r} 2f={f2!r} 4n={n4!r} 4f={f4!r}")
        log(f"  2件: {strip_html(text_2)[:100]}")
        log(f"  4件: {strip_html(text_4)[:120]}")

    save_json(path, data, dry_run)
    log(f"artifact_effect 新增/填充 {added}")


# ---------- char_effect / value_attr / dmg_map scaffolds ----------


def update_char_effect(names: Sequence[str], dry_run: bool) -> None:
    path = EFFECT_PATH / "char_effect.json"
    data: Dict[str, Any] = load_json(path)
    n = 0
    for name in names:
        if name in data:
            log(f"char_effect 已存在: {name}")
            continue
        data[name] = deepcopy(EMPTY_CHAR_EFFECT)
        log(f"char_effect scaffold: {name}")
        n += 1
    save_json(path, data, dry_run)
    log(f"char_effect 新增 {n}")


def update_value_attr(avatars: Sequence[Dict[str, Any]], dry_run: bool) -> None:
    path = EFFECT_PATH / "value_attr.json"
    data: Dict[str, Any] = load_json(path)
    n = 0
    for av in avatars:
        name = str(av.get("name") or "")
        if not name or name in data:
            if name in data:
                log(f"value_attr 已存在: {name}")
            continue
        sp = str(av.get("specialProp") or "")
        attrs = list(SPECIAL_TO_VALUE_ATTR.get(sp, ["攻击力", "暴击率", "暴击伤害"]))
        data[name] = attrs
        log(f"value_attr scaffold {name}: {attrs} (from {sp or 'default'})")
        n += 1
    save_json(path, data, dry_run)
    log(f"value_attr 新增 {n}")


def update_dmg_map(names: Sequence[str], dry_run: bool) -> None:
    path = EFFECT_PATH / "dmg_map.json"
    data: Dict[str, Any] = load_json(path)
    n = 0
    for name in names:
        if name in data:
            log(f"dmg_map 已存在: {name}")
            continue
        data[name] = []
        log(f"dmg_map scaffold 空参考面板: {name}")
        n += 1
    save_json(path, data, dry_run)
    log(f"dmg_map 新增 {n}")


# ---------- char_action ----------


def from_type_to_value(value_type: str, para: float) -> str:
    if value_type == "F1P":
        return "%.1f%%" % (para * 100)
    if value_type == "F2P":
        return "%.2f%%" % (para * 100)
    if value_type == "F1":
        return "%.1f" % para
    if value_type == "F2":
        return "%.2f" % para
    if value_type == "P":
        return str(round(para * 100)) + "%"
    if value_type == "I":
        return "%.2f" % para
    return str(para)


def talent_to_combat(avatar: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    talent_data = avatar.get("talent") or {}
    if not talent_data:
        return None
    # combat slots: A / E / Q by icon
    combat_keys: List[str] = []
    for k, v in talent_data.items():
        if not isinstance(v, dict):
            continue
        kind = icon_kind(str(v.get("icon") or ""))
        if kind in {"A", "E", "Q"} and kind != "A" or (kind == "A" and str(v.get("icon", "")).startswith("Skill_A")):
            # Skill_S may include non-main (dash); keep first Skill_S as E, Skill_E as Q, Skill_A as A
            combat_keys.append(str(k))

    # better: pick by kind uniquely
    by_kind: Dict[str, str] = {}
    for k, v in talent_data.items():
        if not isinstance(v, dict):
            continue
        icon = str(v.get("icon") or "")
        if icon.startswith("Skill_A") and "A" not in by_kind:
            by_kind["A"] = str(k)
        elif icon.startswith("Skill_S") and "E" not in by_kind:
            by_kind["E"] = str(k)
        elif icon.startswith("Skill_E") and "Q" not in by_kind:
            by_kind["Q"] = str(k)

    result: Dict[str, Any] = {}
    for index, kind in enumerate(["A", "E", "Q"], start=1):
        key = by_kind.get(kind)
        if not key or key not in talent_data:
            continue
        t = talent_data[key]
        promote = t.get("promote") or {}
        if "1" not in promote and 1 not in promote:
            continue
        p1 = promote.get("1") or promote.get(1) or {}
        labels = [x for x in (p1.get("description") or []) if x and isinstance(x, str)]
        label_str = "".join(labels)
        para_list = re.findall(r"{(param[0-9]+):", label_str)
        # map param order from labels appearance
        ordered_params = []
        for p in para_list:
            if p not in ordered_params:
                ordered_params.append(p)

        parameters: Dict[str, List[float]] = {}
        for ig, para in enumerate(ordered_params):
            parameters[para] = []
            for level in sorted(promote.keys(), key=lambda x: int(x)):
                params = (promote[level] or {}).get("params") or []
                if ig < len(params):
                    parameters[para].append(params[ig])
                else:
                    parameters[para].append(0.0)

        # build action entries
        for label in labels:
            if "|" not in label:
                continue
            label_name = label.split("|")[0]
            label_split = label.split("|")[-1]
            label_plus = 1
            if "*" in label_split:
                m = re.findall(r"[0-9]+", label_split.split("*")[-1])
                if m:
                    label_plus = int(m[0])
            laber_kanji = "".join(re.findall(r"[\u4e00-\u9fa5]+", label_split)).replace("每秒", "")
            label_kanji = "攻击力"
            for typ in LABEL_TYPE_LIST:
                if typ in laber_kanji:
                    label_kanji = typ
                    break
            # map type display
            type_map = {
                "A": "攻击力",
                "attack": "攻击力",
                "hp": "生命值",
                "defense": "防御力",
                "ce": "元素充能效率",
                "critrate": "暴击率",
                "critDmg": "暴击伤害",
                "em": "元素精通",
                "B": "攻击力",
                "C": "攻击力",
            }
            type_cn = type_map.get(LABEL_TYPE_LIST.get(label_kanji, "attack"), "攻击力")
            if label_kanji in ("生命值", "防御", "元素精通", "暴击率", "暴击伤害", "充能效率"):
                type_cn = {
                    "生命值": "生命值",
                    "防御": "防御力",
                    "元素精通": "元素精通",
                    "暴击率": "暴击率",
                    "暴击伤害": "暴击伤害",
                    "充能效率": "元素充能效率",
                }.get(label_kanji, "攻击力")

            label_attr = re.findall(r"{[a-zA-Z0-9]+:[a-zA-Z0-9]+}", label_split)
            if not label_attr:
                continue
            # skip pure stamina/cd seconds without damage
            if "体力" in label_name or "冷却" in label_name or "持续时间" in label_name:
                if "伤害" not in label_name:
                    continue
            values: List[str] = []
            # use first param series; multi-param join later if needed
            k0 = label_attr[0].replace("{", "").replace("}", "")
            vtype = k0.split(":")[-1]
            pkey = k0.split(":")[0]
            series = parameters.get(pkey) or []
            if not series:
                continue
            # multi param like a+b
            if len(label_attr) >= 2 and ("+" in label_split or "低空/高空" in label):
                # for 低空/高空 use second as 高空
                if "低空/高空" in label:
                    k1 = label_attr[1].replace("{", "").replace("}", "")
                    vtype = k1.split(":")[-1]
                    pkey = k1.split(":")[0]
                    series = parameters.get(pkey) or series
                else:
                    # sum first two percent series into display of first only for scaffold
                    pass
            values = [from_type_to_value(vtype, p) for p in series]
            full_name = f"{INDEX_MAP[index]}{label_name}"
            result[full_name] = {
                "name": full_name,
                "type": type_cn,
                "plus": label_plus,
                "value": values,
            }
    return result or None


def update_char_action(avatar_ids: Sequence[str], vh: str, dry_run: bool) -> None:
    path = EFFECT_PATH / "char_action.json"
    data: Dict[str, Any] = load_json(path)
    n = 0
    for aid in avatar_ids:
        if "10000005" in str(aid) or "10000007" in str(aid):
            continue
        try:
            avatar = fetch_avatar(str(aid), vh)
        except Exception as e:  # noqa: BLE001
            log(f"char_action 拉角色失败 {aid}: {e}")
            continue
        name = str(avatar.get("name") or aid)
        if name in data and data[name]:
            log(f"char_action 已存在: {name} ({len(data[name])} skills)")
            continue
        actions = talent_to_combat(avatar)
        if not actions:
            log(f"char_action 生成失败: {name}")
            continue
        data[name] = actions
        n += 1
        log(f"char_action 生成 {name}: {list(actions.keys())[:8]}... ({len(actions)} entries)")
    save_json(path, data, dry_run)
    log(f"char_action 新增 {n}")


# ---------- main ----------


def resolve_avatar_payloads(
    avatar_ids: Sequence[str],
    avatar_list: Dict[str, Any],
    vh: str,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for aid in avatar_ids:
        if "10000005" in str(aid) or "10000007" in str(aid):
            continue
        info = find_item(avatar_list, str(aid))
        try:
            detail = fetch_avatar(str(aid), vh)
            out.append(detail)
        except Exception as e:  # noqa: BLE001
            log(f"角色详情失败 {aid}: {e}")
            if info:
                out.append(info)
    return out


def main(
    version: str = DEFAULT_VERSION,
    vh: str = DEFAULT_VH,
    dry_run: bool = False,
    only: Optional[Sequence[str]] = None,
    skip_skin: bool = True,
) -> None:
    REPORT.clear()
    targets = set(only) if only else set(ALL_TARGETS)
    unknown = targets - set(ALL_TARGETS)
    if unknown:
        raise SystemExit(f"unknown targets: {unknown}")

    changelog = get_changelog(vh)
    key, entry = pick_entry(changelog, version)
    ver = entry.get("version", key)
    items = entry.get("items") or {}
    avatar_ids = [str(x) for x in items.get("avatar") or []]
    weapon_ids = [str(x) for x in items.get("weapon") or []]
    reliq_ids = [str(x) for x in items.get("reliquary") or []]
    log(f"版本 {ver} (key={key})")
    log(f"  avatar={avatar_ids}")
    log(f"  weapon={weapon_ids}")
    log(f"  reliquary={reliq_ids}")

    avatar_list = load_local_list("charList")
    weapon_list = load_local_list("weaponList")
    avatars = resolve_avatar_payloads(avatar_ids, avatar_list, vh)
    names = [str(a.get("name")) for a in avatars if a.get("name")]

    if "skill_add" in targets:
        log("\n=== skill_add ===")
        update_skill_add(avatar_ids, vh, dry_run)

    if "weapon_effect" in targets:
        log("\n=== weapon_effect ===")
        update_weapon_effect(weapon_ids, weapon_list, vh, dry_run, skip_skin=skip_skin)

    if "artifact_effect" in targets:
        log("\n=== artifact_effect ===")
        update_artifact_effect(reliq_ids, vh, dry_run)

    if "char_effect" in targets:
        log("\n=== char_effect ===")
        update_char_effect(names, dry_run)

    if "value_attr" in targets:
        log("\n=== value_attr ===")
        update_value_attr(avatars, dry_run)

    if "char_action" in targets:
        log("\n=== char_action ===")
        update_char_action(avatar_ids, vh, dry_run)

    if "dmg_map" in targets:
        log("\n=== dmg_map ===")
        update_dmg_map(names, dry_run)

    # 报告
    report_path = EFFECT_PATH / f"_update_report_{ver}.md"
    body = "# effect 更新报告\n\n" + "\n".join(f"- {line}" for line in REPORT) + "\n"
    if not dry_run:
        report_path.write_text(body, encoding="utf-8")
        log(f"\n报告: {report_path}")
    else:
        log("\n[dry-run] 不写报告文件")
    log("完成")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="更新 genshinuid_enka/effect 配置")
    p.add_argument("-v", "--version", default=DEFAULT_VERSION)
    p.add_argument("--vh", default=DEFAULT_VH)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--only",
        default="",
        help=f"逗号分隔子集: {','.join(ALL_TARGETS)}",
    )
    p.add_argument("--include-skin", action="store_true", help="武器皮肤也 scaffold")
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    only = [x.strip() for x in args.only.split(",") if x.strip()] or None
    main(
        version=args.version,
        vh=args.vh,
        dry_run=args.dry_run,
        only=only,
        skip_skin=not args.include_skin,
    )
