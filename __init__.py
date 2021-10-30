from .getImg import draw_pic,draw_abyss_pic,draw_abyss0_pic
from .getDB import connectDB,selectDB,cookiesDB,cacheDB,deletecache,CheckDB,TransDB,OpenPush,GetMysInfo,GetDaily,GetSignList,MysSign,GetSignInfo,OpCookies

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

daily_im = '''
==============
（还剩{}补充满）
==============
原粹树脂：{}/160
每日委托：{}/4
探索派遣：{}/{}
========
{}'''

@sv.scheduled_job('cron', hour='0')
async def delete():
    deletecache()

@sv.scheduled_job('cron', hour='0',minute="30")
async def dailysign():
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE StatusB != ?",("off",))
    c_data = cursor.fetchall()
    for row in c_data:
        
        im = await sign(str(row[0]))

        if row[4] == "on":
            await bot.send_private_msg(user_id = row[2],message = im)
        else:
            await bot.send_group_msg(group_id = row[4],message = f"[CQ:at,qq={row[2]}]" + "\n" + im)

@sv.scheduled_job('interval', minutes=30)
async def push():
    daily_data = await daily()
    if daily_data != None:
        for i in daily_data:
            if i['gid'] == "on":
                await bot.send_private_msg(user_id = i['qid'],message = i['message'])
            else:
                await bot.send_group_msg(group_id = i['gid'],message = f"[CQ:at,qq={i['qid']}]" + "\n" + i['message'])
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
            aid = re.search(r"account_id=(\d*)", mes)
            mysid_data = aid.group(0).split('=')
            mysid = mysid_data[1]
            cookie = ';'.join(filter(lambda x: x.split('=')[0] in ["cookie_token", "account_id"], [i.strip() for i in mes.split(';')]))
            mys_data = await GetMysInfo(mysid,cookie)
            mys_data = mys_data[0]
            for i in mys_data['data']['list']:
                if i['data'][0]['name'] != '活跃天数':
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            
            await cookiesDB(uid,cookie,userid)
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=f'添加Cookies成功！Cookies属于个人重要信息，如果你是在不知情的情况下添加，请马上修改米游社账户密码，保护个人隐私！')
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=f'校验失败！请输入正确的Cookies！')
    elif '开启推送' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"on","StatusA")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
    elif '关闭推送' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"off","StatusA")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
    elif '开启自动签到' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"on","StatusB")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
    elif '关闭自动签到' in message:
        try:
            uid = await selectDB(userid,mode = "uid")
            im = await OpenPush(int(uid[0]),userid,"off","StatusA")
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message=im)
        except:
            await bot.send_msg(self_id=sid, user_id=userid, group_id=gid, message="未找到uid绑定记录。")
        
@sv.on_prefix('开启')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "自动签到":
        try:
            gid = ev.group_id
            qid = ev.sender["user_id"]
            uid = await selectDB(ev.sender['user_id'],mode = "uid")
            im = await OpenPush(int(uid[0]),ev.sender['user_id'],str(gid),"StatusB")
            await bot.send(ev,im,at_sender=True)
        except:
            await bot.send(ev,"未绑定uid信息！",at_sender=True)
    elif m == "推送":
        try:
            gid = ev.group_id
            qid = ev.sender["user_id"]
            uid = await selectDB(ev.sender['user_id'],mode = "uid")
            im = await OpenPush(int(uid[0]),ev.sender['user_id'],str(gid),"StatusA")
            await bot.send(ev,im,at_sender=True)
        except:
            await bot.send(ev,"未绑定uid信息！",at_sender=True)

@sv.on_prefix('关闭')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "自动签到":
        try:
            gid = ev.group_id
            qid = ev.sender["user_id"]
            uid = await selectDB(ev.sender['user_id'],mode = "uid")
            im = await OpenPush(int(uid[0]),ev.sender['user_id'],"off","StatusB")
            await bot.send(ev,im,at_sender=True)
        except:
            await bot.send(ev,"未绑定uid信息！",at_sender=True)
    elif m == "推送":
        try:
            gid = ev.group_id
            qid = ev.sender["user_id"]
            uid = await selectDB(ev.sender['user_id'],mode = "uid")
            im = await OpenPush(int(uid[0]),ev.sender['user_id'],"off","StatusA")
            await bot.send(ev,im,at_sender=True)
        except:
            await bot.send(ev,"未绑定uid信息！",at_sender=True)

@sv.on_fullmatch('签到')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        qid = ev.sender["user_id"]
        uid = await selectDB(ev.sender['user_id'],mode = "uid")
        uid = uid[0]
        im = await sign(uid)
        await bot.send(ev,im,at_sender=True)
    except:
        pass

@sv.on_fullmatch('优化Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        im = await OpCookies()
        await bot.send(ev,im,at_sender=True)
    except:
        pass
    
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
        mes = await daily("ask",uid)
        im = mes[0]['message']
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




async def sign(uid):
    sign_data = await MysSign(uid)
    sign_info = await GetSignInfo(uid)
    sign_info = sign_info['data']
    sign_list = await GetSignList()
    status = sign_data['message']
    getitem = sign_list['data']['awards'][int(sign_info['total_sign_day'])-1]['name']
    getnum = sign_list['data']['awards'][int(sign_info['total_sign_day'])-1]['cnt']
    get_im = f"本次签到获得{getitem}x{getnum}"
    if status == "OK" and sign_info['is_sign'] == True:
        mes_im = "签到成功"
    else:
        mes_im = status
    sign_missed = sign_info['sign_cnt_missed']
    im = "\n" + mes_im +"!" + "\n" + get_im + "\n" + f"本月漏签次数：{sign_missed}"
    return im

async def daily(mode = "push",uid = None):
    temp_list = []
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    if mode == "push":
        cursor = c.execute("SELECT *  FROM NewCookiesTable WHERE StatusA != ?",("off",))
        c_data = cursor.fetchall()
    elif mode == "ask":
        c_data = ([uid,0,0,0,0,0,0],)

    for row in c_data:
        raw_data = await GetDaily(str(row[0]))
        dailydata = raw_data["data"]

        resin_num = dailydata["current_resin"]
        task_num = dailydata["finished_task_num"]
        travel_num = dailydata["current_expedition_num"]
        max_travel_num = dailydata["max_expedition_num"]
        travel_data = dailydata["expeditions"]

        if resin_num >= row[6] :

            re_time = dailydata["resin_recovery_time"]
            m, s = divmod(int(re_time), 60)
            h, m = divmod(m, 60)
            time = "%02d小时%02d分钟%02d秒" % (h, m, s)

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
            send_mes = daily_im.format(time,resin_num,task_num,travel_num,max_travel_num,travel_str)
            if row[1] != 0:
                send_mes = "你的树脂快满了！" + send_mes
            temp_list.append({"qid":row[2],"gid":row[3],"message":send_mes})
            return temp_list
