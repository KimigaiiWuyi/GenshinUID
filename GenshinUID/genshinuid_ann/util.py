# -*- coding: UTF-8 -*-
import inspect
import datetime
import functools
from typing import Dict, Optional, TypedDict

import httpx


class _Dict(dict):
    __setattr__ = dict.__setitem__  # type: ignore
    __getattr__ = dict.__getitem__


class _CacheData(TypedDict):
    time: Optional[datetime.datetime]
    value: Optional[int]


def filter_list(plist, func):
    return list(filter(func, plist))


def cache(ttl=datetime.timedelta(hours=1), **kwargs):
    def wrap(func):
        cache_data: Dict[str, _CacheData] = {}

        @functools.wraps(func)
        async def wrapped(*args, **kw):
            nonlocal cache_data
            bound = inspect.signature(func).bind(*args, **kw)
            bound.apply_defaults()
            ins_key = '|'.join(
                ['%s_%s' % (k, v) for k, v in bound.arguments.items()]
            )
            default_data: _CacheData = {
                'time': None,
                'value': None,
            }
            data = cache_data.get(ins_key, default_data)

            now = datetime.datetime.now()
            if not data['time'] or now - data['time'] > ttl:
                try:
                    data['value'] = await func(*args, **kw)
                    data['time'] = now
                    cache_data[ins_key] = data
                except Exception as e:
                    raise e

            return data['value']

        return wrapped

    return wrap


@cache(ttl=datetime.timedelta(minutes=30), arg_key='url')
async def cache_request_json(url):
    async with httpx.AsyncClient() as client:
        res = await client.get(url, timeout=10)
        return res.json(object_hook=_Dict)


black_ids = [762, 422, 423, 1263, 495, 1957, 2522, 2388, 2516, 2476]
