import sqlite3
import sys

from httpx import AsyncClient

from nonebot import *
import requests,random,os,json,re
import hoshino
import asyncio
import time
import string
import hashlib
import base64

mhyVersion = "2.11.1"

FILE_PATH = os.path.abspath(os.path.join(os.getcwd(), "hoshino"))
DATA_PATH = os.path.join(FILE_PATH,'config')

async def OpenPush(uid,qid,status):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT * from NewCookies WHERE UID = ?",(uid,))
    c_data = cursor.fetchall()
    if len(c_data) != 0:
        try:
            c.execute("UPDATE NewCookies SET StatusA = ?,QID = ? WHERE UID=?",(status,qid,uid))
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
    cursor = c.execute("SELECT Cookies,UID  from NewCookies")
    for row in cursor:
        try:
            ltuid = re.search(r"ltuid=(\d*)", row[0])
            mysid_data = ltuid.group(0).split('=')
            mysid = mysid_data[1]
            
            mys_data = await GetMysInfo(mysid,row[0])
            mys_data = mys_data[0]
            uid = mys_data['data']['list'][0]['game_role_id']
            
            str = str + f"uid{row[1]}/mysid{mysid}的Cookies是正常的！\n"
        except:
            str = str + f"uid{row[1]}/mysid{mysid}的Cookies是异常的！已删除该条Cookies！\n"
            c.execute("DELETE from NewCookies where UID=？",(row[1],))
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
        c.execute('''CREATE TABLE IF NOT EXISTS NewCookies
            (Cookies TEXT PRIMARY KEY     NOT NULL,
            UID         INT,
            StatusA     TEXT,
            StatusB     TEXT,
            QID         INT,
            NUM         INT,
            Extra       TEXT);''')
        cursor = c.execute("SELECT * from CookiesTable")
        c_data = cursor.fetchall()
        for row in c_data:
            try:
                ltuid = re.search(r"ltuid=(\d*)", row[0])
                mysid_data = ltuid.group(0).split('=')
                mysid = mysid_data[1]
                mys_data = await GetMysInfo(mysid,row[0])
                mys_data = mys_data[0]
                uid = mys_data['data']['list'][0]['game_role_id']
                c.execute("INSERT OR IGNORE INTO NewCookies (Cookies,UID,StatusA,StatusB,NUM) \
                            VALUES (?, ?,?,?,?)",(row[0],uid,"off","off",140))
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
        cookiesrow = c.execute("SELECT * FROM NewCookies ORDER BY RANDOM() limit 1")
        for row2 in cookiesrow:
            if mode == 1:
                c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                        VALUES (?, ?)",(row2[0],uid))
            if mode == 2:
                c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                        VALUES (?, ?)",(row2[0],uid))
            use = row2[0]
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

async def cookiesDB(uid,Cookies):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS NewCookies
    (Cookies TEXT PRIMARY KEY     NOT NULL,
    UID         INT,
    StatusA     TEXT,
    StatusB     TEXT,
    QID         INT,
    NUM         INT,
    Extra       TEXT);''')

    c.execute("INSERT OR IGNORE INTO NewCookies (Cookies,UID,StatusA,StatusB,NUM) \
        VALUES (?, ?,?,?,?)",(Cookies,uid,"off","off",140))

    conn.commit()
    conn.close()

async def OwnerCookies(uid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()

    try:
        cursor = c.execute("SELECT *  FROM NewCookies WHERE UID = ?",(uid,))
        c_data = cursor.fetchall()
        cookies = c_data[0][0]
    except:
        return
    
    return cookies












def md5(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()

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
        sys.exit(1)

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
        sys.exit(1)


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
        sys.exit(1)

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
        print ("访问失败，请重试！")
        #sys.exit (1)
        return