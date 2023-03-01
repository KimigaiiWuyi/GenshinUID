import json
import time
import random
import string
import hashlib
from typing import Any, Dict, Optional

_S = {
    '2.44.1': {
        'LK2': 'IEIZiKYaput2OCKQprNuGsog1NZc1FkS',
        'K2': 'dZAwGk4e9aC0MXXItkwnHamjA1x30IYw',
        '25': 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs',
    },
    'os': '6cqshh5dhw73bzxn20oexa9k516chk7s',
    'PD': 'JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS',
}


def random_hex(length):
    result = hex(random.randint(0, 16**length)).replace('0x', '').upper()
    if len(result) < length:
        result = '0' * (length - len(result)) + result
    return result


def md5(text):
    md5_func = hashlib.md5()
    md5_func.update(text.encode())
    return md5_func.hexdigest()


def random_text(num: int) -> str:
    return ''.join(random.sample(string.ascii_lowercase + string.digits, num))


def _random_str_ds(
    salt: str,
    sets: str = string.ascii_lowercase + string.digits,
    with_body: bool = False,
    q: str = '',
    b: Optional[Dict[str, Any]] = None,
):
    i = str(int(time.time()))
    r = ''.join(random.sample(sets, 6))
    s = f'salt={salt}&t={i}&r={r}'
    if with_body:
        s += f'&b={json.dumps(b) if b else ""}&q={q}'
    c = md5(s)
    return f'{i},{r},{c}'


def _random_int_ds(salt: str, q: str = '', b: Optional[Dict[str, Any]] = None):
    br = json.dumps(b) if b else ''
    s = salt
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5(f'salt={s}&t={t}&r={r}&b={br}&q={q}')
    return f'{t},{r},{c}'


def get_ds_token(
    q: str = '',
    b: Optional[Dict[str, Any]] = None,
    salt: str = _S['2.44.1']['25'],
):
    return _random_int_ds(salt, q, b)


def get_web_ds_token(web=False):
    return _random_str_ds(_S['2.44.1']['LK2'] if web else _S['2.44.1']['K2'])


def generate_os_ds(salt: str = '') -> str:
    return _random_str_ds(salt or _S['os'], sets=string.ascii_letters)


def generate_passport_ds(q: str = '', b: Optional[Dict[str, Any]] = None):
    return _random_str_ds(_S['PD'], string.ascii_letters, True, q, b)
