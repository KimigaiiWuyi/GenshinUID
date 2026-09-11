"""玩家目录里的 Akasha 右栏缓存：刷新时写入，查询只读盘、不打接口。"""

from __future__ import annotations

import json
import asyncio
from typing import TYPE_CHECKING, Mapping
from pathlib import Path
from urllib.parse import quote

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from .akasha_side import SIDE_RANK_MAX, SIDE_GAIN_LOADOUTS, match_calc_board, pick_loadout_ids
from ..utils.api.cv.api import (
    BUILD_LB_API,
    NEARBY_LB_API,
    DAMAGE_DIST_API,
    SUBSTAT_PRIORITY_API,
)
from ..utils.api.cv.models import (
    GlobalRankRow,
    BuildLeaderboardRow,
    SubstatPriorityBoard,
    DamageDistributionBoard,
)
from ..utils.api.cv.global_ranks import parse_global_ranks_payload
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.api.cv.substat_priority import (
    parse_substat_priority_payload,
    compute_substat_priority_boards,
)
from ..utils.api.cv.build_leaderboards import (
    list_visible_leaderboards,
    parse_build_leaderboards_payload,
)
from ..utils.api.cv.damage_distribution import (
    board_calculation_id,
    find_damage_distribution,
    list_visible_distributions,
    parse_damage_distribution_payload,
)

if TYPE_CHECKING:
    from ..utils.api.cv.request import _CvApi

AkashaDisk = tuple[
    list[SubstatPriorityBoard],
    list[BuildLeaderboardRow],
    list[DamageDistributionBoard],
    list[GlobalRankRow],
]


def akasha_char_path(uid: str, char_id: str, root: Path | None = None) -> Path:
    base = root if root is not None else PLAYER_PATH
    return base / uid / "akasha" / f"{char_id}.json"


def load_akasha_side(uid: str, char_id: str, root: Path | None = None) -> AkashaDisk | None:
    """读盘并解析。缺文件 / 坏结构返回 None（查询侧不展示右列）。"""
    path = akasha_char_path(uid, char_id, root)
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    boards: list[SubstatPriorityBoard] = []
    if "substat" in raw:
        items = parse_substat_priority_payload(raw["substat"])
        if items is not None:
            boards = compute_substat_priority_boards(items)
    rows: list[BuildLeaderboardRow] = []
    if "leaderboards" in raw:
        parsed_rows = parse_build_leaderboards_payload(raw["leaderboards"])
        if parsed_rows is not None:
            rows = list_visible_leaderboards(parsed_rows)
    dists: list[DamageDistributionBoard] = []
    if "damage" in raw:
        parsed_dd = parse_damage_distribution_payload(raw["damage"])
        if parsed_dd is not None:
            dists = list_visible_distributions(parsed_dd)
    ranks: list[GlobalRankRow] = []
    if "global" in raw and rows:
        parsed_gb = parse_global_ranks_payload(raw["global"], rows[0]["out_of"])
        if parsed_gb is not None:
            ranks = parsed_gb
    if not boards and not rows and not dists and not ranks:
        return None
    ids = pick_loadout_ids(rows)
    sp_out: list[SubstatPriorityBoard] = []
    if ids:
        for cid in ids[:SIDE_GAIN_LOADOUTS]:
            hit = match_calc_board(boards, cid)
            if hit is None:
                continue
            for item in boards:
                if item["calculation_id"] == hit["calculation_id"]:
                    sp_out.append(item)
                    break
    elif boards:
        sp_out = [boards[0]]
    dd_out: list[DamageDistributionBoard] = []
    want = ids if ids else ([dists[0]["calculation_id"]] if dists else [])
    for cid in want:
        found = find_damage_distribution(dists, cid)
        if found is not None:
            dd_out.append(found)
    return sp_out, rows, dd_out, ranks


async def dump_akasha_sides(
    uid: str,
    rank_data: Mapping[str, object],
    now: str,
    api: _CvApi | None = None,
    root: Path | None = None,
) -> None:
    """给刚写完的 rank.json 补每名角色的右栏原始 JSON。"""
    own = api is None
    if api is None:
        from ..utils.api.cv.request import _CvApi

        api = _CvApi()
    sem = asyncio.Semaphore(4)

    async def _run(char_id: str, md5: str) -> None:
        async with sem:
            await _dump_one(api, uid, char_id, md5, now, root)

    jobs: list[tuple[str, str]] = []
    for key, node in rank_data.items():
        char_id = str(key)
        if not isinstance(node, dict) or "md5" not in node:
            continue
        md5 = node["md5"]
        if not isinstance(md5, str) or not md5:
            continue
        jobs.append((char_id, md5))
    if jobs:
        await asyncio.gather(*[_run(cid, md5) for cid, md5 in jobs])
    if own:
        await api.close()


async def _dump_one(
    api: _CvApi,
    uid: str,
    char_id: str,
    md5: str,
    now: str,
    root: Path | None = None,
) -> None:
    sp_url = SUBSTAT_PRIORITY_API.format(quote(uid, safe=""), quote(md5, safe=""))
    lb_url = BUILD_LB_API.format(quote(uid, safe=""), quote(md5, safe=""))
    sp_raw = await api.get_json(sp_url)
    lb_raw = await api.get_json(lb_url, {"variant": "profilePage"})
    payload: dict[str, object] = {"md5": md5, "time": now, "character_id": char_id}
    if not isinstance(sp_raw, int):
        payload["substat"] = sp_raw
    if not isinstance(lb_raw, int):
        payload["leaderboards"] = lb_raw
    parsed_rows = parse_build_leaderboards_payload(lb_raw) if not isinstance(lb_raw, int) else None
    visible = list_visible_leaderboards(parsed_rows) if parsed_rows is not None else []
    calc_id = visible[0]["calculation_id"] if visible else ""
    out_of = visible[0]["out_of"] if visible else 0
    player_result = visible[0]["result"] if visible else 0.0
    if calc_id:
        dd_id = board_calculation_id(calc_id)
        dd_url = DAMAGE_DIST_API.format(quote(dd_id, safe=""), quote(uid, safe=""), quote(md5, safe=""))
        dd_raw = await api.get_json(dd_url)
        if not isinstance(dd_raw, int):
            payload["damage"] = dd_raw
    if calc_id and out_of > 0:
        gb_id = board_calculation_id(calc_id)
        thresh = f"{player_result + 0.01:.4f}"
        gb_url = NEARBY_LB_API.format(quote(gb_id, safe=""), thresh, SIDE_RANK_MAX)
        gb_raw = await api.get_json(gb_url)
        if not isinstance(gb_raw, int):
            payload["global"] = gb_raw
    if "substat" not in payload and "leaderboards" not in payload:
        return
    path = akasha_char_path(uid, char_id, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    logger.debug(t("log.genshinuid.akasha_side_cached", uid=uid, char_id=char_id))
