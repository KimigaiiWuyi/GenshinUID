"""小助手深渊 / 危战使用率：解析、滞后判断、缓存。"""

from __future__ import annotations

import re
import json
import hashlib
from typing import Literal, TypedDict
from pathlib import Path

import aiofiles

from ..utils.resource.RESOURCE_PATH import USAGE_RANK_PATH

UsageKind = Literal["abyss", "hard"]
SHOW_CHAR_SLOTS = 24
SHOW_TEAM_SLOTS = 8
AI_CHAR = 12
AI_TEAM = 4
_KEEP_CHAR = 40
_KEEP_TEAM = 16
_DAY = re.compile(r"(20\d{2}-\d{2}-\d{2})")
_VER = re.compile(r"(\d+)\.(\d+)")


class UsageChar(TypedDict):
    name: str
    star: int
    avatar: str
    use_rate: float
    use_rate_change: float
    side_rate: float


class UsageMember(TypedDict):
    name: str
    star: int
    avatar: str


class UsageTeam(TypedDict):
    members: list[UsageMember]
    use_rate: float
    side_pct: int
    time: float


class UsageSide(TypedDict):
    name: str
    characters: list[UsageChar]
    teams: list[UsageTeam]


class UsageSnapshot(TypedDict):
    kind: str
    title: str
    version_label: str
    history_id: int
    last_update: str
    window_text: str
    window_date: str
    sample: str
    tips: str
    tips2: str
    sides: list[UsageSide]


class StoredUsage(TypedDict):
    snapshot: UsageSnapshot
    monster_brief: str
    fetched_at: str


class _SideKey(TypedDict):
    name: str
    pct: str
    num: str


class _CharStat(TypedDict):
    name: str
    star: int
    avatar: str
    use_rate: float
    use_rate_change: float


class _RawTeam(TypedDict):
    members: list[UsageMember]
    use_rate: float
    time: float
    weights: dict[str, float]
    pcts: dict[str, int]


_ABYSS_SIDES: tuple[_SideKey, ...] = (
    {"name": "上半", "pct": "up_use", "num": "up_use_num"},
    {"name": "下半", "pct": "down_use", "num": "down_use_num"},
)
_HARD_SIDES: tuple[_SideKey, ...] = (
    {"name": "上路", "pct": "up_use", "num": "up_use_num"},
    {"name": "中路", "pct": "mid_use", "num": "mid_use_num"},
    {"name": "下路", "pct": "down_use", "num": "down_use_num"},
)


def _as_float(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    if not isinstance(value, str):
        return 0.0
    text = value.strip().rstrip("%")
    if text.startswith("-"):
        body = text[1:]
        sign = -1.0
    else:
        body = text
        sign = 1.0
    if body.count(".") > 1 or body in {"", "."} or not body.replace(".", "").isdigit():
        return 0.0
    return sign * float(body)


def _text(raw: dict[str, object], key: str) -> str:
    if key not in raw:
        return ""
    value = raw[key]
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return ""


def pct(value: float) -> str:
    rounded = round(value, 1)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.1f}"


def version_pair(text: str) -> tuple[int, int] | None:
    found = _VER.search(text)
    if found is None:
        return None
    return int(found.group(1)), int(found.group(2))


def alignment(window_date: str, current_open: str, usage_label: str, game_version: str) -> tuple[str, bool]:
    # 日期对得上就不是滞后：插件版本号可能先于使用率接口更新。
    if window_date and current_open:
        if window_date == current_open:
            return "与当期日程对齐", False
        if current_open > window_date:
            return f"滞后：使用率仍是 {window_date} 的样本，当期从 {current_open} 开始", True
        return f"样本窗口 {window_date} 晚于已缓存日程 {current_open}", False
    usage = version_pair(usage_label)
    game = version_pair(game_version)
    if usage is not None and game is not None and usage < game:
        return f"滞后：使用率版本 {usage_label}，游戏版本 {game_version}，没有日程日期可对照", True
    if not current_open:
        return "未能对照当期日程", False
    return "未能对照当期日程", False


