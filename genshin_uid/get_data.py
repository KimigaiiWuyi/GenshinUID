import datetime
import hashlib
import json
import os
import random
import re
import sqlite3
import string
import time
from aiohttp import ClientSession
from shutil import copyfile

import requests
from httpx import AsyncClient
from nonebot import logger

mhyVersion = "2.11.1"

BASE_PATH = os.path.dirname(__file__)
BASE2_PATH = os.path.join(BASE_PATH, 'mihoyo_libs/mihoyo_bbs')
INDEX_PATH = os.path.join(BASE2_PATH, 'index')


async def config_check(func, mode="CHECK"):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS Config
            (Name TEXT PRIMARY KEY     NOT NULL,
            Status      TEXT,
            GroupList   TEXT,
            Extra       TEXT);''')
    c.execute("INSERT OR IGNORE INTO Config (Name,Status) \
                            VALUES (?, ?)", (func, "on"))
    if mode == "CHECK":
        cursor = c.execute("SELECT * from Config WHERE Name = ?", (func,))
        c_data = cursor.fetchall()
        conn.close()
        if c_data[0][1] != "off":
            return True
        else:
            return False
    elif mode == "OPEN":
        c.execute("UPDATE Config SET Status = ? WHERE Name=?", ("on", func))
        conn.commit()
        conn.close()
        return True
    elif mode == "CLOSED":
        c.execute("UPDATE Config SET Status = ? WHERE Name=?", ("off", func))
        conn.commit()
        conn.close()
        return True


async def get_a_lots(qid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS UseridDict
            (QID INT PRIMARY KEY     NOT NULL,
            lots        TEXT,
            cache       TEXT,
            permission  TEXT,
            Status      TEXT,
            Subscribe   TEXT,
            Extra       TEXT);''')
    cursor = c.execute("SELECT * from UseridDict WHERE QID = ?", (qid,))
    c_data = cursor.fetchall()
    with open(os.path.join(INDEX_PATH, 'lots.txt'), "r") as f:
        raw_data = f.read()
        raw_data = raw_data.replace(' ', "").split('-')

    if len(c_data) == 0:
        num = random.randint(1, len(raw_data) - 1)
        data = raw_data[num]
        c.execute("INSERT OR IGNORE INTO UseridDict (QID,lots) \
                            VALUES (?, ?)", (qid, str(num)))
    else:
        if c_data[0][1] is None:
            num = random.randint(0, len(raw_data) - 1)
            data = raw_data[num]
            c.execute("UPDATE UseridDict SET lots = ? WHERE QID=?", (str(num), qid))
        else:
            num = int(c_data[0][1])
            data = raw_data[num]
    conn.commit()
    conn.close()
    return data


async def open_push(uid, qid, status, mode):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT * from NewCookiesTable WHERE UID = ?", (uid,))
    c_data = cursor.fetchall()
    if len(c_data) != 0:
        try:
            c.execute("UPDATE NewCookiesTable SET {s} = ?,QID = ? WHERE UID=?".format(s=mode), (status, qid, uid))
            conn.commit()
            conn.close()
            return "成功！"
        except:
            return "未找到Ck绑定记录。"
    else:
        return "未找到Ck绑定记录。"


async def check_db():
    return_str = str()
    invalid_list = []
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT UID,Cookies,QID  from NewCookiesTable")
    c_data = cursor.fetchall()
    for row in c_data:
        try:
            aid = re.search(r"account_id=(\d*)", row[1])
            mihoyo_id_data = aid.group(0).split('=')
            mihoyo_id = mihoyo_id_data[1]
            mys_data = await get_mihoyo_bbs_info(mihoyo_id, row[1])
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            return_str = return_str + f"uid{row[0]}/mys{mihoyo_id}的Cookies是正常的！\n"
        except:
            return_str = return_str + f"uid{row[0]}的Cookies是异常的！已删除该条Cookies！\n"
            invalid_list.append([row[2], row[0]])
            c.execute("DELETE from NewCookiesTable where UID=?", (row[0],))
            try:
                c.execute("DELETE from CookiesCache where Cookies=?", (row[1],))
            except:
                pass
    conn.commit()
    conn.close()
    return [return_str, invalid_list]


