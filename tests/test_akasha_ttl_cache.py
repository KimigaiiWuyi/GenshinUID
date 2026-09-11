from __future__ import annotations

import sys
import asyncio
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

_ROOT = Path(__file__).resolve().parents[1]
_CV = _ROOT / "GenshinUID" / "utils" / "api" / "cv"

_SPEC = spec_from_file_location("akasha_cv_ttl_cache", _CV / "ttl_cache.py")
assert _SPEC is not None and _SPEC.loader is not None
_MOD = module_from_spec(_SPEC)
sys.modules["akasha_cv_ttl_cache"] = _MOD
_SPEC.loader.exec_module(_MOD)

TtlMemo = _MOD.TtlMemo


def test_second_call_same_key_skips_factory() -> None:
    async def main() -> None:
        clock = [100.0]
        memo: TtlMemo[list[str]] = TtlMemo(ttl_sec=3600, monotonic=lambda: clock[0])
        n = 0

        async def factory() -> list[str] | int:
            nonlocal n
            n += 1
            return ["ok"]

        first = await memo.get("u:m", factory)
        second = await memo.get("u:m", factory)
        assert first == ["ok"]
        assert second == ["ok"]
        assert n == 1

    asyncio.run(main())


def test_expired_key_refetches() -> None:
    async def main() -> None:
        clock = [0.0]
        memo: TtlMemo[list[str]] = TtlMemo(ttl_sec=10, monotonic=lambda: clock[0])
        n = 0

        async def factory() -> list[str] | int:
            nonlocal n
            n += 1
            return [str(n)]

        assert await memo.get("k", factory) == ["1"]
        clock[0] = 9.0
        assert await memo.get("k", factory) == ["1"]
        clock[0] = 10.1
        assert await memo.get("k", factory) == ["2"]
        assert n == 2

    asyncio.run(main())


def test_errno_is_not_cached() -> None:
    async def main() -> None:
        memo: TtlMemo[list[str]] = TtlMemo(ttl_sec=3600)
        n = 0

        async def factory() -> list[str] | int:
            nonlocal n
            n += 1
            return -1

        assert await memo.get("k", factory) == -1
        assert await memo.get("k", factory) == -1
        assert n == 2

    asyncio.run(main())


def test_inflight_same_key_shares_one_factory() -> None:
    async def main() -> None:
        memo: TtlMemo[list[str]] = TtlMemo(ttl_sec=3600)
        n = 0
        started = asyncio.Event()
        release = asyncio.Event()

        async def factory() -> list[str] | int:
            nonlocal n
            n += 1
            started.set()
            await release.wait()
            return ["once"]

        first = asyncio.create_task(memo.get("k", factory))
        await started.wait()
        second = asyncio.create_task(memo.get("k", factory))
        release.set()
        a, b = await asyncio.gather(first, second)
        assert a == ["once"]
        assert b == ["once"]
        assert n == 1

    asyncio.run(main())


def test_different_keys_do_not_share() -> None:
    async def main() -> None:
        memo: TtlMemo[list[str]] = TtlMemo(ttl_sec=3600)
        n = 0

        async def factory() -> list[str] | int:
            nonlocal n
            n += 1
            return [str(n)]

        a = await memo.get("a", factory)
        b = await memo.get("b", factory)
        assert a == ["1"]
        assert b == ["2"]
        assert n == 2

    asyncio.run(main())
