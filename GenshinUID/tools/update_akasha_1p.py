"""
从 akasha.cv 抓取各榜单 top 1% 面板算术平均，写入 effect/akasha_1p_avg.json。

不依赖 gsuid_core，版本更新后直接跑以替换旧文件:

  python GenshinUID/tools/update_akasha_1p.py
  python GenshinUID/tools/update_akasha_1p.py --dry-run
  python GenshinUID/tools/update_akasha_1p.py --concurrency 8
  python GenshinUID/tools/update_akasha_1p.py --include-filters
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "genshinuid_enka" / "effect" / "akasha_1p_avg.json"

CATEGORIES_URL = "https://akasha.cv/api/v2/leaderboards/categories"
CHARTS_URL = "https://akasha.cv/api/charts/calculations/{calculationId}"

# Cloudflare 拦常见浏览器 UA；与 _CvApi 同一 UA 才能拿到 JSON。
HEADERS = {
    "User-Agent": "GsCore / GenshinUID / 6.2.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

_RETRY_STATUS = {429, 502, 503, 504}
_RETRY_TIMES = 6

SOURCE = {
    "categories": CATEGORIES_URL,
    "avg": "https://akasha.cv/api/charts/calculations/{calculationId}",
    "variantAvg": "https://akasha.cv/api/charts/calculations/{calculationId}?variant={variant}",
    "note": "avgStats is the arithmetic mean of the top 1% bucket for that leaderboard. Same for every player.",
}


@dataclass(frozen=True)
class BoardJob:
    character_id: int
    character_name: str
    element: str
    leaderboard: str
    short: str
    weapon: str
    weapon_id: str
    refinement: int
    calculation_id: str
    default_variant: str | None
    filter_names: tuple[str, ...]


@dataclass(frozen=True)
class ChartAvg:
    avg_stats: dict[str, float]
    score_avg: float
    score_min: float
    score_max: float


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _avg_stats(raw: object) -> dict[str, float]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        num = _as_float(value)
        if num is None:
            continue
        out[key] = num
    return out


def _parse_jobs(payload: object) -> list[BoardJob]:
    if not isinstance(payload, dict) or "data" not in payload:
        raise RuntimeError("categories 响应没有 data")
    data = payload["data"]
    if not isinstance(data, list):
        raise RuntimeError("categories.data 不是列表")
    jobs: list[BoardJob] = []
    for cat in data:
        if not isinstance(cat, dict):
            continue
        if "characterId" not in cat or "characterName" not in cat or "name" not in cat:
            continue
        if "short" not in cat or "weapons" not in cat:
            continue
        cid = _as_int(cat["characterId"])
        name = cat["characterName"]
        lb_name = cat["name"]
        short = cat["short"]
        weapons = cat["weapons"]
        element = cat["element"] if "element" in cat and isinstance(cat["element"], str) else ""
        if cid is None or not isinstance(name, str) or not isinstance(lb_name, str):
            continue
        if not isinstance(short, str) or not isinstance(weapons, list):
            continue
        for weapon in weapons:
            job = _parse_weapon_job(cid, name, element, lb_name, short, weapon)
            if job is not None:
                jobs.append(job)
    if not jobs:
        raise RuntimeError("没有解析到任何榜单")
    return jobs


def _parse_weapon_job(
    character_id: int,
    character_name: str,
    element: str,
    leaderboard: str,
    short: str,
    weapon: object,
) -> BoardJob | None:
    if not isinstance(weapon, dict):
        return None
    if "hidden" in weapon and weapon["hidden"] is True:
        return None
    needed = ("name", "weaponId", "refinement", "calculationId")
    for key in needed:
        if key not in weapon:
            return None
    wname = weapon["name"]
    if not isinstance(wname, str):
        return None
    wid = weapon["weaponId"]
    if isinstance(wid, int):
        weapon_id = str(wid)
    elif isinstance(wid, str):
        weapon_id = wid
    else:
        return None
    refinement = _as_int(weapon["refinement"])
    calc_id = weapon["calculationId"]
    if refinement is None or not isinstance(calc_id, (str, int)):
        return None
    default_variant: str | None = None
    if "defaultVariant" in weapon and isinstance(weapon["defaultVariant"], str) and weapon["defaultVariant"]:
        default_variant = weapon["defaultVariant"]
    filters: list[str] = []
    if "filters" in weapon and isinstance(weapon["filters"], list):
        for filt in weapon["filters"]:
            if isinstance(filt, dict) and "name" in filt and isinstance(filt["name"], str):
                filters.append(filt["name"])
    return BoardJob(
        character_id=character_id,
        character_name=character_name,
        element=element,
        leaderboard=leaderboard,
        short=short,
        weapon=wname,
        weapon_id=weapon_id,
        refinement=refinement,
        calculation_id=str(calc_id),
        default_variant=default_variant,
        filter_names=tuple(filters),
    )


async def _get_json(client: httpx.AsyncClient, url: str, params: Mapping[str, str] | None = None) -> object:
    delay = 1.0
    last_status = 0
    for _ in range(_RETRY_TIMES):
        resp = await client.get(url, params=params)
        last_status = resp.status_code
        if resp.status_code in _RETRY_STATUS:
            await asyncio.sleep(delay)
            delay *= 1.6
            continue
        ctype = resp.headers["content-type"] if "content-type" in resp.headers else ""
        if "json" not in ctype.lower():
            raise RuntimeError(f"非 JSON（可能是 Cloudflare）：{url} status={resp.status_code}")
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError(f"重试耗尽: {url} status={last_status}")


async def _fetch_chart(client: httpx.AsyncClient, calculation_id: str, variant: str | None) -> ChartAvg:
    url = CHARTS_URL.format(calculationId=calculation_id)
    params = {"variant": variant} if variant else None
    payload = await _get_json(client, url, params)
    if not isinstance(payload, dict) or "data" not in payload:
        raise RuntimeError(f"charts 无 data: {calculation_id} variant={variant}")
    data = payload["data"]
    if not isinstance(data, list) or not data:
        raise RuntimeError(f"charts 空桶: {calculation_id} variant={variant}")
    first = data[0]
    if not isinstance(first, dict):
        raise RuntimeError(f"charts 首桶不是对象: {calculation_id}")
    if "avg" not in first or "min" not in first or "max" not in first:
        raise RuntimeError(f"charts 首桶缺 avg/min/max: {calculation_id}")
    score_avg = _as_float(first["avg"])
    score_min = _as_float(first["min"])
    score_max = _as_float(first["max"])
    if score_avg is None or score_min is None or score_max is None:
        raise RuntimeError(f"charts 分值不是数字: {calculation_id}")
    stats_raw: object = first["avgStats"] if "avgStats" in first else {}
    return ChartAvg(
        avg_stats=_avg_stats(stats_raw),
        score_avg=score_avg,
        score_min=score_min,
        score_max=score_max,
    )


def _row_from_job(job: BoardJob, base: ChartAvg, default_avg: ChartAvg | None) -> dict[str, object]:
    row: dict[str, object] = {
        "characterId": job.character_id,
        "characterName": job.character_name,
        "element": job.element,
        "leaderboard": job.leaderboard,
        "short": job.short,
        "weapon": job.weapon,
        "weaponId": job.weapon_id,
        "refinement": job.refinement,
        "calculationId": job.calculation_id,
        "avgStats": base.avg_stats,
        "score": {"avg": base.score_avg, "min": base.score_min, "max": base.score_max},
    }
    if job.default_variant and default_avg is not None:
        row["defaultVariant"] = job.default_variant
        row["defaultVariantAvgStats"] = default_avg.avg_stats
        row["defaultVariantScore"] = {
            "avg": default_avg.score_avg,
            "min": default_avg.score_min,
            "max": default_avg.score_max,
        }
    return row


def _row_sort_key(row: dict[str, object]) -> tuple[int, str, str]:
    cid = row["characterId"]
    calc = row["calculationId"]
    weapon = row["weapon"]
    assert isinstance(cid, int)
    assert isinstance(calc, str)
    assert isinstance(weapon, str)
    return (cid, calc, weapon)


async def scrape(
    *,
    concurrency: int,
    include_filters: bool,
    limit: int | None,
) -> dict[str, object]:
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
        cats = await _get_json(client, CATEGORIES_URL)
        jobs = _parse_jobs(cats)
        if limit is not None:
            jobs = jobs[:limit]
        sem = asyncio.Semaphore(concurrency)
        done = 0
        total = len(jobs)

        async def run_job(job: BoardJob) -> dict[str, object]:
            nonlocal done
            async with sem:
                base = await _fetch_chart(client, job.calculation_id, None)
                default_avg: ChartAvg | None = None
                if job.default_variant:
                    default_avg = await _fetch_chart(client, job.calculation_id, job.default_variant)
                row = _row_from_job(job, base, default_avg)
                if include_filters and job.filter_names:
                    variants: dict[str, dict[str, object]] = {}
                    for name in job.filter_names:
                        if job.default_variant and name == job.default_variant:
                            continue
                        chart = await _fetch_chart(client, job.calculation_id, name)
                        variants[name] = {
                            "avgStats": chart.avg_stats,
                            "score": {
                                "avg": chart.score_avg,
                                "min": chart.score_min,
                                "max": chart.score_max,
                            },
                        }
                    if variants:
                        row["filterVariants"] = variants
                done += 1
                if done % 20 == 0 or done == total:
                    print(f"  {done}/{total}", flush=True)
                return row

        rows = list(await asyncio.gather(*[run_job(j) for j in jobs]))
        rows.sort(key=_row_sort_key)

    return {
        "source": SOURCE,
        "fetchedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(rows),
        "leaderboards": rows,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="抓取 Akasha 各榜单 top 1% avgStats")
    parser.add_argument("--dry-run", action="store_true", help="只拉数据不写文件")
    parser.add_argument("--concurrency", type=int, default=8, help="并发请求数")
    parser.add_argument("--include-filters", action="store_true", help="额外抓全部 ER 等过滤变体")
    parser.add_argument("--limit", type=int, default=None, help="只抓前 N 条（调试）")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="输出 json 路径")
    args = parser.parse_args()
    if args.concurrency < 1:
        print("concurrency 必须 >= 1", file=sys.stderr)
        return 2

    print(f"categories → charts, concurrency={args.concurrency}", flush=True)
    payload = asyncio.run(
        scrape(
            concurrency=args.concurrency,
            include_filters=args.include_filters,
            limit=args.limit,
        )
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(f"leaderboards: {payload['count']}", flush=True)
    if args.dry_run:
        print(f"dry-run, 将写入 {args.out} ({len(text)} bytes)")
        return 0
    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".json.tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