async def connect_db(userid, uid=None, mys=None):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS UIDDATA
        (USERID INT PRIMARY KEY     NOT NULL,
        UID         TEXT,
        MYSID       TEXT);''')

    c.execute("INSERT OR IGNORE INTO UIDDATA (USERID,UID,MYSID) \
    VALUES (?, ?,?)", (userid, uid, mys))

    if uid:
        c.execute("UPDATE UIDDATA SET UID = ? WHERE USERID=?", (uid, userid))
    if mys:
        c.execute("UPDATE UIDDATA SET MYSID = ? WHERE USERID=?", (mys, userid))

    conn.commit()
    conn.close()


async def select_db(userid, mode="auto"):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT *  FROM UIDDATA WHERE USERID = ?", (userid,))
    for row in cursor:
        if mode == "auto":
            if row[0]:
                if row[2]:
                    return [row[2], 3]
                elif row[1]:
                    return [row[1], 2]
                else:
                    return None
            else:
                return None
        elif mode == "uid":
            return [row[1], 2]
        elif mode == "mys":
            return [row[2], 3]


async def delete_cache():
    try:
        copyfile("ID_DATA.db", "ID_DATA_bak.db")
        logger.info("————数据库成功备份————")
    except:
        logger.info("————数据库备份失败————")

    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        c.execute("DROP TABLE CookiesCache")
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Extra=?", (None, "limit30"))
        c.execute('''CREATE TABLE IF NOT EXISTS CookiesCache
        (UID TEXT PRIMARY KEY,
        MYSID         TEXT,
        Cookies       TEXT);''')
        conn.commit()
        conn.close()
        logger.info("————UID查询缓存已清空————")
    except:
        logger.info("\nerror\n")

    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        c.execute("UPDATE UseridDict SET lots=NULL")
        conn.commit()
        conn.close()
        logger.info("————御神签缓存已清空————")
    except:
        logger.info("\nerror\n")


def error_db(ck, err):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    if err == "error":
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Cookies=?", ("error", ck))
    elif err == "limit30":
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Cookies=?", ("limit30", ck))


def cache_db(uid, mode=1, mys=None):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS CookiesCache
        (UID TEXT PRIMARY KEY,
        MYSID         TEXT,
        Cookies       TEXT);''')

    if mode == 1:
        if mys:
            cursor = c.execute("SELECT *  FROM CookiesCache WHERE MYSID = ?", (mys,))
        else:
            cursor = c.execute("SELECT *  FROM CookiesCache WHERE UID = ?", (uid,))
    else:
        cursor = c.execute("SELECT *  FROM CookiesCache WHERE MYSID = ?", (uid,))
    c_data = cursor.fetchall()

    if len(c_data) == 0:
        if mode == 2:
            conn.create_function("REGEXP", 2, regex_func)
            cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE REGEXP(Cookies, ?)", (uid,))
            d_data = cursor.fetchall()

        else:
            cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE UID = ?", (uid,))
            d_data = cursor.fetchall()

        if len(d_data) != 0:
            if d_data[0][7] != "error":
                use = d_data[0][1]
                if mode == 1:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                            VALUES (?, ?)", (use, uid))
                elif mode == 2:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                            VALUES (?, ?)", (use, uid))
            else:
                cookies_row = c.execute("SELECT * FROM NewCookiesTable WHERE Extra IS NULL ORDER BY RANDOM() LIMIT 1")
                e_data = cookies_row.fetchall()
                if len(e_data) != 0:
                    if mode == 1:
                        c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                                VALUES (?, ?)", (e_data[0][1], uid))
                    elif mode == 2:
                        c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                                VALUES (?, ?)", (e_data[0][1], uid))
                    use = e_data[0][1]
                else:
                    return "没有可以使用的Cookies！"
        else:
            cookies_row = c.execute("SELECT * FROM NewCookiesTable WHERE Extra IS NULL ORDER BY RANDOM() LIMIT 1")
            e_data = cookies_row.fetchall()
            if len(e_data) != 0:
                if mode == 1:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                            VALUES (?, ?)", (e_data[0][1], uid))
                elif mode == 2:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                            VALUES (?, ?)", (e_data[0][1], uid))
                use = e_data[0][1]
            else:
                return "没有可以使用的Cookies！"
    else:
        use = c_data[0][2]
        if mys:
            try:
                c.execute("UPDATE CookiesCache SET UID = ? WHERE MYSID=?", (uid, mys))
            except:
                c.execute("UPDATE CookiesCache SET MYSID = ? WHERE UID=?", (mys, uid))

    conn.commit()
    conn.close()
    return use


