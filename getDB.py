import sqlite3
import sys

from httpx import AsyncClient

from nonebot import *
import requests,random,os,json,re
import asyncio
import time
import string
import hashlib
import base64

mhyVersion = "2.11.1"

FILE_PATH = os.path.abspath(os.path.join(os.getcwd(), "hoshino"))
BASE_PATH = os.path.dirname(__file__)
BASE2_PATH = os.path.join(BASE_PATH,'mys')
INDEX_PATH = os.path.join(BASE2_PATH,'index')

async def OpenPush(uid,qid,status,mode):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT * from NewCookiesTable WHERE UID = ?",(uid,))
    c_data = cursor.fetchall()
    if len(c_data) != 0:
        try:
            c.execute("UPDATE NewCookiesTable SET {s} = ?,QID = ? WHERE UID=?".format(s = mode),(status,qid,uid))
            conn.commit()
            conn.close()
            return "成功！"
        except:
            return "未找到Ck绑定记录。"
    else:
        return "未找到Ck绑定记录。"

async def CheckDB():
    str = ''
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT UID,Cookies  from NewCookiesTable")
    c_data = cursor.fetchall()
    for row in c_data:
        try:
            aid = re.search(r"account_id=(\d*)",row[1])
            mysid_data = aid.group(0).split('=')
            mysid = mysid_data[1]
            mys_data = await GetMysInfo(mysid,row[1])
            mys_data = mys_data[0]
            uid = mys_data['data']['list'][0]['game_role_id']
            str = str + f"uid{row[0]}/mysid{mysid}的Cookies是正常的！\n"
        except:
            str = str + f"uid{row[0]}的Cookies是异常的！已删除该条Cookies！\n"
            c.execute("DELETE from NewCookiesTable where UID=?",(row[0],))
            test = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = 'CookiesCache'")
            if test == 0:
                pass
            else:
                c.execute("DELETE from CookiesCache where Cookies=?",(row[1],))
    conn.commit()
    conn.close()
    return str

async def TransDB():
    str = ''
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    test = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = 'CookiesTable'")
    if test == 0:
        conn.commit()
        conn.close()
        return "你没有需要迁移的数据库。"
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS NewCookiesTable
            (UID INT PRIMARY KEY     NOT NULL,
            Cookies     TEXT,
            QID         INT,
            StatusA     TEXT,
            StatusB     TEXT,
            StatusC     TEXT,
            NUM         INT,
            Extra       TEXT);''')
        cursor = c.execute("SELECT * from CookiesTable")
        c_data = cursor.fetchall()
        for row in c_data:
            try:
                newcookies = ';'.join(filter(lambda x: x.split('=')[0] in ["cookie_token", "account_id"], [i.strip() for i in row[0].split(';')]))
                aid = re.search(r"account_id=(\d*)", row[0])
                mysid_data = aid.group(0).split('=')
                mysid = mysid_data[1]
                mys_data = await GetMysInfo(mysid,row[0])
                mys_data = mys_data[0]
                uid = mys_data['data']['list'][0]['game_role_id']
                c.execute("INSERT OR IGNORE INTO NewCookiesTable (Cookies,UID,StatusA,StatusB,StatusC,NUM) \
                            VALUES (?, ?,?,?,?,?)",(newcookies,uid,"off","off","off",140))
                str = str + f"uid{uid}/mysid{mysid}的Cookies已转移成功！\n"
            except:
                str = str + f"uid{uid}/mysid{mysid}的Cookies是异常的！已删除该条Cookies！\n"
        conn.commit()
        conn.close()
        return str

async def connectDB(userid,uid = None,mys = None):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS UIDDATA
        (USERID INT PRIMARY KEY     NOT NULL,
        UID         TEXT,
        MYSID       TEXT);''')

    c.execute("INSERT OR IGNORE INTO UIDDATA (USERID,UID,MYSID) \
    VALUES (?, ?,?)",(userid,uid,mys))

    if uid:
        c.execute("UPDATE UIDDATA SET UID = ? WHERE USERID=?",(uid,userid))
    if mys:
        c.execute("UPDATE UIDDATA SET MYSID = ? WHERE USERID=?",(mys,userid))

    conn.commit()
    conn.close()

async def selectDB(userid,mode = "auto"):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT *  FROM UIDDATA WHERE USERID = ?",(userid,))
    for row in cursor:
        if mode == "auto":
            if row[0]:
                if row[2]:
                    return [row[2],3]
                elif row[1]:
                    return [row[1],2]
                else:
                    return None
            else:
                return None
        elif mode == "uid":
            return [row[1],2]
        elif mode == "mys":
            return [row[2],3]
            
def deletecache():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute("DROP TABLE CookiesCache")
    conn.commit()
    conn.close()

