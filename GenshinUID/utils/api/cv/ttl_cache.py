"""Akasha 相同传参的短时缓存：TTL 1 小时，并发相同 key 只打一次 HTTP。

errno（``int``）不落盘，避免把失败锁一小时。
"""

from __future__ import annotations

import time
import asyncio
from typing import Generic, TypeVar
from collections.abc import Callable, Awaitable

T = TypeVar("T")

CV_CACHE_TTL_SEC = 3600.0


class TtlMemo(Generic[T]):
    """进程内 TTL 缓存。``get`` 的成功值（非 ``int``）按 key 复用。"""

    def __init__(
        self,
        ttl_sec: float = CV_CACHE_TTL_SEC,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl = ttl_sec
        self._monotonic = monotonic
        self._store: dict[str, tuple[float, T]] = {}
        self._inflight: dict[str, asyncio.Task[T | int]] = {}

    async def get(self, key: str, factory: Callable[[], Awaitable[T | int]]) -> T | int:
        """命中且未过期则直接返回；否则跑 ``factory``。

        已在飞的相同 ``key`` 共用同一个 Task，避免并发重复请求。
        """
        now = self._monotonic()
        if key in self._store:
            expires_at, value = self._store[key]
            if expires_at > now:
                return value
            del self._store[key]
        if key in self._inflight:
            return await self._inflight[key]
        task: asyncio.Task[T | int] = asyncio.create_task(factory())
        self._inflight[key] = task
        try:
            result = await task
            if not isinstance(result, int):
                self._store[key] = (self._monotonic() + self._ttl, result)
            return result
        finally:
            if key in self._inflight and self._inflight[key] is task:
                del self._inflight[key]