def _history_id(raw: dict[str, object]) -> int:
    if "history_list" not in raw or not isinstance(raw["history_list"], list):
        return 0
    for item in raw["history_list"]:
        if not isinstance(item, dict):
            continue
        title = item["title"] if "title" in item and isinstance(item["title"], str) else ""
        if "11层" in title:
            continue
        if "value" not in item:
            continue
        value = item["value"]
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return 0


def _window_date(text: str) -> str:
    found = _DAY.search(text)
    if found is None:
        return ""
    return found.group(1)


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    rows: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _indexes(blocks: list[object]) -> tuple[dict[str, _CharStat], dict[str, str]]:
    stats: dict[str, _CharStat] = {}
    by_url: dict[str, str] = {}
    sources: list[dict[str, object]] = []
    # 平铺列表带较上期变化，必须先于分段榜写入。
    if len(blocks) > 1:
        sources.extend(_dict_list(blocks[1]))
    if blocks:
        for rank in _dict_list(blocks[0]):
            if "list" in rank:
                sources.extend(_dict_list(rank["list"]))
    for item in sources:
        name = item["name"] if "name" in item and isinstance(item["name"], str) else ""
        avatar = item["avatar"] if "avatar" in item and isinstance(item["avatar"], str) else ""
        if not name:
            continue
        if avatar and avatar not in by_url:
            by_url[avatar] = name
        if name in stats:
            continue
        star = int(_as_float(item["star"])) if "star" in item else 4
        stats[name] = _CharStat(
            name=name,
            star=star if star else 4,
            avatar=avatar,
            use_rate=_as_float(item["use_rate"]) if "use_rate" in item else 0.0,
            use_rate_change=_as_float(item["use_rate_change"]) if "use_rate_change" in item else 0.0,
        )
    return stats, by_url


def _member_name(avatar: str, by_url: dict[str, str]) -> str:
    if avatar in by_url:
        return by_url[avatar]
    tail = avatar.rsplit("/", 1)[-1]
    if not tail:
        return "未知"
    for url, name in by_url.items():
        if url.rsplit("/", 1)[-1] == tail:
            return name
    return "未知"


def _parse_teams(block: object, keys: tuple[_SideKey, ...], by_url: dict[str, str]) -> list[_RawTeam]:
    teams: list[_RawTeam] = []
    for item in _dict_list(block):
        roles = _dict_list(item["role"]) if "role" in item else []
        members: list[UsageMember] = []
        for role in roles:
            avatar = role["avatar"] if "avatar" in role and isinstance(role["avatar"], str) else ""
            star = int(_as_float(role["star"])) if "star" in role else 4
            members.append(UsageMember(name=_member_name(avatar, by_url), star=star if star else 4, avatar=avatar))
        weights: dict[str, float] = {}
        pcts: dict[str, int] = {}
        for key in keys:
            num = _as_float(item[key["num"]]) if key["num"] in item else 0.0
            percent = _as_float(item[key["pct"]]) if key["pct"] in item else 0.0
            weights[key["name"]] = num if num > 0 else percent
            pcts[key["name"]] = int(round(percent))
        teams.append(
            _RawTeam(
                members=members,
                use_rate=_as_float(item["use_rate"]) if "use_rate" in item else 0.0,
                time=_as_float(item["time"]) if "time" in item else 0.0,
                weights=weights,
                pcts=pcts,
            )
        )
    return teams


def _primary(pcts: dict[str, int], order: list[str]) -> str:
    best = order[0]
    best_val = pcts[best] if best in pcts else 0
    for name in order[1:]:
        value = pcts[name] if name in pcts else 0
        if value > best_val:
            best = name
            best_val = value
    return best