async def cacheDB(uid,mode = 1,mys = None):
    use = ''
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS CookiesCache
        (UID TEXT PRIMARY KEY,
        MYSID         TEXT,
        Cookies       TEXT);''')
        
    if mode == 1:
        if mys:
            cursor = c.execute("SELECT *  FROM CookiesCache WHERE MYSID = ?",(mys,))
            c_data = cursor.fetchall()
        else:
            cursor = c.execute("SELECT *  FROM CookiesCache WHERE UID = ?",(uid,))
            c_data = cursor.fetchall()
    elif mode == 2:
        cursor = c.execute("SELECT *  FROM CookiesCache WHERE MYSID = ?",(uid,))
        c_data = cursor.fetchall()
        
    if len(c_data)==0:
        cookiesrow = c.execute("SELECT * FROM NewCookiesTable ORDER BY RANDOM() limit 1")
        for row2 in cookiesrow:
            if mode == 1:
                c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                        VALUES (?, ?)",(row2[1],uid))
            if mode == 2:
                c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                        VALUES (?, ?)",(row2[1],uid))
            use = row2[1]
    else:
        use = c_data[0][2]
        if mys:
            try:
                c.execute("UPDATE CookiesCache SET UID = ? WHERE MYSID=?",(uid,mys))
            except:
                c.execute("UPDATE CookiesCache SET MYSID = ? WHERE UID=?",(mys,uid))
        
    conn.commit()
    conn.close()
    return use

async def cookiesDB(uid,Cookies,qid):
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
    
    cursor = c.execute("SELECT * from NewCookiesTable WHERE UID = ?",(uid,))
    c_data = cursor.fetchall()
    if len(c_data) == 0 :
        c.execute("INSERT OR IGNORE INTO NewCookiesTable (Cookies,UID,StatusA,StatusB,StatusC,NUM,QID) \
            VALUES (?, ?,?,?,?,?,?)",(Cookies,uid,"off","off","off",140,qid))
    else:
        c.execute("UPDATE NewCookiesTable SET Cookies = ? WHERE UID=?",(Cookies,uid))

    conn.commit()
    conn.close()

async def OpCookies():
    str = ""
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    test = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = 'NewCookies'")
    if test == 0:
        conn.commit()
        conn.close()
        return "你没有需要优化的数据库。"
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS NewCookiesTable
            (UID INT PRIMARY KEY     NOT NULL,
            Cookies     TEXT,
            QID         INT,
            StatusA     TEXT,
            StatusB     TEXT,
            StatusC     TEXT,
            NUM         INT,
            Extra       TEXT);''')
        cursor = c.execute("SELECT * from NewCookies")
        c_data = cursor.fetchall()
        for row in c_data:
            try:
                newcookies = ';'.join(filter(lambda x: x.split('=')[0] in ["cookie_token", "account_id"], [i.strip() for i in row[0].split(';')]))
                aid = re.search(r"account_id=(\d*)", row[0])
                mysid_data = aid.group(0).split('=')
                mysid = mysid_data[1]
                mys_data = await GetMysInfo(mysid,row[0])
                mys_data = mys_data[0]
                uid = mys_data['data']['list'][0]['game_role_id']
                c.execute("INSERT OR IGNORE INTO NewCookiesTable (Cookies,UID,StatusA,StatusB,StatusC,QID,NUM) \
                            VALUES (?, ?,?,?,?,?,?)",(newcookies,row[1],row[2],row[3],"off",row[4],row[5]))
                str = str + f"uid{row[1]}的Cookies已转移成功！\n"
            except:
                str = str + f"uid{row[1]}的Cookies是异常的！已删除该条Cookies！\n"
        conn.commit()
        conn.close()
        return str
            
    
