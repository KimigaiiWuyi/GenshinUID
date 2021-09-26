import sqlite3
import os
import yaml
import random

FILE_PATH = os.path.abspath(os.path.join(os.getcwd(), "hoshino"))
DATA_PATH = os.path.join(FILE_PATH,'config')

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

async def selectDB(userid):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT *  FROM UIDDATA WHERE USERID = ?",(userid,))
    for row in cursor:
        if row[0]:
            if row[2]:
                return [row[2],3]
            elif row[1]:
                return [row[1],2]
            else:
                return None
        else:
            return None
            
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
        cookiesrow = c.execute("SELECT * FROM CookiesTable ORDER BY RANDOM() limit 1")
        #r = cookiesrow.fetchall()
        #random.randint(0,len(r))
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
            c.execute("UPDATE CookiesCache SET UID = ? WHERE MYSID=?",(uid,mys))
        
    conn.commit()
    conn.close()
    return use

async def cookiesDB(Cookies):
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS CookiesTable
        (Cookies TEXT PRIMARY KEY     NOT NULL);''')

    c.execute("INSERT OR IGNORE INTO CookiesTable (Cookies) \
        VALUES (?)",(Cookies,))

    conn.commit()
    conn.close()