def _build_sides(teams: list[_RawTeam], stats: dict[str, _CharStat], keys: tuple[_SideKey, ...]) -> list[UsageSide]:
    order = [key["name"] for key in keys]
    char_weight: dict[str, dict[str, float]] = {name: {} for name in order}
    totals: dict[str, float] = {name: 0.0 for name in order}
    grouped: dict[str, list[_RawTeam]] = {name: [] for name in order}
    for team in teams:
        for side, weight in team["weights"].items():
            if weight <= 0 or side not in totals:
                continue
            totals[side] += weight
            seen: set[str] = set()
            for member in team["members"]:
                if member["name"] == "未知" or member["name"] in seen:
                    continue
                seen.add(member["name"])
                bucket = char_weight[side]
                bucket[member["name"]] = (bucket[member["name"]] if member["name"] in bucket else 0.0) + weight
        side = _primary(team["pcts"], order)
        if team["pcts"][side] >= 50:
            grouped[side].append(team)
    sides: list[UsageSide] = []
    for side in order:
        ranked: list[UsageChar] = []
        total = totals[side]
        for name, weight in char_weight[side].items():
            stat = stats[name] if name in stats else None
            ranked.append(
                UsageChar(
                    name=name,
                    star=stat["star"] if stat is not None else 4,
                    avatar=stat["avatar"] if stat is not None else "",
                    use_rate=stat["use_rate"] if stat is not None else 0.0,
                    use_rate_change=stat["use_rate_change"] if stat is not None else 0.0,
                    side_rate=(weight / total * 100) if total else 0.0,
                )
            )
        ranked.sort(key=lambda item: item["side_rate"], reverse=True)
        picked = grouped[side]
        picked.sort(key=lambda item: item["use_rate"], reverse=True)
        team_rows = [
            UsageTeam(
                members=team["members"],
                use_rate=team["use_rate"],
                side_pct=team["pcts"][side] if side in team["pcts"] else 0,
                time=team["time"],
            )
            for team in picked[:_KEEP_TEAM]
        ]
        sides.append(UsageSide(name=side, characters=ranked[:_KEEP_CHAR], teams=team_rows))
    return sides


_HARD_SAMPLE = re.compile(r"难度5&6总有效样本(\d+)份，难度6有效样本(\d+)份")


def hard_difficulty_samples(tips: str) -> tuple[int, int] | None:
    found = _HARD_SAMPLE.search(tips)
    if found is None:
        return None
    total = int(found.group(1))
    level6 = int(found.group(2))
    if level6 > total:
        return None
    return total - level6, level6


def parse_usage(raw: object, kind: UsageKind) -> UsageSnapshot | str:
    if not isinstance(raw, dict):
        return "使用率数据不是对象。"
    if "result" not in raw or not isinstance(raw["result"], list) or len(raw["result"]) < 4:
        return "使用率结果不完整。"
    blocks: list[object] = list(raw["result"])
    stats, by_url = _indexes(blocks)
    keys = _ABYSS_SIDES if kind == "abyss" else _HARD_SIDES
    teams = _parse_teams(blocks[3], keys, by_url)
    label = _text(raw, "version").replace("当前版本：", "").strip()
    window = _text(raw, "update")
    sample_num = _as_float(raw["top_own"]) if "top_own" in raw else 0.0
    return UsageSnapshot(
        kind=kind,
        title=_text(raw, "title"),
        version_label=label,
        history_id=_history_id(raw),
        last_update=_text(raw, "last_update"),
        window_text=window,
        window_date=_window_date(window),
        sample=str(int(sample_num)) if sample_num else "",
        tips=_text(raw, "tips"),
        tips2=_text(raw, "tips2"),
        sides=_build_sides(teams, stats, keys),
    )


def visible_characters(chars: list[UsageChar]) -> list[UsageChar]:
    return chars[:SHOW_CHAR_SLOTS]


def _change(value: float) -> str:
    if value > 0:
        return f"较上期+{pct(value)}%"
    if value < 0:
        return f"较上期{pct(value)}%"
    return "较上期持平"


def _fmt_char(char: UsageChar) -> str:
    return (
        f"{char['name']} 本侧{pct(char['side_rate'])}% "
        f"使用率{pct(char['use_rate'])}%（{_change(char['use_rate_change'])}）"
    )


def _fmt_team(team: UsageTeam) -> str:
    names = "/".join(member["name"] for member in team["members"])
    clock = f" 均时{pct(team['time'])}s" if team["time"] > 0 else ""
    return f"{names} 使用率{pct(team['use_rate'])}% 本侧{team['side_pct']}%{clock}"


