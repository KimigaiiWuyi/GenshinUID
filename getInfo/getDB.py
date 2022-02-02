import sqlite3,os,random,time,re,traceback
from shutil import copyfile

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
CHAR_PATH = os.path.join(FILE2_PATH,'chars')
CHAR_DONE_PATH = os.path.join(FILE2_PATH,'char_done')
CHAR_IMG_PATH = os.path.join(FILE2_PATH,'char_img')
REL_PATH = os.path.join(FILE2_PATH,'reliquaries')
INDEX_PATH = os.path.join(FILE2_PATH,'index')
CHAR_WEAPON_PATH = os.path.join(FILE2_PATH,'char_weapon')
TEXT_PATH = os.path.join(FILE2_PATH,'texture2d')
WEAPON_PATH = os.path.join(FILE2_PATH,'weapon')
BG_PATH = os.path.join(FILE2_PATH,'bg')

async def record(gname,gid,uname,uid,mes,reply):
    now = int(time.time())
    timeArray = time.localtime(now)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS MessageList
            (Time INT PRIMARY KEY     NOT NULL,
            TimeStr TEXT,
            GuildName   TEXT,
            GuildID  TEXT,
            UserName TEXT,
            UserID  TEXT,
            Msg     TEXT,
            Reply    TEXT);''')

    c.execute("INSERT OR IGNORE INTO MessageList (Time,TimeStr,GuildName,GuildID,UserName,UserID,Msg,Reply) \
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)",(now,otherStyleTime,gname,gid,uname,uid,mes,reply))
    
    conn.commit()
    conn.close()

async def check_switch(gid,func):
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        columns = [i[1] for i in c.execute('PRAGMA table_info(GuildList)')]

        if func not in columns:
            c.execute('ALTER TABLE GuildList ADD COLUMN {} TEXT'.format(func))

        cursor = c.execute("SELECT {}  FROM GuildList WHERE GuildID = ?".format(func),(gid,))
        c_data = cursor.fetchall()
        conn.commit()
        conn.close()
        if c_data[0][0] != "off":
            return True
        else:
            return False
    except Exception as e:
        traceback.print_exc()
        return False

async def subGuild_status(gid):
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        cursor = c.execute("SELECT Permission FROM GuildList WHERE GuildID = ?",(gid,))
        c_data = cursor.fetchall()
        conn.commit()
        conn.close()
        temp_dict = c_data[0][0].split(',')
        return temp_dict
    except Exception as e:
        traceback.print_exc()
        return False

async def check_subGuild_switch(gid,subgid):
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()

        columns = [i[1] for i in c.execute('PRAGMA table_info(GuildList)')]

        if "Permission" not in columns:
            c.execute('ALTER TABLE GuildList ADD COLUMN Permission TEXT')

        cursor = c.execute("SELECT Permission FROM GuildList WHERE GuildID = ?",(gid,))
        c_data = cursor.fetchall()
        conn.commit()
        conn.close()
        if c_data[0][0] == None:
            return True
        else:
            temp_dict = c_data[0][0].split(',')
            if subgid in temp_dict:
                return True
            else:
                return False
    except Exception as e:
        traceback.print_exc()
        return False

async def change_subGuild_switch(gid,subgid,status):
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        columns = [i[1] for i in c.execute('PRAGMA table_info(GuildList)')]

        if "Permission" not in columns:
            c.execute('ALTER TABLE GuildList ADD COLUMN Permission TEXT')
            
        cursor = c.execute("SELECT Permission FROM GuildList WHERE GuildID = ?",(gid,))
        c_data = cursor.fetchall()
        if c_data[0][0] == None:
            temp_dict = [subgid]
        else:
            temp_dict = c_data[0][0].split(',')
            if status == "open" and subgid in temp_dict:
                return
            elif status == "open":
                temp_dict.append(subgid)
            else:
                temp_dict = list(filter(lambda x : x!=subgid,temp_dict))
                if temp_dict == [""]:
                    c.execute("UPDATE GuildList SET Permission = ? WHERE GuildID=?",(None,gid))
                    conn.commit()
                    conn.close()
                    return

        status = ','.join(temp_dict)
        c.execute("UPDATE GuildList SET Permission = ? WHERE GuildID=?",(status,gid))
        conn.commit()
        conn.close()
        return
    except Exception as e:
        traceback.print_exc()
        return

async def change_switch(gid,func,status):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute("UPDATE GuildList SET {s} = ? WHERE GuildID=?".format(s = func),(status,gid))
    conn.commit()
    conn.close()

async def change_guild(mode,gid,gname):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS GuildList
                (GuildID TEXT PRIMARY KEY     NOT NULL,
                GuildName   TEXT,
                SearchRole  TEXT,
                LinkUID     TEXT,
                CharInfo    TEXT,
                WeaponInfo  TEXT,
                CostInfo    TEXT,
                TalentsInfo TEXT,
                PolarInfo   TEXT,
                guideInfo   TEXT,
                CardInfo    TEXT,
                GetLots     TEXT,
                AudioInfo   TEXT);''')
    if mode == "new":
        c.execute("INSERT OR IGNORE INTO GuildList (GuildID,GuildName) \
                            VALUES (?, ?)",(gid,gname))
    elif mode == "delete":
        c.execute("DELETE from GuildList where GuildID=?",(gid,))
    conn.commit()
    conn.close()
    
