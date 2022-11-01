import json
import time
import random
import string
import hashlib


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


def old_version_get_ds_token(mysbbs=False):
    if mysbbs:
        n = 'N50pqm7FSy2AkFz2B3TqtuZMJ5TOl3Ep'
    else:
        n = 'z8DRIUjNDT7IT5IZXvrUAxyupA1peND9'
    i = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5('salt=' + n + '&t=' + i + '&r=' + r)
    return i + ',' + r + ',' + c


def get_ds_token(q='', b=None, salt=None):
    if b:
        br = json.dumps(b)
    else:
        br = ''
    if salt:
        s = salt
    else:
        s = 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs'
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5('salt=' + s + '&t=' + t + '&r=' + r + '&b=' + br + '&q=' + q)
    return t + ',' + r + ',' + c

def generate_dynamic_secret(salt=None) -> str:
    """Create a new overseas dynamic secret."""
    if salt:
        s = salt
    else:
        s = '6cqshh5dhw73bzxn20oexa9k516chk7s'
    t = int(time.time())
    r = "".join(random.choices(string.ascii_letters, k=6))
    h = hashlib.md5(f"salt={s}&t={t}&r={r}".encode()).hexdigest()
    return f"{t},{r},{h}"
