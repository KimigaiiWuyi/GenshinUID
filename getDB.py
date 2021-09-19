import sqlite3
import os

FILE_PATH = os.path.abspath(os.path.join(os.getcwd(), "../.."))
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