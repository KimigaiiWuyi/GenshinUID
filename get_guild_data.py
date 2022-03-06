import sqlite3,time,traceback

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
        if c_data[0][0] == None and status == "open":
            temp_dict = [subgid]
        else:
            temp_dict = c_data[0][0].split(',')
            if status == "open" and subgid in temp_dict:
                return
            elif status == "open":
                temp_dict.append(subgid)
            else:
                temp_dict = list(filter(lambda x : x!=subgid,temp_dict))
                if temp_dict == []:
                    c.execute("UPDATE GuildList SET Permission = NULL WHERE GuildID=?",(gid,))
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