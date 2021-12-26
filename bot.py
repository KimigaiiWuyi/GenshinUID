import re,os,random,sqlite3,sys,datetime,math
import base64
from apscheduler.schedulers.background import BackgroundScheduler
from shutil import copyfile
import urllib.parse

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from getDB import (connectDB, cookiesDB, deletecache, selectDB, get_alots, cacheDB, errorDB, add_guild, check_switch,record,change_switch)
from getData import (GetCharTalentsInfo,GetInfo,GetWeaponInfo,GetCharInfo,GetUidPic,GetMysInfo)
from getImg import (draw_event_pic)

import qqbot
from qqbot.model.guild import Guild
from qqbot.model.message import (
    MessageSendRequest,
    Message,
    CreateDirectMessageRequest,
    DirectMessageGuild,
)
from qqbot.core.util import logging

logger = logging.getLogger(__name__)

token = qqbot.Token("","")

api = qqbot.UserAPI(token, False)
guild_api = qqbot.GuildAPI(token,False)
msg_api = qqbot.MessageAPI(token, False)
user = api.me()
print(user.username)

switch_list = {
    "uid":"SearchRole",
    "mys":"SearchRole",
    "绑定uid":"LinkUID",
    "绑定mys":"LinkUID",
    "角色":"CharInfo",
    "武器":"WeaponInfo",
    "材料":"CostInfo",
    "天赋":"TalentsInfo",
    "命座":"PolarInfo",
    "攻略":"guideInfo",
    "信息":"CardInfo",
    "御神签":"GetLots"
}

weapon_im = '''【名称】：{}
【类型】：{}
【稀有度】：{}
【介绍】：{}
【攻击力】：{}{}{}'''

char_info_im = '''{}
【稀有度】：{}
【武器】：{}
【元素】：{}
【突破加成】：{}
【生日】：{}
【命之座】：{}
【cv】：{}
【介绍】：{}'''

def check_startwish(raw_mes,key_word,gid):
    if raw_mes.startswith(key_word) and check_switch(gid,switch_list[key_word]):
        return True
    else:
        return False

def up_guild_list():
    guild_list = api.me_guilds()
    for guild in guild_list:
        #guild_data = guild_api.guild(guild.id)
        add_guild(guild.id,guild.name)

up_guild_list()

