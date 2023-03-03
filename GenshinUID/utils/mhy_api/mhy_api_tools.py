import hmac
import json
import time
import random
import string
import hashlib
from typing import Any, Dict, Optional


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
        s += f"&b={json.dumps(b) if b else ''}&q={q}"
    c = md5(s)
    return f'{i},{r},{c}'


def old_version_get_ds_token(mysbbs=False):
    return _random_str_ds(
        'N50pqm7FSy2AkFz2B3TqtuZMJ5TOl3Ep'
        if mysbbs
        else 'z8DRIUjNDT7IT5IZXvrUAxyupA1peND9'
    )


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
    salt: str = 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs',
):
    return _random_int_ds(salt, q, b)


def generate_dynamic_secret(salt: str = "") -> str:
    """Create a new overseas dynamic secret."""
    return _random_str_ds(
        salt or '6cqshh5dhw73bzxn20oexa9k516chk7s', sets=string.ascii_letters
    )


def generate_passport_ds(q: str = '', b: Optional[Dict[str, Any]] = None):
    return _random_str_ds(
        "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS", string.ascii_letters, True, q, b
    )


def HMCASHA256(data, key):
    key = key.encode('utf-8')
    message = data.encode('utf-8')
    sign = hmac.new(key, message, digestmod=hashlib.sha256).digest()
    return sign.hex()


def gen_payment_sign(data):
    data = dict(sorted(data.items(), key=lambda x: x[0]))
    value = "".join([str(i) for i in data.values()])
    sign = HMCASHA256(value, "6bdc3982c25f3f3c38668a32d287d16b")
    return sign
