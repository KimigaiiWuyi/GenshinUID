from .getImg import draw_pic,draw_abyss_pic,draw_abyss0_pic
from .getDB import connectDB,selectDB,cookiesDB,cacheDB,deletecache,CheckDB,TransDB,OpenPush,GetMysInfo,GetDaily,GetSignList,MysSign,GetSignInfo,OpCookies,GetAward,GetWeaponInfo,GetCharInfo

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

month_im = '''
==============
本日获取原石：{}
本日获取摩拉：{}
==============
昨日获取原石：{}
昨日获取摩拉：{}
==============
本月获取原石：{}
本月获取摩拉：{}
==============
上月获取原石：{}
上月获取摩拉：{}
==============
{}========
'''

weapon_im = '''
名称：{}
类型：{}
稀有度：{}
介绍：{}
攻击力：{}
{}：{}
{}
'''

char_info_im ='''
{}
稀有度：{}
武器：{}
元素：{}
突破加成：{}
生日：{}
命之座：{}
cv：{}
介绍：{}
'''

@sv.on_prefix('武器')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    im = await weapon_wiki(message)
    await bot.send(ev,im,at_sender=True)

@sv.on_prefix('角色')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    im = await char_wiki(message)
    await bot.send(ev,im,at_sender=True)

@sv.on_prefix('命座')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    num = int(re.findall(r"\d+", message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    im = await char_wiki(m,2,num)
    await bot.send(ev,im,at_sender=True)
    
#每日零点清空cookies使用缓存
@sv.scheduled_job('cron', hour='0')
async def delete():
    deletecache()
    
#每日零点半进行米游社签到
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
            
#每隔半小时检测树脂是否超过设定值
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

#私聊事件
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

#群聊开启 自动签到 和 推送树脂提醒 功能
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
            
#群聊关闭 自动签到 和 推送树脂提醒 功能
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
            
#群聊内 每月统计 功能
@sv.on_fullmatch('每月统计')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        qid = ev.sender["user_id"]
        uid = await selectDB(ev.sender['user_id'],mode = "uid")
        uid = uid[0]
        data = await GetAward(uid)
        nickname = data['data']['nickname']
        day_stone = data['data']['day_data']['current_primogems']
        day_mora = data['data']['day_data']['current_mora']
        lastday_stone = data['data']['day_data']['last_primogems']
        lastday_mora = data['data']['day_data']['last_mora']
        month_stone = data['data']['month_data']['current_primogems']
        month_mora = data['data']['month_data']['current_mora']
        lastmonth_stone = data['data']['month_data']['last_primogems']
        lastmonth_mora = data['data']['month_data']['last_mora']
        group_str = ''
        for i in data['data']['month_data']['group_by']:
            group_str = group_str + i['action'] + ":" + str(i['num']) + "| " + "百分比：" + str(i['percent']) + "%" + '\n'

        im = month_im.format(day_stone,day_mora,lastday_stone,lastday_mora,month_stone,month_mora,lastmonth_stone,lastmonth_mora,group_str)
        await bot.send(ev,im,at_sender=True)
    except:
        pass
        
#群聊内 签到 功能
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

#群聊内 数据库v2 迁移至 数据库v3 的命令，一般只需要更新时执行一次
@sv.on_fullmatch('优化Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    try:
        im = await OpCookies()
        await bot.send(ev,im,at_sender=True)
    except:
        pass

#群聊内 校验Cookies 是否正常的功能，不正常自动删掉
@sv.on_fullmatch('校验全部Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    im = await CheckDB()
    await bot.send(ev,im)   

#群聊内 数据库v1 迁移至 数据库v2 的命令，一般只需要更新时执行一次
@sv.on_fullmatch('迁移Cookies')
async def _(bot:HoshinoBot,  ev: CQEvent):
    im = await TransDB()
    await bot.send(ev,im)   

#群聊内 查询当前树脂状态以及派遣状态 的命令
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
    
#群聊内 查询uid 的命令
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
            
#群聊内 绑定uid 的命令，会绑定至当前qq号上
@sv.on_prefix('绑定uid')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    await connectDB(ev.sender['user_id'],uid)
    await bot.send(ev,'绑定uid成功！', at_sender=True)
    
#群聊内 绑定米游社通行证 的命令，会绑定至当前qq号上，和绑定uid不冲突，两者可以同时绑定
@sv.on_prefix('绑定mys')
async def _(bot:HoshinoBot,  ev: CQEvent):
    message = ev.message.extract_plain_text()
    mys = re.findall(r"\d+", message)[0]  # str
    await connectDB(ev.sender['user_id'],None,mys)
    await bot.send(ev,'绑定米游社id成功！', at_sender=True)

#群聊内 绑定过uid/mysid的情况下，可以查询，默认优先调用米游社通行证，多出世界等级一个参数
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

#群聊内 查询米游社通行证 的命令
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

#群聊内 查询uid 的命令（旧版），不输出武器信息
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



#签到函数
async def sign(uid):
    try:
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
    except:
        im = "\n签到失败，请检查Cookies是否失效。"
    return im

#统计状态函数
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

async def weapon_wiki(name):
    data = await GetWeaponInfo(name)
    name = data['name']
    type = data['weapontype']
    star = data['rarity'] + "星"
    info = data['description']
    atk = str(data['baseatk'])
    sub_name = data['substat']
    sub_val = (data['subvalue'] + '%') if sub_name != '元素精通' else data['subvalue']
    raw_effect = data['effect']
    rw_ef = []
    for i in range(len(data['r1'])):
        now =  ''
        for j in range(1,6):
            now = now + data['r{}'.format(j)][i] + "/"
        now = now[:-1]
        rw_ef.append(now)
    raw_effect = raw_effect.format(*rw_ef)
    effect = data['effectname'] + "：" + raw_effect
    im = weapon_im.format(name,type,star,info,atk,sub_name,sub_val,effect)
    return im

async def char_wiki(name,mode = 0,num = 0):
    data = await GetCharInfo(name,mode)
    if mode == 0:
        name = data['title'] + ' — ' + data['name']
        star = data['rarity']
        type = data["weapontype"]
        element = data['element']
        up_val = data['substat']
        bdday = data['birthday']
        polar = data['constellation']
        cv = data['cv']['chinese']
        info = data['description']
        im = char_info_im.format(name,star,type,element,up_val,bdday,polar,cv,info)
    elif mode == 1:
        im = '暂不支持'
    elif mode == 2:
        im = data["c{}".format(num)]['name'] + "：" + data["c{}".format(num)]['effect']
    return im