def usage_ai_text(
    snapshot: UsageSnapshot,
    align: str,
    lagged: bool,
    current_monsters: str,
    own_monsters: str,
    history: list[str],
    stale_note: str,
) -> str:
    title = "深渊使用率" if snapshot["kind"] == "abyss" else "危战使用率"
    lines = [
        f"【{title}】{snapshot['version_label'] or snapshot['title']}",
        f"状态：{align}",
        f"样本更新：{snapshot['last_update'] or '未知'}",
        f"统计窗口：{snapshot['window_text'] or '未知'}",
        f"有效样本：{snapshot['sample'] or '未知'}",
        "使用率不是开期当天更新，可能晚数日甚至跨版本。状态写滞后时，下面的角色和队伍是旧期样本，不能直接当当期配队。",
    ]
    if stale_note:
        lines.append(stale_note)
    if snapshot["tips"]:
        lines.append(snapshot["tips"])
    for side in snapshot["sides"]:
        chars = "；".join(_fmt_char(char) for char in visible_characters(side["characters"])[:AI_CHAR]) or "无"
        teams = "；".join(_fmt_team(team) for team in side["teams"][:AI_TEAM]) or "无"
        lines.append(f"{side['name']}角色：{chars}")
        lines.append(f"{side['name']}队伍：{teams}")
    if lagged:
        lines.append("当期怪物（不要用上面的旧样本顶替）：")
        lines.append(current_monsters or "当期怪物没取到。配队改看深渊信息或危战信息。")
        lines.append("本样本对应的怪物（旧期，用来和当期对照）：")
        lines.append(own_monsters or "保存样本时没有怪物缓存。")
    else:
        lines.append("当期怪物：")
        lines.append(current_monsters or own_monsters or "当期怪物没取到。配队改看深渊信息或危战信息。")
    if history:
        lines.append("已缓存样本（以后没有新使用率时，用怪物去对相近的一期）：")
        lines.extend(history)
    lines.append("配队只从用户箱子里挑。使用率高但箱子没有的写成缺口。深渊上下半、危战三路都不要重复同一个角色。")
    return "\n".join(lines)


def _file_name(snapshot: UsageSnapshot) -> str:
    if snapshot["history_id"] > 0:
        return f"{snapshot['kind']}_{snapshot['history_id']}.json"
    digest = hashlib.sha256(snapshot["version_label"].encode()).hexdigest()[:8]
    return f"{snapshot['kind']}_{digest}.json"


def _char_from(value: object) -> UsageChar | None:
    if not isinstance(value, dict) or "name" not in value or not isinstance(value["name"], str):
        return None
    avatar = value["avatar"] if "avatar" in value and isinstance(value["avatar"], str) else ""
    return UsageChar(
        name=value["name"],
        star=int(_as_float(value["star"])) if "star" in value else 4,
        avatar=avatar,
        use_rate=_as_float(value["use_rate"]) if "use_rate" in value else 0.0,
        use_rate_change=_as_float(value["use_rate_change"]) if "use_rate_change" in value else 0.0,
        side_rate=_as_float(value["side_rate"]) if "side_rate" in value else 0.0,
    )


def _team_from(value: object) -> UsageTeam | None:
    if not isinstance(value, dict) or "members" not in value or not isinstance(value["members"], list):
        return None
    members: list[UsageMember] = []
    for item in value["members"]:
        if not isinstance(item, dict) or "name" not in item or not isinstance(item["name"], str):
            continue
        avatar = item["avatar"] if "avatar" in item and isinstance(item["avatar"], str) else ""
        members.append(
            UsageMember(
                name=item["name"],
                star=int(_as_float(item["star"])) if "star" in item else 4,
                avatar=avatar,
            )
        )
    if not members:
        return None
    return UsageTeam(
        members=members,
        use_rate=_as_float(value["use_rate"]) if "use_rate" in value else 0.0,
        side_pct=int(_as_float(value["side_pct"])) if "side_pct" in value else 0,
        time=_as_float(value["time"]) if "time" in value else 0.0,
    )


