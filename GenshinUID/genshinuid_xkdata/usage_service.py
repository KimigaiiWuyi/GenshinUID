"""拉取使用率、对照当期怪物，并出图。"""

from __future__ import annotations

import hashlib
import calendar
import datetime

from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error
from gsuid_core.ai_core.trigger_bridge import ai_return

from ..version import Genshin_version
from .html_usage import render_usage_image
from .usage_rank import (
    SHOW_TEAM_SLOTS,
    UsageKind,
    StoredUsage,
    UsageSnapshot,
    alignment,
    list_usage,
    save_usage,
    parse_usage,
    history_lines,
    usage_ai_text,
    visible_characters,
)
from ..utils.api.teyvat.api import AbyssRank_API, AbyssRank2_API
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.api.teyvat.request import teyvat_api
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, TEMP_PATH
from ..genshinuid_guide.html_endgame import _file_uri
from ..genshinuid_guide.lunaris_tower import TowerFloorView, plain_markup, fetch_tower_floor
from ..genshinuid_guide.lunaris_leyline import LeyView, fetch_leyline


def _ai_return_msg(text: str) -> None:
    try:
        ai_return(text)
    except Exception:
        return


def _day(text: str) -> datetime.date | None:
    parts = text.split("-")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    if month < 1 or month > 12:
        return None
    if day < 1 or day > calendar.monthrange(year, month)[1]:
        return None
    return datetime.date(year, month, day)


def tower_brief(view: TowerFloorView) -> str:
    lines = [f"日程{view['schedule_id']} {view['open_time'][:10]}~{view['close_time'][:10]} {view['buff_name']}"]
    desc = plain_markup(view["buff_desc"])
    if len(desc) > 160:
        desc = desc[:160] + "…"
    if desc:
        lines.append(desc)
    for chamber in view["chambers"]:
        upper = "、".join(mon["name"] for mon in chamber["upper"])
        lower = "、".join(mon["name"] for mon in chamber["lower"])
        lines.append(f"{chamber['name']} 上半：{upper} 下半：{lower}")
    return "\n".join(lines)


def ley_brief(view: LeyView) -> str:
    lines = [f"日程{view['schedule_id']} {view['begin'][:10]}~{view['end'][:10]} {view['name']}"]
    for lane in view["lanes"]:
        mechs = "、".join(mech["name"] for mech in lane["mechs"] if mech["name"])
        lines.append(f"{lane['name']} {mechs}")
    return "\n".join(lines)


async def period_context(kind: UsageKind, when: datetime.date | None) -> tuple[str, str]:
    if kind == "abyss":
        viewed, _error, _ranges = await fetch_tower_floor(12, when=when)
        if viewed is None:
            return "", ""
        return viewed["open_time"][:10], tower_brief(viewed)
    viewed, _error, _ranges = await fetch_leyline(when=when)
    if viewed is None:
        return "", ""
    return viewed["begin"][:10], ley_brief(viewed)


def _shown_avatars(snapshot: UsageSnapshot) -> dict[str, str]:
    found: dict[str, str] = {}
    for side in snapshot["sides"]:
        for char in visible_characters(side["characters"]):
            if char["name"] not in found:
                found[char["name"]] = char["avatar"]
        for team in side["teams"][:SHOW_TEAM_SLOTS]:
            for member in team["members"]:
                if member["name"] not in found:
                    found[member["name"]] = member["avatar"]
    return found


async def _face_uri(name: str, avatar: str) -> str:
    if name == "未知":
        return ""
    avatar_id = await name_to_avatar_id(name)
    if avatar_id:
        local = CHAR_PATH / f"{avatar_id}.png"
        if local.exists():
            return _file_uri(local)
    if not avatar:
        return ""
    digest = hashlib.sha256(avatar.encode()).hexdigest()[:16]
    suffix = ".jpg" if ".jpg" in avatar.lower() or ".jpeg" in avatar.lower() else ".png"
    dest = TEMP_PATH / f"usage_{digest}{suffix}"
    if not dest.exists():
        await download(avatar, 16, dest.name)
    if dest.exists() and dest.stat().st_size > 64:
        return _file_uri(dest)
    return ""


async def _faces(avatars: dict[str, str]) -> dict[str, str]:
    faces: dict[str, str] = {}
    for name, avatar in avatars.items():
        uri = await _face_uri(name, avatar)
        if uri:
            faces[name] = uri
    return faces


async def refresh_usage(kind: UsageKind) -> None:
    url = AbyssRank2_API if kind == "hard" else AbyssRank_API
    payload = await teyvat_api.get_rank_payload(url)
    if isinstance(payload, int):
        logger.warning(t("log.genshinuid.usage_refresh_fail", kind=kind))
        return
    parsed = parse_usage(payload, kind)
    if isinstance(parsed, str):
        logger.warning(t("log.genshinuid.usage_refresh_fail", kind=kind))
        return
    current_open, current_brief = await period_context(kind, None)
    own_brief = current_brief
    window = _day(parsed["window_date"])
    if window is not None and parsed["window_date"] != current_open:
        _open, brief = await period_context(kind, window)
        own_brief = brief
    fetched = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    await save_usage(StoredUsage(snapshot=parsed, monster_brief=own_brief, fetched_at=fetched))
    logger.info(t("log.genshinuid.usage_refresh", kind=kind))


async def build_usage_image(kind: UsageKind) -> str | bytes:
    url = AbyssRank2_API if kind == "hard" else AbyssRank_API
    payload = await teyvat_api.get_rank_payload(url)
    stale = ""
    own_monsters = ""
    if isinstance(payload, int):
        cached = await list_usage(kind)
        if not cached:
            text = get_error(payload)
            _ai_return_msg(text)
            return text
        snapshot = cached[0]["snapshot"]
        own_monsters = cached[0]["monster_brief"]
        stale = "接口这次没取到，下面是缓存样本。"
    else:
        parsed = parse_usage(payload, kind)
        if isinstance(parsed, str):
            _ai_return_msg(parsed)
            return parsed
        snapshot = parsed
    current_open, current_monsters = await period_context(kind, None)
    if not isinstance(payload, int):
        window = _day(snapshot["window_date"])
        if window is not None and snapshot["window_date"] != current_open:
            _open, own_monsters = await period_context(kind, window)
        else:
            own_monsters = current_monsters
        fetched = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        await save_usage(StoredUsage(snapshot=snapshot, monster_brief=own_monsters, fetched_at=fetched))
    align, lagged = alignment(snapshot["window_date"], current_open, snapshot["version_label"], Genshin_version)
    records = await list_usage(kind)
    _ai_return_msg(
        usage_ai_text(
            snapshot,
            align,
            lagged,
            current_monsters,
            own_monsters,
            history_lines(records),
            stale,
        )
    )
    return await render_usage_image(snapshot, align, lagged, await _faces(_shown_avatars(snapshot)))
