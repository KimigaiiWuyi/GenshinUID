# -*- coding: UTF-8 -*-
import base64
import os
import json
import inspect
import functools
import datetime
import httpx
from io import BytesIO
from PIL import ImageFont

config_path = os.path.join(os.path.dirname(__file__), 'config.json')

class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

def get_path(*paths):
    return os.path.join(os.path.dirname(__file__), *paths)

def filter_list(plist, func):
    return list(filter(func, plist))

def get_font(size, w='85'):
    return ImageFont.truetype(get_path('font', f'HYWenHei {w}W.ttf'),size=size)

def pil2b64(data):
    bio = BytesIO()
    data = data.convert("RGB")
    data.save(bio, format='JPEG', quality=75)
    base64_str = base64.b64encode(bio.getvalue()).decode()
    return 'base64://' + base64_str

def pil2b64(data):
    bio = BytesIO()
    data = data.convert("RGB")
    data.save(bio, format='JPEG', quality=75)
    base64_str = base64.b64encode(bio.getvalue()).decode()
    return 'base64://' + base64_str

def cache(ttl=datetime.timedelta(hours=1), **kwargs):
    def wrap(func):
        cache_data = {}

        @functools.wraps(func)
        async def wrapped(*args, **kw):
            nonlocal cache_data
            bound = inspect.signature(func).bind(*args, **kw)
            bound.apply_defaults()
            ins_key = '|'.join(['%s_%s' % (k, v) for k, v in bound.arguments.items()])
            default_data = {"time": None, "value": None}
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
        return res.json(object_hook=Dict)

def load_config() -> int:
    try:
        with open(config_path, encoding='utf8') as f:
            config = json.load(f)
            return config
    except:
        return {"group": [], "ids": []}

#写入群设置
def write_config(config) -> int:
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False)

black_ids = [762, 422, 423, 1263, 495, 1957, 2522, 2388, 2516, 2476]
config = load_config()