def _side_from(value: object) -> UsageSide | None:
    if not isinstance(value, dict) or "name" not in value or not isinstance(value["name"], str):
        return None
    characters = (
        [char for item in value["characters"] if (char := _char_from(item)) is not None]
        if "characters" in value and isinstance(value["characters"], list)
        else []
    )
    teams = (
        [team for item in value["teams"] if (team := _team_from(item)) is not None]
        if "teams" in value and isinstance(value["teams"], list)
        else []
    )
    return UsageSide(name=value["name"], characters=characters, teams=teams)


def _snapshot_from(value: object) -> UsageSnapshot | None:
    if not isinstance(value, dict) or "kind" not in value or not isinstance(value["kind"], str):
        return None
    if "sides" not in value or not isinstance(value["sides"], list):
        return None
    sides = [side for item in value["sides"] if (side := _side_from(item)) is not None]
    if not sides:
        return None
    history = value["history_id"] if "history_id" in value else 0
    return UsageSnapshot(
        kind=value["kind"],
        title=_text(value, "title"),
        version_label=_text(value, "version_label"),
        history_id=int(history) if isinstance(history, int) and not isinstance(history, bool) else 0,
        last_update=_text(value, "last_update"),
        window_text=_text(value, "window_text"),
        window_date=_text(value, "window_date"),
        sample=_text(value, "sample"),
        tips=_text(value, "tips"),
        tips2=_text(value, "tips2"),
        sides=sides,
    )


def stored_from_object(raw: object) -> StoredUsage | None:
    if not isinstance(raw, dict) or "snapshot" not in raw:
        return None
    snapshot = _snapshot_from(raw["snapshot"])
    if snapshot is None:
        return None
    brief = raw["monster_brief"] if "monster_brief" in raw and isinstance(raw["monster_brief"], str) else ""
    fetched = raw["fetched_at"] if "fetched_at" in raw and isinstance(raw["fetched_at"], str) else ""
    return StoredUsage(snapshot=snapshot, monster_brief=brief, fetched_at=fetched)


async def save_usage(stored: StoredUsage, folder: Path | None = None) -> None:
    root = folder if folder is not None else USAGE_RANK_PATH
    root.mkdir(parents=True, exist_ok=True)
    path = root / _file_name(stored["snapshot"])
    if not stored["monster_brief"] and path.exists():
        previous = await load_usage_file(path)
        if previous is not None and previous["monster_brief"]:
            stored = StoredUsage(
                snapshot=stored["snapshot"],
                monster_brief=previous["monster_brief"],
                fetched_at=stored["fetched_at"],
            )
    async with aiofiles.open(path, "w", encoding="utf-8") as file:
        await file.write(json.dumps(stored, ensure_ascii=False))


async def load_usage_file(path: Path) -> StoredUsage | None:
    if not path.exists():
        return None
    async with aiofiles.open(path, encoding="utf-8") as file:
        text = await file.read()
    try:
        raw: object = json.loads(text)
    except json.JSONDecodeError:
        return None
    return stored_from_object(raw)


async def list_usage(kind: str, folder: Path | None = None) -> list[StoredUsage]:
    root = folder if folder is not None else USAGE_RANK_PATH
    if not root.exists():
        return []
    found: list[StoredUsage] = []
    for path in sorted(root.glob(f"{kind}_*.json")):
        stored = await load_usage_file(path)
        if stored is not None and stored["snapshot"]["kind"] == kind:
            found.append(stored)
    found.sort(key=lambda item: item["snapshot"]["history_id"], reverse=True)
    return found


def history_lines(records: list[StoredUsage], limit: int = 6) -> list[str]:
    lines: list[str] = []
    for stored in records[:limit]:
        snap = stored["snapshot"]
        brief = stored["monster_brief"].split("\n", 1)[0] if stored["monster_brief"] else "无怪物摘要"
        lines.append(f"- {snap['version_label'] or snap['title']} 窗口{snap['window_date'] or '未知'} {brief}")
    return lines
