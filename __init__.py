from .getImg import draw_pic,draw_abyss_pic,draw_abyss0_pic
from .getDB import connectDB,selectDB,cookiesDB,cacheDB,deletecache,CheckDB,TransDB,OpenPush,GetMysInfo,GetDaily

from nonebot import *
from hoshino import Service,R,priv,util
from hoshino.typing import MessageSegment,CQEvent, HoshinoBot

import requests,random,os,json,re,time,datetime,string,base64

import hoshino
import asyncio
import hashlib
import sqlite3
from io import BytesIO
import urllib

sv = Service('genshinuid')
bot = get_bot()

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
Texture_PATH = os.path.join(FILE2_PATH,'texture2d')


@sv.scheduled_job('cron', hour='0')
async def delete():
    deletecache()

@sv.scheduled_job('interval', minutes=30)
async def push():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT *  FROM NewCookies WHERE StatusA != ?",("off",))
    c_data = cursor.fetchall()
    for row in c_data:
        raw_data = await GetDaily(str(row[1]))
        dailydata = raw_data["data"]
        resin_num = dailydata["current_resin"]
        if resin_num >= row[5]:
            re_time = dailydata["resin_recovery_time"]
            m, s = divmod(int(re_time), 60)
            h, m = divmod(m, 60)
            time = "%02d小时%02d分钟%02d秒" % (h, m, s)

            task_num = dailydata["finished_task_num"]
            travel_num = dailydata["current_expedition_num"]
            max_travel_num = dailydata["max_expedition_num"]
            travel_data = dailydata["expeditions"]

            travel_str = ''

            for i in travel_data:
                name = i["avatar_side_icon"].split('/')[-1].split('.')[0].split('_')[-1]
                statu = i['status']
                if statu == "Finished":
                    travel_str = travel_str + f"{name} : 完成\n"
                else:
                    remain_time = i['remained_time']
                    m1, s1 = divmod(int(remain_time), 60)
                    h1, m1 = divmod(m1, 60)
                    remain_time_str = "还剩%02d小时%02d分钟%02d秒" % (h1, m1, s1)
                    travel_str = travel_str + f"{name} : {remain_time_str}\n"
            im = f'''
==============
你的树脂快满了！！！
（还剩{time}补充满）
==============
原粹树脂：{resin_num}/160
每日委托：{task_num}/4
探索派遣：{travel_num}/{max_travel_num}
========
{travel_str}
'''.strip()

            if row[2] == "on":
                await bot.send_private_msg(user_id = row[4],message = im)
            else:
                await bot.send_group_msg(group_id = row[2],message = f"[CQ:at,qq={row[4]}]" + "\n" + im)
        else:
            pass

@bot.on_message('private')
async def setting(ctx):
    message = ctx['raw_message']
    sid=int(ctx["self_id"])
    userid=int(ctx["sender"]["user_id"])
    gid=0
    if '添加 ' in message:
        try:
            mes = message.replace('添加 ','')
            ltuid = re.search(r"ltuid=(\d*)", mes)
            mysid_data = ltuid.group(0).split('=')
            mysid = mysid_data[1]
            
            mys_data = await GetMysInfo(mysid,mes)
            mys_data = mys_data[0]
            uid = mys_data['data']['list'][0]['game_role_id']
            
            await cookiesDB(uid,mes)
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=f'添加Cookies成功！Cookies属于个人重要信息，如果你是在不知情的情况下添加，请马上修改米游社账户密码，保护个人隐私！')
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=f'校验失败！')
    elif '开启推送' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"on")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
    elif '关闭推送' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"off")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
        
@sv.on_fullmatch('开启推送')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        gid = ev.group_id
        qid = ev.sender["user_id"]
        uid = await selectDB(ev.sender['user_id'],mode = "uid")
        im = await OpenPush(int(uid[0]),ev.sender['user_id'],str(gid))
        await bot.send(ev,im,at_sender=True)
    except:
        await bot.send(ev,"未绑定uid信息！",at_sender=True)

@sv.on_fullmatch('关闭推送')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        gid = ev.group_id
        qid = ev.sender["user_id"]
        uid = await selectDB(ev.sender['user_id'],mode = "uid")
        im = await OpenPush(int(uid[0]),ev.sender['user_id'],"off")
        await bot.send(ev,im,at_sender=True)
    except:
        await bot.send(ev,"未绑定uid信息！",at_sender=True)

