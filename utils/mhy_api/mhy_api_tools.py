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


def old_version_get_ds_token(mysbbs=False):
    if mysbbs:
        n = 'dWCcD2FsOUXEstC5f9xubswZxEeoBOTc'
    else:
        n = 'h8w582wxwgqvahcdkpvdhbh2w9casgfl'
    i = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5('salt=' + n + '&t=' + i + '&r=' + r)
    return i + ',' + r + ',' + c


def get_ds_token(q='', b=None):
    if b:
        br = json.dumps(b)
    else:
        br = ''
    s = 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs'
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5('salt=' + s + '&t=' + t + '&r=' + r + '&b=' + br + '&q=' + q)
    return t + ',' + r + ',' + c