def regex_func(value, patter):
    c_pattern = re.compile(r"account_id={}".format(patter))
    return c_pattern.search(value) is not None


async def cookies_db(uid, cookies, qid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS NewCookiesTable
    (UID INT PRIMARY KEY     NOT NULL,
    Cookies         TEXT,
    QID         INT,
    StatusA     TEXT,
    StatusB     TEXT,
    StatusC     TEXT,
    NUM         INT,
    Extra       TEXT);''')

    cursor = c.execute("SELECT * from NewCookiesTable WHERE UID = ?", (uid,))
    c_data = cursor.fetchall()
    if len(c_data) == 0:
        c.execute("INSERT OR IGNORE INTO NewCookiesTable (Cookies,UID,StatusA,StatusB,StatusC,NUM,QID) \
            VALUES (?, ?,?,?,?,?,?)", (cookies, uid, "off", "off", "off", 140, qid))
    else:
        c.execute("UPDATE NewCookiesTable SET Cookies = ? WHERE UID=?", (cookies, uid))

    conn.commit()
    conn.close()


async def stoken_db(s_cookies, uid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    columns = [i[1] for i in c.execute('PRAGMA table_info(NewCookiesTable)')]

    if "Stoken" not in columns:
        c.execute('ALTER TABLE NewCookiesTable ADD COLUMN Stoken TEXT')

    c.execute("UPDATE NewCookiesTable SET Stoken = ? WHERE UID=?", (s_cookies, int(uid)))

    conn.commit()
    conn.close()


async def get_stoken(uid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    try:
        cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE UID = ?", (uid,))
        c_data = cursor.fetchall()
        stoken = c_data[0][8]
    except:
        return

    return stoken


async def owner_cookies(uid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    try:
        cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE UID = ?", (uid,))
        c_data = cursor.fetchall()
        cookies = c_data[0][1]
    except:
        return

    return cookies


def random_hex(length):
    result = hex(random.randint(0, 16 ** length)).replace('0x', '').upper()
    if len(result) < length:
        result = "0" * (length - len(result)) + result
    return result


def md5(text):
    md5_func = hashlib.md5()
    md5_func.update(text.encode())
    return md5_func.hexdigest()


def old_version_get_ds_token(mysbbs=False):
    if mysbbs:
        n = "fd3ykrh7o1j54g581upo1tvpam0dsgtf"
    else:
        n = "h8w582wxwgqvahcdkpvdhbh2w9casgfl"
    i = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return i + "," + r + "," + c


def get_ds_token(q="", b=None):
    if b:
        br = json.dumps(b)
    else:
        br = ""
    s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r + "&b=" + br + "&q=" + q)
    return t + "," + r + "," + c


async def get_stoken_by_login_ticket(loginticket, mys_id):
    async with AsyncClient() as client:
        req = await client.get(
            url="https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket",
            params={
                "login_ticket": loginticket,
                "token_types" : "3",
                "uid"         : mys_id
            }
        )
    return req.json()


async def get_daily_data(uid, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/dailyNote",
                headers={
                    'DS'               : get_ds_token("role_id=" + uid + "&server=" + server_id),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/',
                    "Cookie"           : await owner_cookies(uid)},
                params={
                    "server" : server_id,
                    "role_id": uid
                }
            )
            data = json.loads(req.text)
        return data
    except requests.exceptions.SSLError:
        try:
            async with AsyncClient() as client:
                req = await client.get(
                    url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/dailyNote",
                    headers={
                        'DS'               : get_ds_token("role_id=" + uid + "&server=" + server_id),
                        'x-rpc-app_version': mhyVersion,
                        'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 '
                                             '(KHTML, like Gecko) miHoYoBBS/2.11.1',
                        'x-rpc-client_type': '5',
                        'Referer'          : 'https://webstatic.mihoyo.com/',
                        "Cookie"           : await owner_cookies(uid)},
                    params={
                        "server" : server_id,
                        "role_id": uid
                    }
                )
            data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            logger.info("当前状态读取Api失败！")
    except Exception as e:
        logger.info("访问每日信息失败，请重试！")
        logger.info(e.with_traceback)


async def get_sign_list():
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/home",
                headers={
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/'},
                params={
                    "act_id": "e202009291139501"
                }
            )
            data = json.loads(req.text)
        return data
    except:
        logger.info("获取签到奖励列表失败，请重试")


async def get_sign_info(uid, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/info",
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie"           : await owner_cookies(uid),
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/'},
                params={
                    "act_id": "e202009291139501",
                    "region": server_id,
                    "uid"   : uid
                }
            )
            data = json.loads(req.text)
        return data
    except:
        logger.info("获取签到信息失败，请重试")


async def mihoyo_bbs_sign(uid, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        req = requests.post(
            url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign",
            headers={
                'User_Agent'       : 'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 ('
                                     'KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 '
                                     'miHoYoBBS/2.3.0',
                "Cookie"           : await owner_cookies(uid),
                "x-rpc-device_id"  : random_hex(32),
                'Origin'           : 'https://webstatic.mihoyo.com',
                'X_Requested_With' : 'com.mihoyo.hyperion',
                'DS'               : old_version_get_ds_token(),
                'x-rpc-client_type': '5',
                'Referer'          : 'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id'
                                     '=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon',
                'x-rpc-app_version': '2.3.0'
            },
            json={"act_id": "e202009291139501", "uid": uid, "region": server_id}
        )
        data2 = json.loads(req.text)
        return data2
    except:
        logger.info("签到失败，请重试")


async def get_award(uid, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://hk4e-api.mihoyo.com/event/ys_ledger/monthInfo",
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie"           : await owner_cookies(uid),
                    'DS'               : old_version_get_ds_token(),
                    "x-rpc-device_id"  : random_hex(32),
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/'},
                params={
                    "act_id"                : "e202009291139501",
                    "bind_region"           : server_id,
                    "bind_uid"              : uid,
                    "month"                 : "0",
                    "bbs_presentation_style": "fullscreen",
                    "bbs_auth_required"     : True,
                    "utm_source"            : "bbs",
                    "utm_medium"            : "mys",
                    "utm_campaign"          : "icon"
                }
            )
            data = json.loads(req.text)
        return data
    except:
        logger.info("访问失败，请重试！")
        # sys.exit(1)


async def get_info(uid, ck, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/index",
                headers={
                    'DS'               : get_ds_token("role_id=" + uid + "&server=" + server_id),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/',
                    "Cookie"           : ck},
                params={
                    "role_id": uid,
                    "server" : server_id
                }
            )
            data = json.loads(req.text)
        return data
    except requests.exceptions.SSLError:
        try:
            async with AsyncClient() as client:
                req = await client.get(
                    url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/index",
                    headers={
                        'DS'               : get_ds_token("role_id=" + uid + "&server=" + server_id),
                        'x-rpc-app_version': mhyVersion,
                        'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 '
                                             '(KHTML, like Gecko) miHoYoBBS/2.11.1',
                        'x-rpc-client_type': '5',
                        'Referer'          : 'https://webstatic.mihoyo.com/',
                        "Cookie"           : ck},
                    params={
                        "role_id": uid,
                        "server" : server_id
                    }
                )
            data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            logger.info("米游社基础信息读取新Api失败！")
    except Exception as e:
        logger.info("米游社基础信息读取旧Api失败！")
        logger.info(e.with_traceback)


async def get_spiral_abyss_info(uid, ck, schedule_type="1", server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/spiralAbyss",
                headers={
                    'DS'               : get_ds_token(
                        "role_id=" + uid + "&schedule_type=" + schedule_type + "&server=" + server_id),
                    'Origin'           : 'https://webstatic.mihoyo.com',
                    'Cookie'           : ck,
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS '
                                         'X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/'
                },
                params={
                    "schedule_type": schedule_type,
                    "role_id"      : uid,
                    "server"       : server_id
                }
            )
            data = json.loads(req.text)
        return data
    except requests.exceptions.SSLError:
        try:
            async with AsyncClient() as client:
                req = await client.get(
                    url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/spiralAbyss",
                    headers={
                        'DS'               : get_ds_token(
                            "role_id=" + uid + "&schedule_type=" + schedule_type + "&server=" + server_id),
                        'Origin'           : 'https://webstatic.mihoyo.com',
                        'Cookie'           : ck,
                        'x-rpc-app_version': mhyVersion,
                        'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 '
                                             '(KHTML, like Gecko) miHoYoBBS/2.11.1',
                        'x-rpc-client_type': '5',
                        'Referer'          : 'https://webstatic.mihoyo.com/'
                    },
                    params={
                        "role_id"               : uid,
                        "server"                : server_id,
                        "bbs_presentation_style": "fullscreen",
                        "bbs_auth_required"     : "true",
                        "utm_source"            : "bbs",
                        "utm_medium"            : "mys",
                        "utm_campaign"          : "icon"
                    }
                )
            data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            logger.info("深渊信息读取新Api失败！")
    except Exception as e:
        logger.info("深渊信息读取老Api失败！")
        logger.info(e.with_traceback)


def get_character(uid, character_ids, ck, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    try:
        req = requests.post(
            url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/character",
            headers={
                'DS'               : get_ds_token('', {"character_ids": character_ids, "role_id": uid,
                                                       "server"       : server_id}),
                'Origin'           : 'https://webstatic.mihoyo.com',
                'Cookie'           : ck,
                'x-rpc-app_version': mhyVersion,
                'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, '
                                     'like Gecko) miHoYoBBS/2.11.1',
                'x-rpc-client_type': '5',
                'Referer'          : 'https://webstatic.mihoyo.com/'
            },
            json={"character_ids": character_ids, "role_id": uid, "server": server_id}
        )
        data2 = json.loads(req.text)
        return data2
    except requests.exceptions.SSLError:
        try:
            req = requests.post(
                url="https://api-takumi-record.mihoyo.com/game_record/app/genshin/api/character",
                headers={
                    'DS'               : get_ds_token('', {"character_ids": character_ids, "role_id": uid,
                                                           "server"       : server_id}),
                    'Origin'           : 'https://webstatic.mihoyo.com',
                    'Cookie'           : ck,
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/'
                },
                json={"character_ids": character_ids, "role_id": uid, "server": server_id}
            )
            data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            logger.info("深渊信息读取新Api失败！")
    except Exception as e:
        logger.info("深渊信息读取老Api失败！")
        logger.info(e.with_traceback)


async def get_calculate_info(client: ClientSession, uid, char_id, ck, name, server_id="cn_gf01"):
    if uid[0] == '5':
        server_id = "cn_qd01"
    url = "https://api-takumi.mihoyo.com/event/e20200928calculate/v1/sync/avatar/detail"
    req = await client.get(
        url=url,
        headers={
            'DS': get_ds_token("uid={}&avatar_id={}&region={}".format(uid, char_id, server_id)),
            'x-rpc-app_version': mhyVersion,
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                          'KHTML, like Gecko) miHoYoBBS/2.11.1',
            'x-rpc-client_type': '5',
            'Referer': 'https://webstatic.mihoyo.com/',
            "Cookie": ck},
        params={
            "avatar_id": char_id,
            "uid": uid,
            "region": server_id
        }
    )
    data = await req.json()
    data.update({"name": name})
    return data


async def get_mihoyo_bbs_info(mysid, ck):
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/card/wapi/getGameRecordCard",
                headers={
                    'DS'               : get_ds_token("uid=" + mysid),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                                         'KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer'          : 'https://webstatic.mihoyo.com/',
                    "Cookie"           : ck},
                params={"uid": mysid}
            )
            data = json.loads(req.text)
        return data
    except requests.exceptions.SSLError:
        try:
            async with AsyncClient() as client:
                req = await client.get(
                    url="https://api-takumi-record.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid=" + mysid,
                    headers={
                        'DS'               : get_ds_token("uid=" + mysid),
                        'x-rpc-app_version': mhyVersion,
                        'User-Agent'       : 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 '
                                             '(KHTML, like Gecko) miHoYoBBS/2.11.1',
                        'x-rpc-client_type': '5',
                        'Referer'          : 'https://webstatic.mihoyo.com/',
                        "Cookie"           : ck},
                    params={"uid": mysid}
                )
                data = json.loads(req.text)
            return data
        except json.decoder.JSONDecodeError:
            logger.info("米游社信息读取新Api失败！")
    except Exception as e:
        logger.info("米游社信息读取老Api失败！")
        logger.info(e.with_traceback)


async def get_audio_info(name, audioid, language="cn"):
    url = "https://genshin.minigg.cn/"
    async with AsyncClient() as client:
        req = await client.get(
            url=url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/95.0.4638.69 Safari/537.36',
                'Referer'   : 'https://genshin.minigg.cn/index.html'},
            params={"characters": name, "audioid": audioid, "language": language}
        )
    return req.text


async def get_weapon_info(name, level=None):
    if level:
        params = {"query": name, "stats": level}
    else:
        params = {"query": name}
    async with AsyncClient() as client:
        req = await client.get(
            url="https://info.minigg.cn/weapons",
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/95.0.4638.69 Safari/537.36'},
            params=params
        )
    data = json.loads(req.text)
    return data


async def get_misc_info(mode, name):
    url = "https://info.minigg.cn/{}".format(mode)
    async with AsyncClient() as client:
        req = await client.get(
            url=url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/97.0.4692.71 Safari/537.36'},
            params={"query": name}
        )
    data = json.loads(req.text)
    return data


async def get_char_info(name, mode="char", level=None):
    url2 = None
    url3 = None
    data2 = None
    baseurl = "https://info.minigg.cn/characters?query="
    if mode == "talents":
        url = "https://info.minigg.cn/talents?query=" + name
    elif mode == "constellations":
        url = "https://info.minigg.cn/constellations?query=" + name
    elif mode == "costs":
        url = baseurl + name + "&costs=1"
        url2 = "https://info.minigg.cn/talents?query=" + name + "&costs=1"
        url3 = "https://info.minigg.cn/talents?query=" + name + "&matchCategories=true"
    elif level:
        url = baseurl + name + "&stats=" + level
    else:
        url = baseurl + name

    if url2:
        async with AsyncClient() as client:
            req = await client.get(
                url=url2,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/95.0.4638.69 Safari/537.36',
                    'Referer'   : 'https://genshin.minigg.cn/index.html'})
            data2 = json.loads(req.text)
            if "errcode" in data2:
                async with AsyncClient() as client_:
                    req = await client_.get(
                        url=url3,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                          'like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                            'Referer'   : 'https://genshin.minigg.cn/index.html'})
                    data2 = json.loads(req.text)

    async with AsyncClient() as client:
        req = await client.get(
            url=url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/95.0.4638.69 Safari/537.36',
                'Referer'   : 'https://genshin.minigg.cn/index.html'})
        try:
            data = json.loads(req.text)
            if "errcode" in data:
                async with AsyncClient() as client_:
                    req = await client_.get(
                        url=url + "&matchCategories=true",
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                          'like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                            'Referer'   : 'https://genshin.minigg.cn/index.html'})
                    data = json.loads(req.text)
        except:
            data = None
    return data if data2 is None else [data, data2]


async def get_genshin_events(mode="List"):
    if mode == "Calendar":
        now_time = datetime.datetime.now().strftime('%Y-%m-%d')
        base_url = "https://api-takumi.mihoyo.com/event/bbs_activity_calendar/getActList"
        params = {
            "time"    : now_time,
            "game_biz": "ys_cn",
            "page"    : 1,
            "tag_id"  : 0
        }
    else:
        base_url = "https://hk4e-api.mihoyo.com/common/hk4e_cn/announcement/api/getAnn{}".format(mode)
        params = {
            "game"     : "hk4e",
            "game_biz" : "hk4e_cn",
            "lang"     : "zh-cn",
            "bundle_id": "hk4e_cn",
            "platform" : "pc",
            "region"   : "cn_gf01",
            "level"    : 55,
            "uid"      : 100000000
        }

    async with AsyncClient() as client:
        req = await client.get(
            url=base_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/95.0.4638.69 Safari/537.36'},
            params=params
        )
    data = json.loads(req.text)
    return data