def _message_handler(event, message: Message):
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)

    guild_data = guild_api.guild(message.guild_id)
    at_mes = re.search(r'\<\@\![0-9]+\>',message.content)
    raw_mes = message.content.replace(at_mes.group(),"").replace(" ","")
    record_mes = raw_mes
    
    mes = None
    image = None

    if raw_mes == "频道信息":
        mes = getGuildStatus()
    elif raw_mes.startswith("开启"):
        raw_mes = raw_mes.replace("开启","")
        try:
            change_switch(message.guild_id,switch_list[raw_mes],"on")
            mes = "成功。"
        except Exception as e:
            print(e.with_traceback)
            mes = "发生错误，可能是输入的功能名不正确。"
    elif raw_mes.startswith("关闭"):
        raw_mes = raw_mes.replace("关闭","")
        try:
            change_switch(message.guild_id,switch_list[raw_mes],"off")
            mes = "成功。"
        except Exception as e:
            print(e.with_traceback)
            mes = "发生错误，可能是输入的功能名不正确。"
    elif check_startwish(raw_mes,"uid",message.guild_id):
        raw_mes = raw_mes.replace("uid","")
        try:
            uid = re.findall(r"[0-9]+", raw_mes)[0]
            if len(uid) != 9:
                mes = "你输入了错误的uid，请检查输入是否正确。"
            else:
                image = GetUidUrl(uid,message.author.id,message.author.username)
        except:
            mes = "未知错误。"
    elif check_startwish(raw_mes,"mys",message.guild_id):
        raw_mes = raw_mes.replace("mys","")
        try:
            uid = re.findall(r"[0-9]+", raw_mes)[0]
            image = GetUidUrl(uid,message.author.id,message.author.username,mode=3)
        except:
            mes = "未知错误。"
    #elif raw_mes.startswith("活动列表"):
        #draw_event_pic()
    #    pass
    elif check_startwish(raw_mes,"绑定uid",message.guild_id):
        uid = raw_mes.replace("绑定uid","")
        try:
            connectDB(userid = message.author.id,uid = uid)
            mes = "绑定uid成功。"
        except:
            mes = "绑定失败。"
    elif check_startwish(raw_mes,"绑定mys",message.guild_id):
        uid = raw_mes.replace("绑定mys","")
        try:
            connectDB(userid = message.author.id,mys = uid)
            mes = "绑定mysid成功。"
        except:
            mes = "绑定失败。"
    elif check_startwish(raw_mes,"角色",message.guild_id):
        raw_mes = raw_mes.replace("角色","")
        name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
        level = re.findall(r"[0-9]+", raw_mes)
        if len(level) == 1:
            mes = char_wiki(name,extra="stats",num=level[0])
        else:
            mes = char_wiki(name)
    elif check_startwish(raw_mes,"武器",message.guild_id):
        name = raw_mes.replace("武器","")
        mes = weapon_wiki(name)
    elif check_startwish(raw_mes,"材料",message.guild_id):
        name = raw_mes.replace("材料","")
        mes = char_wiki(name,extra="cost")
    elif check_startwish(raw_mes,"天赋",message.guild_id):
        raw_mes = raw_mes.replace("天赋","")
        name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
        num = re.findall(r"[0-9]+", raw_mes)
        if len(num) == 1:
            mes = talents_wiki(name,num[0])
        else:
            mes = "参数不正确。"
    elif check_startwish(raw_mes,"命座",message.guild_id):
        raw_mes = raw_mes.replace("命座","")
        name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
        num = re.findall(r"[0-9]+", raw_mes)
        if len(num) == 1:
            mes = char_wiki(name,2,num[0])
        else:
            mes = "参数不正确。"
    elif check_startwish(raw_mes,"攻略",message.guild_id):
        raw_mes = raw_mes.replace("攻略","")
        name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
        image = "https://img.genshin.minigg.cn/guide/{}.jpg".format(urllib.parse.quote(name, safe=''))
    elif check_startwish(raw_mes,"信息",message.guild_id):
        raw_mes = raw_mes.replace("信息","")
        name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
        image = "https://img.genshin.minigg.cn/info/{}.jpg".format(urllib.parse.quote(name, safe=''))

    elif raw_mes == "御神签" and check_switch(message.guild_id,switch_list["御神签"]):
        raw_data = get_alots(message.author.id)
        mes = base64.b64decode(raw_data).decode("utf-8")

    if image:
        try:
            send = qqbot.MessageSendRequest(content = "",image = image, msg_id = message.id)
            msg_api.post_message(message.channel_id, send)
        except Exception as e:
            logger.info(e.args)
            send = qqbot.MessageSendRequest(str(e), message.id)
            msg_api.post_message(message.channel_id, send)
        record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,image)
    elif mes:
        try:
            send = qqbot.MessageSendRequest(mes, message.id)
            msg_api.post_message(message.channel_id, send)
        except Exception as e:
            logger.info(e.args)
            send = qqbot.MessageSendRequest(str(e), message.id)
            msg_api.post_message(message.channel_id, send)
        record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
    else:
        mes = "你可能发送了错误的指令或参数不正确,或者使用了未开启的功能，请查看帮助。"
        send = qqbot.MessageSendRequest(mes, message.id)
        msg_api.post_message(message.channel_id, send)
        record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
    return

def _guild_handler(event, guild:Guild):
    up_guild_list()

qqbot_handler2 = qqbot.Handler(qqbot.HandlerType.GUILD_EVENT_HANDLER, _guild_handler)
qqbot_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
qqbot.listen_events(token, False, qqbot_handler)
qqbot.listen_events(token, False, qqbot_handler2)

def getGuildStatus():
    guild_list = api.me_guilds()
    guild_member_all_count = 0
    guild_status_mes  = ""
    for guild in guild_list:
        guild_data = guild_api.guild(guild.id)
        guild_status_mes += "【{}】{}人\n".format(guild.name,str(guild_data.member_count))
        guild_member_all_count += guild_data.member_count
    guild_status_mes += "【{}】总加入频道 {} 个,总人数为 {}".format(user.username,str(len(guild_list)),str(guild_member_all_count))
    return guild_status_mes

def weapon_wiki(name):
    data = GetWeaponInfo(name)
    name = data['name']
    type = data['weapontype']
    star = data['rarity'] + "星"
    info = data['description']
    atk = str(data['baseatk'])
    sub_name = data['substat']
    if data['subvalue'] != "":
        sub_val = (data['subvalue'] +
                '%') if sub_name != '元素精通' else data['subvalue']
        sub = "\n" + "【" + sub_name + "】" + sub_val
    else:
        sub = ""

    if data['effectname'] != "":
        raw_effect = data['effect']
        rw_ef = []
        for i in range(len(data['r1'])):
            now = ''
            for j in range(1, 6):
                now = now + data['r{}'.format(j)][i] + "/"
            now = now[:-1]
            rw_ef.append(now)
        raw_effect = raw_effect.format(*rw_ef)
        effect = "\n" + "【" + data['effectname'] + "】" + "：" + raw_effect
    else:
        effect = ""
    im = weapon_im.format(name, type, star, info, atk,
                          sub, effect)
    return im