@sv.on_fullmatch('校验全部Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    im = await CheckDB()
    await bot.send(ev,im)   

@sv.on_fullmatch('迁移Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    im = await TransDB()
    await bot.send(ev,im)   
        
@sv.on_fullmatch('当前状态')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        uid = await selectDB(ev.sender['user_id'],mode = "uid")
        uid = uid[0]
        raw_data = await GetDaily(uid)
        dailydata = raw_data["data"]
        resin_num = dailydata["current_resin"]
        re_time = dailydata["resin_recovery_time"]
        m, s = divmod(int(re_time), 60)
        h, m = divmod(m, 60)
        time = "%02d小时%02d分钟%02d秒" % (h, m, s)

        task_num = dailydata["finished_task_num"]
        travel_num = dailydata["current_expedition_num"]
        max_travel_num = dailydata["max_expedition_num"]
        travel_data = dailydata["expeditions"]

        travel_str = ''

        for i in travel_data:
            name = i["avatar_side_icon"].split('/')[-1].split('.')[0].split('_')[-1]
            statu = i['status']
            if statu == "Finished":
                travel_str = travel_str + f"{name} : 完成\n"
            else:
                remain_time = i['remained_time']
                m1, s1 = divmod(int(remain_time), 60)
                h1, m1 = divmod(m1, 60)
                remain_time_str = "还剩%02d小时%02d分钟%02d秒" % (h1, m1, s1)
                travel_str = travel_str + f"{name} : {remain_time_str}\n"

        im = f'''
：
==============
（还剩{time}补充满）
==============
原粹树脂：{resin_num}/160
每日委托：{task_num}/4
探索派遣：{travel_num}/{max_travel_num}
========
{travel_str}
'''.strip()

    except:
        im = "没有找到绑定信息。"

    await bot.send(ev,im, at_sender=True)   
    

@sv.on_prefix('uid')
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image)
                await bot.send(ev, im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid,ev.sender['nickname'],image)
                await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'深渊输入错误！')
    elif m == "上期深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image,2,"2")
                await bot.send(ev, im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid,ev.sender['nickname'],image,2,"2")
                await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'深渊输入错误！')        
    else:
        try:
            im = await draw_pic(uid,ev.sender['nickname'],image,2)
            await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'输入错误！')

@sv.on_prefix('绑定uid')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    await connectDB(ev.sender['user_id'],uid)
    await bot.send(ev,'绑定uid成功！', at_sender=True)

@sv.on_prefix('绑定mys')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    mys = re.findall(r"\d+", message)[0]  # str
    await connectDB(ev.sender['user_id'],None,mys)
    await bot.send(ev,'绑定米游社id成功！', at_sender=True)

@sv.on_prefix('查询')
async def _(bot,  ev):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    at = re.search(r"\[CQ:at,qq=(\d*)\]", str(ev.raw_message.strip()))
    message = ev.message.extract_plain_text()
    if at:
        qid = at.group(1)
        mi =await bot.get_group_member_info(group_id=ev.group_id, user_id=qid)
        nickname = mi["nickname"]
        uid = await selectDB(qid)
    else:
        nickname = ev.sender['nickname']
        uid = await selectDB(ev.sender['user_id'])
        
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if uid:
        if m == "深渊":
            try:
                if len(re.findall(r"\d+", message)) == 1:
                    floor_num = re.findall(r"\d+", message)[0]
                    im = await draw_abyss_pic(uid[0],nickname,floor_num,image,uid[1])
                    await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid[0],nickname,image,uid[1])
                    await bot.send(ev, im, at_sender=True)
            except:
                await bot.send(ev,'输入错误！')
        elif m == "上期深渊":
            try:
                if len(re.findall(r"\d+", message)) == 1:
                    floor_num = re.findall(r"\d+", message)[0]
                    im = await draw_abyss_pic(uid[0],nickname,floor_num,image,uid[1],"2")
                    await bot.send(ev, im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid[0],nickname,image,uid[1],"2")
                    await bot.send(ev, im, at_sender=True)
            except:
                await bot.send(ev,'深渊输入错误！') 
        elif m == "":
            try:
                bg = await draw_pic(uid[0],nickname,image,uid[1])
                await bot.send(ev, bg, at_sender=True)
            except:
                await bot.send(ev,'输入错误！')
        else:
            pass
    else:
        await bot.send(ev,'未找到绑定记录！')


@sv.on_prefix('mys')
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image,3)
                await bot.send(ev, im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid,ev.sender['nickname'],image,3)
                await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'深渊输入错误！')
    elif m == "上期深渊":
        try:
            if len(re.findall(r"\d+", message)) == 1:
                floor_num = re.findall(r"\d+", message)[0]
                im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image,3,"2")
                await bot.send(ev, im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid,ev.sender['nickname'],image,3,"2")
                await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'深渊输入错误！') 
    else:
        try:
            im = await draw_pic(uid,ev.sender['nickname'],image,3)
            await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'输入错误！')

@sv.on_prefix('UID')
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    try:
        im = await draw_pic(uid,ev.sender['nickname'],image,1)
        await bot.send(ev, im, at_sender=True)
    except:
        await bot.send(ev,'输入错误！')