async def get_alots(qid):
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
    cursor = c.execute("SELECT * from UseridDict WHERE QID = ?",(qid,))
    c_data = cursor.fetchall()
    with open(os.path.join(INDEX_PATH,'lots.txt'),"r") as f:
        raw_data = f.read()
        raw_data = raw_data.replace(' ', "").split('-')

    if len(c_data) == 0:
        num = random.randint(1,len(raw_data)-1)
        data = raw_data[num]
        c.execute("INSERT OR IGNORE INTO UseridDict (QID,lots) \
                            VALUES (?, ?)",(qid,str(num)))
    else:
        if c_data[0][1] == None:
            num = random.randint(0,len(raw_data)-1)
            data = raw_data[num]
            c.execute("UPDATE UseridDict SET lots = ? WHERE QID=?",(str(num),qid))
        else:
            num = int(c_data[0][1])
            data = raw_data[num]       
    conn.commit()
    conn.close()
    return data

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
        if mode == 2:
            conn.create_function("REGEXP", 2, functionRegex)
            cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE REGEXP(Cookies, ?)",(uid,))
            d_data = cursor.fetchall()
 
        elif mode == 1:
            cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE UID = ?",(uid,))
            d_data = cursor.fetchall()

        if len(d_data) !=0 :
            if d_data[0][7] != "error":
                use = d_data[0][1]
                if mode == 1:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                            VALUES (?, ?)",(use,uid))
                elif mode == 2:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                            VALUES (?, ?)",(use,uid))
            else:
                cookiesrow = c.execute("SELECT * FROM NewCookiesTable WHERE Extra IS NULL ORDER BY RANDOM() LIMIT 1")
                e_data = cookiesrow.fetchall()
                if len(e_data) != 0:
                    if mode == 1:
                        c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                                VALUES (?, ?)",(e_data[0][1],uid))
                    elif mode == 2:
                        c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                                VALUES (?, ?)",(e_data[0][1],uid))
                    use = e_data[0][1]
                else:
                    return "没有可以使用的Cookies！"
        else:
            cookiesrow = c.execute("SELECT * FROM NewCookiesTable WHERE Extra IS NULL ORDER BY RANDOM() LIMIT 1")
            e_data = cookiesrow.fetchall()
            if len(e_data) != 0:
                if mode == 1:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,UID) \
                            VALUES (?, ?)",(e_data[0][1],uid))
                elif mode == 2:
                    c.execute("INSERT OR IGNORE INTO CookiesCache (Cookies,MYSID) \
                            VALUES (?, ?)",(e_data[0][1],uid))
                use = e_data[0][1]
            else:
                return "没有可以使用的Cookies！"
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

def functionRegex(value,patter):
    c_pattern = re.compile(r"account_id={}".format(patter))
    return c_pattern.search(value) is not None

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

async def deletecache():
    try:
        copyfile("ID_DATA.db", "ID_DATA_bak.db")
        print("————数据库成功备份————")
    except:
        print("————数据库备份失败————")
    
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        c.execute("DROP TABLE CookiesCache")
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Extra=?",(None,"limit30"))
        c.execute('''CREATE TABLE IF NOT EXISTS CookiesCache
        (UID TEXT PRIMARY KEY,
        MYSID         TEXT,
        Cookies       TEXT);''')
        conn.commit()
        conn.close()
        print("————UID查询缓存已清空————")
    except:
        print("\nerror\n")
    
    try:
        conn = sqlite3.connect('ID_DATA.db')
        c = conn.cursor()
        c.execute("UPDATE UseridDict SET lots=NULL")
        conn.commit()
        conn.close()
        print("————御神签缓存已清空————")
    except:
        print("\nerror\n")

async def errorDB(ck,err):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    if err == "error":
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Cookies=?",("error",ck))
    elif err == "limit30":
        c.execute("UPDATE NewCookiesTable SET Extra = ? WHERE Cookies=?",("limit30",ck))