async def OwnerCookies(uid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    try:
        cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE UID = ?",(uid,))
        c_data = cursor.fetchall()
        cookies = c_data[0][1]
    except:
        return
    
    return cookies










def random_hex(length):
    result = hex(random.randint(0,16**length)).replace('0x','').upper()
    if len(result)<length:
        result = "0"*(length-len(result))+result
    return result

def md5(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()

def oldDSGet():
    n = "h8w582wxwgqvahcdkpvdhbh2w9casgfl"
    i = str(int(time.time()))
    r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
    c = md5("salt=" + n + "&t=" + i + "&r=" + r)
    return (i + "," + r + "," + c)
    
def DSGet(q = "",b = None):
    if b:
        br = json.dumps(b)
    else:
        br = ""
    s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r + "&b=" + br + "&q=" + q)
    return t + "," + r + "," + c

async def GetDaily(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/dailyNote?server=" + ServerID + "&role_id=" + Uid,
                headers={
                    'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": await OwnerCookies(Uid)})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")
        sys.exit(1)

async def GetSignList():
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/home?act_id=e202009291139501",
                headers={
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")

async def GetSignInfo(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/event/bbs_sign_reward/info?act_id=e202009291139501&region=" + ServerID + "&uid=" + Uid,
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie": await OwnerCookies(Uid),
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")
        
async def MysSign(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        req = requests.post(
            url = "https://api-takumi.mihoyo.com/event/bbs_sign_reward/sign",
            headers={
                'User_Agent': 'Mozilla/5.0 (Linux; Android 10; MIX 2 Build/QKQ1.190825.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/83.0.4103.101 Mobile Safari/537.36 miHoYoBBS/2.3.0',
                "Cookie": await OwnerCookies(Uid),
                "x-rpc-device_id":random_hex(32),
                'Origin': 'https://webstatic.mihoyo.com',
                'X_Requested_With': 'com.mihoyo.hyperion',
                'DS': oldDSGet(),
                'x-rpc-client_type': '5',
                'Referer': 'https://webstatic.mihoyo.com/bbs/event/signin-ys/index.html?bbs_auth_required=true&act_id=e202009291139501&utm_source=bbs&utm_medium=mys&utm_campaign=icon',
                'x-rpc-app_version': '2.3.0'
            },
            json = {"act_id": "e202009291139501" ,"uid": Uid ,"region": ServerID}
        )
        data2 = json.loads(req.text)
        return data2
    except:
        print("访问失败，请重试！")
    
async def GetAward(Uid,ServerID="cn_gf01"):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://hk4e-api.mihoyo.com/event/ys_ledger/monthInfo?month={}&bind_uid={}&bind_region={}&bbs_presentation_style=fullscreen&bbs_auth_required=true&utm_source=bbs&utm_medium=mys&utm_campaign=icon".format("0",Uid,ServerID),
                headers={
                    'x-rpc-app_version': mhyVersion,
                    "Cookie": await OwnerCookies(Uid),
                    'DS': oldDSGet(),
                    "x-rpc-device_id":random_hex(32),
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")
        #sys.exit(1)

async def GetInfo(Uid,ServerID="cn_gf01",Schedule_type="1",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/index?role_id=" + Uid + "&server=" + ServerID,
                headers={
                    'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": await cacheDB(Uid,1,mysid)})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")
        #sys.exit(1)

async def GetSpiralAbyssInfo(Uid, ServerID="cn_gf01",Schedule_type="1",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/spiralAbyss?schedule_type=" + Schedule_type + "&server="+ ServerID +"&role_id=" + Uid,
                headers={
                    'DS': DSGet("role_id=" + Uid + "&schedule_type=" + Schedule_type + "&server="+ ServerID),
                    'Origin': 'https://webstatic.mihoyo.com',
                    'Cookie': await cacheDB(Uid,1,mysid),                
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/'
                    }
                )
            data = json.loads(req.text)
        return data
    except:
        print("1访问失败，请重试！")
        #sys.exit(1)


async def GetCharacter(Uid,Character_ids, ServerID="cn_gf01",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        req = requests.post(
            url = "https://api-takumi.mihoyo.com/game_record/app/genshin/api/character",
            headers={
                'DS': DSGet('',{"character_ids": Character_ids ,"role_id": Uid ,"server": ServerID}),
                'Origin': 'https://webstatic.mihoyo.com',
                'Cookie': await cacheDB(Uid,1,mysid),
                'x-rpc-app_version': mhyVersion,
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                'x-rpc-client_type': '5',
                'Referer': 'https://webstatic.mihoyo.com/'
            },
            json = {"character_ids": Character_ids ,"role_id": Uid ,"server": ServerID}
        )
        data2 = json.loads(req.text)
        return data2
    except:
        print("访问失败，请重试！")
        #sys.exit(1)

async def GetMysInfo(mysid,cookies = None):
    if cookies:
        ck = cookies
    else:
        ck = await cacheDB(mysid,2)
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid=" + mysid,
                headers={
                    'DS': DSGet("uid="+mysid),
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    "Cookie": ck})
            data = json.loads(req.text)
        return [data,mysid]
    except:
        im = "err"
        return im
        
async def GetWeaponInfo(name):
    async with AsyncClient() as client:
        req = await client.get(
            url="https://genshin.minigg.cn/?weapon=" + name,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'Referer': 'https://genshin.minigg.cn/index.html'})
        data = json.loads(req.text)
    return data

async def GetCharInfo(name,mode = 0):
    str = ""
    if mode == 1:
        str = "&talents=1"
    elif mode == 2:
        str = "&constellations=1"
        
    async with AsyncClient() as client:
        req = await client.get(
            url="https://genshin.minigg.cn/?char=" + name + str,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
                'Referer': 'https://genshin.minigg.cn/index.html'})
        data = json.loads(req.text)
    return data