def char_wiki(name, mode=0, num="", extra=""):
    data = GetCharInfo(name, mode)
    try:
        if mode == 0:
            if isinstance(data,str):
                raw_data = data.replace("[","").replace("\n","").replace("]","").replace(" ","").replace("'","").split(',')
                if data.replace("\n","").replace(" ","") == "undefined":
                    im = "不存在该角色或类型。"
                else:
                    im = ','.join(raw_data)
            else:
                if extra == "cost":
                    talent_data = GetCharInfo(name, 1)

                    im = "【天赋材料(一份)】\n{}\n【突破材料】\n{}"
                    im1 = ""
                    im2 = ""
                    
                    talent_temp = {}
                    talent_cost = talent_data["costs"]
                    for i in talent_cost.values():
                        for j in i:
                            if j["name"] not in talent_temp:
                                talent_temp[j["name"]] = j["count"]
                            else:
                                talent_temp[j["name"]] = talent_temp[j["name"]] + j["count"]
                    for k in talent_temp:
                        im1 = im1 + k + ":" + str(talent_temp[k]) + "\n"

                    temp = {}
                    cost = data["costs"]
                    for i in range(1,7):
                        for j in cost["ascend{}".format(i)]:
                            if j["name"] not in temp:
                                temp[j["name"]] = j["count"]
                            else:
                                temp[j["name"]] = temp[j["name"]] + j["count"]
                                
                    for k in temp:
                        im2 = im2 + k + ":" + str(temp[k]) + "\n"
                    
                    im = im.format(im1,im2)

                elif extra == "stats":
                    data2 = GetCharInfo(name, mode, num)
                    im = (name + "\n等级：" + str(data2["level"]) + "\n血量：" + str(math.floor(data2["hp"])) +
                        "\n攻击力：" + str(math.floor(data2["attack"])) + "\n防御力：" + str(math.floor(data2["defense"])) +
                        "\n" + data["substat"] + "：" + '%.1f%%' % (data2["specialized"] * 100))
                else:
                    name = data['title'] + ' — ' + data['name']
                    star = data['rarity']
                    type = data["weapontype"]
                    element = data['element']
                    up_val = data['substat']
                    bdday = data['birthday']
                    polar = data['constellation']
                    cv = data['cv']['chinese']
                    info = data['description']
                    im = char_info_im.format(
                        name, star, type, element, up_val, bdday, polar, cv, info)
        elif mode == 1:
            im = '暂不支持'
        elif mode == 2:
            im = "【" + data["c{}".format(num)]['name'] + "】" + "：" + \
                "\n" + data["c{}".format(num)]['effect'].replace("*", "")
    except:
        im = "参数不正确。"
    return im

def talents_wiki(name,num):
    raw_data = GetCharTalentsInfo(name)

    if int(num) <= 3 :
        if num == "1":
            data = raw_data["combat1"]
        elif num == "2":
            data = raw_data["combat2"]
        elif num == "3":
            data = raw_data["combat3"]
        skill_name = data["name"]
        skill_info = data["info"]
        skill_detail = ""

        for i in data["attributes"]["parameters"]:
            temp = ""
            for k in data["attributes"]["parameters"][i]:
                temp += "%.2f%%" % (k * 100) + "/"
            data["attributes"]["parameters"][i] = temp[:-1]

        for i in data["attributes"]["labels"]:
            #i = i.replace("{","{{")
            i = re.sub(r':[a-zA-Z0-9]+}', "}", i)
            #i.replace(r':[a-zA-Z0-9]+}','}')
            skill_detail += i + "\n"

        skill_detail = skill_detail.format(**data["attributes"]["parameters"])

        im = "【{}】\n{}\n————\n{}".format(skill_name,skill_info,skill_detail)

    else:
        if num == "4":
            data = raw_data["passive1"]
        elif num == "5":
            data = raw_data["passive2"]
        elif num == "6":
            data = raw_data["passive3"]
        skill_name = data["name"]
        skill_info = data["info"]
        im = "【{}】\n{}".format(skill_name,skill_info)

    return im

def GetUidUrl(uid,qid,nickname,mode = 2):
    while 1:
        use_cookies = cacheDB(uid,mode-1)
        if use_cookies == '':
            return "绑定记录不存在。"
        elif use_cookies == "没有可以使用的Cookies！":
            return "没有可以使用的Cookies！"

        if mode == 3:
            mys_data = GetMysInfo(uid,use_cookies)
            mysid_data = uid
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            #role_level = mys_data['data']['list'][0]['level']
            
        raw_data = GetInfo(uid,use_cookies)
            
        if raw_data["retcode"] != 0:
            if raw_data["retcode"] == 10001:
                #return ("Cookie错误/过期，请重置Cookie")
                errorDB(use_cookies,"error")
            elif raw_data["retcode"] == 10101:
                #return ("当前cookies已达到30人上限！")
                errorDB(use_cookies,"limit30")
            elif raw_data["retcode"] == 10102:
                return ("当前查询id已经设置了隐私，无法查询！")
            else:
                return (
                    "Api报错，返回内容为：\r\n"
                    + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
                )
        else:
            break
        
    url = GetUidPic(raw_data,uid,qid,nickname)
    return url