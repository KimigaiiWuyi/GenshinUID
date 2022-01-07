import re,os,random,sqlite3,sys,datetime,math,json,time
import base64
from apscheduler.schedulers.background import BackgroundScheduler
from shutil import copyfile
import urllib.parse
import httpx

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from getDB import (connectDB, cookiesDB, deletecache, selectDB, get_alots, cacheDB, errorDB, add_guild, check_switch,record,change_switch)
from getData import (GetInfo,GetWeaponInfo,GetCharInfo,GetUidPic,GetMysInfo,GetAudioInfo)
from getImg import (draw_event_pic)

import qqbot
from qqbot.model.guild import Guild
from qqbot.model.audio import AudioControl
from qqbot.model.message import (
    MessageSendRequest,
    MessageArk,
    Message,
    CreateDirectMessageRequest,
    DirectMessageGuild,
)
from qqbot.core.util import logging

logger = logging.getLogger(__name__)

token = qqbot.Token("","")

api = qqbot.UserAPI(token, False)
guild_api = qqbot.GuildAPI(token,False)
audio_api = qqbot.AudioAPI(token,False)
msg_api = qqbot.MessageAPI(token, False)
guild_member_api = qqbot.GuildMemberAPI(token,False)
user = api.me()
print(user.username)

audio_raw_ark = {
    "template_id": 24,
    "kv": [
      {
        "key": "#DESC#",
        "value": ""
      },
      {
        "key": "#PROMPT#",
        "value": ""
      },
      {
        "key": "#TITLE#",
        "value": ""
      },
      {
        "key": "#METADESC#",
        "value": ""
      },
      {
        "key": "#IMG#",
        "value": ""
      },
      {
        "key": "#LINK#",
        "value": ""
      },
      {
        "key": "#SUBTITLE#",
        "value": ""
      }
    ]
}

help_ark = MessageArk(data = {
    "template_id": 23,
    "kv": [
      {
        "key": "#DESC#",
        "value": "原神Bot"
      },
      {
        "key": "#PROMPT#",
        "value": "这是一份原神帮助"
      },
      {
        "key": "#LIST#",
        "obj": [
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "===原神Bot==="
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "原神娱乐功能Bot"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "=================="
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "uid+<uid> · 输入9位的原神UID"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "攻略+<角色名> · 查看角色攻略"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "信息+<角色|武器> · 查看该角色或武器的介绍"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "角色+<角色名> · 查看该角色的介绍-文字版"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "武器+<武器名> · 查看该武器的介绍-文字版"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "御神签 · 与游戏内御神签结果无关"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "命座+<数字>+<角色名> · 查看命座描述"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "-------------------"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "需要@机器人使用，+号无需输入"
              }
            ]
          },
          {
            "obj_kv": [
              {
                "key": "desc",
                "value": "<> 表示填入的内容，· 后面为说明"
              }
            ]
          },
        
        ]
      }
    ]
})

switch_list = {
    "uid":"SearchRole",
    "mys":"SearchRole",
    "查询":"SearchRole",
    "绑定uid":"LinkUID",
    "绑定mys":"LinkUID",
    "角色":"CharInfo",
    "武器":"WeaponInfo",
    "材料":"CostInfo",
    "天赋":"TalentsInfo",
    "命座":"PolarInfo",
    "攻略":"guideInfo",
    "信息":"CardInfo",
    "御神签":"GetLots",
    "语音":"AudioInfo"
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

audio_json = {
    "357":["357_01","357_02","357_03"],
    "1000000":["1000000_01","1000000_02","1000000_03","1000000_04","1000000_05","1000000_06","1000000_07"],
    "1000001":["1000001_01","1000001_02","1000001_03"],
    "1000002":["1000002_01","1000002_02","1000002_03"],
    "1000100":["1000100_01","1000100_02","1000100_03","1000100_04","1000100_05"],
    "1000101":["1000101_01","1000101_02","1000101_03","1000101_04","1000101_05","1000101_06"],
    "1000200":["1000200_01","1000200_02","1000200_03"],
    "1010201":["1010201_01"],
    "1000300":["1000300_01","1000300_02"],
    "1000400":["1000400_01","1000400_02","1000400_03"],
    "1000500":["1000500_01","1000500_02","1000500_03"],
    "1010000":["1010000_01","1010000_02","1010000_03","1010000_04","1010000_05"],
    "1010001":["1010001_01","1010001_02"],
    "1010100":["1010100_01","1010100_02","1010100_03","1010100_04","1010100_05"],
    "1010200":["1010200_01","1010200_02","1010200_03","1010200_04","1010200_05"],
    "1010300":["1010300_01","1010300_02","1010300_03","1010300_04","1010300_05"],
    "1010301":["1010301_01","1010301_02","1010301_03","1010301_04","1010301_05"],
    "1010400":["1010400_01","1010400_02","1010400_03"],
    "1020000":["1020000_01"]
}

def check_startwish(raw_mes,key_word,gid):
    if raw_mes.startswith(key_word) and check_switch(gid,switch_list[key_word]):
        return True
    else:
        return False

def check_cookies():
    with open("cookies_simp.json",'r') as load_f:
        load_dict = json.load(load_f)
    num = 0
    for i in load_dict["data"]:
        aid = re.search(r"account_id=(\d*)", i)
        mysid_data = aid.group(0).split('=')
        mysid = mysid_data[1]
        cookie = ';'.join(filter(lambda x: x.split('=')[0] in [
                          "cookie_token", "account_id"], [j.strip() for j in i.split(';')]))
        uid = int(time.time()) + num
        num += 1
        cookiesDB(uid, i, 10086)

def up_guild_list():
    guild_list = api.me_guilds()
    for guild in guild_list:
        #guild_data = guild_api.get_guild(guild.id)
        add_guild(guild.id,guild.name)

up_guild_list()

def GetUidUrl(uid,qid,nickname,mode = 2):
    try:
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
    except Exception as e:
        qqbot.logger.info(e.with_traceback)
        return "发生错误，频道信息Api可能变动。"
    
def _message_handler(event, message: Message):
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)

    try:
        guild_data = guild_api.get_guild(message.guild_id)
        at_mes = re.search(r'\<\@\![0-9]+\>',message.content)
        raw_mes = message.content.replace(at_mes.group(),"").replace(" ","").replace("/","")
        record_mes = raw_mes
    except Exception as e:
        qqbot.logger.info(e.with_traceback)
        return

    mes = None
    image = None
    ark = None
    audio = None
    
    if raw_mes == "频道信息":
        try:
            mes = getGuildStatus()
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "发生错误，频道信息Api可能变动。"
    elif raw_mes == "help":
        ark = help_ark
    elif raw_mes == "整理123":
        try:
            check_cookies()
            mes = "成功!"
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "ck添加错误。"
    elif check_startwish(raw_mes,"语音",message.guild_id):
        raw_mes = raw_mes.replace("语音","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            if name == "列表":
                image = "https://img.genshin.minigg.cn/audio-favicon/audioid.png"
            elif name == "":
                return
            else:
                audioid = re.findall(r"[0-9]+", raw_mes)[0]
                if audioid in audio_json:
                    audioid = random.choice(audio_json[audioid])
                audio_url = GetAudioInfo(name,audioid)
                audio_img = "https://img.genshin.minigg.cn/avatar/{}.png".format(name)
                audio_str = "{}语音{}".format(name,audioid)
                audio_raw_ark["kv"][0]["value"] = "角色语音"
                audio_raw_ark["kv"][1]["value"] = "角色语音"
                audio_raw_ark["kv"][2]["value"] = audio_str
                audio_raw_ark["kv"][3]["value"] = "原神角色的语音"
                audio_raw_ark["kv"][4]["value"] = audio_img
                audio_raw_ark["kv"][5]["value"] = audio_url
                audio_raw_ark["kv"][6]["value"] = "原神语音"
                ark = MessageArk(data = audio_raw_ark)
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = e.with_traceback
    elif raw_mes == "查询" and check_switch(message.guild_id,switch_list["查询"]):
        try:
            uid = selectDB(message.author.id)
            author = guild_member_api.get_guild_member(message.guild_id,message.author.id)
            nickname = author.user.username
            get_url = GetUidUrl(uid[0],message.author.id,nickname,uid[1])
            url = json.loads(get_url)
            if url["url"].startswith("/"):
                image = "https://yuanshen.minigg.cn" + url["url"]
                status = urllib.request.urlopen(image).code
                if status == 200:
                    pass
                else:
                    image = None
                    mes = "链接不存在。"
            else:
                mes = image
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "没有找到绑定信息。"
    elif raw_mes.startswith("开启"):
        raw_mes = raw_mes.replace("开启","").replace("功能","")
        try:
            change_switch(message.guild_id,switch_list[raw_mes],"on")
            mes = "成功。"
        except Exception as e:
            print(e.with_traceback)
            mes = "发生错误，可能是输入的功能名不正确。"
    elif raw_mes.startswith("关闭"):
        raw_mes = raw_mes.replace("关闭","").replace("功能","")
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
                get_url = GetUidUrl(uid,message.author.id,message.author.username)
                url = json.loads(get_url)
                if url["url"].startswith("/"):
                    image = "https://yuanshen.minigg.cn" + url["url"]
                    status = urllib.request.urlopen(image).code
                    if status == 200:
                        pass
                    else:
                        image = None
                        mes = "链接不存在。"
                else:
                    mes = image
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "参数不正确。"
    elif check_startwish(raw_mes,"mys",message.guild_id):
        raw_mes = raw_mes.replace("mys","")
        try:
            uid = re.findall(r"[0-9]+", raw_mes)[0]
            get_url = GetUidUrl(uid,message.author.id,message.author.username,mode=3)
            url = json.loads(get_url)
            if url["url"].startswith("/"):
                image = "https://yuanshen.minigg.cn" + url["url"]
                status = urllib.request.urlopen(image).code
                if status == 200:
                    pass
                else:
                    image = None
                    mes = "链接不存在。"
            else:
                mes = image
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "参数不正确。"
    #elif raw_mes.startswith("活动列表"):
        #draw_event_pic()
    #    pass
    elif check_startwish(raw_mes,"绑定uid",message.guild_id):
        uid = raw_mes.replace("绑定uid","")
        try:
            connectDB(userid = message.author.id,uid = uid)
            mes = "绑定uid成功。"
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "绑定失败。"
    elif check_startwish(raw_mes,"绑定mys",message.guild_id):
        uid = raw_mes.replace("绑定mys","")
        try:
            connectDB(userid = message.author.id,mys = uid)
            mes = "绑定mysid成功。"
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "绑定失败。"
    elif check_startwish(raw_mes,"角色",message.guild_id):
        raw_mes = raw_mes.replace("角色","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            level = re.findall(r"[0-9]+", raw_mes)
            if len(level) == 1:
                mes = char_wiki(name,"char",level=level[0])
            else:
                mes = char_wiki(name)
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "不存在该角色或类型。"
    elif check_startwish(raw_mes,"武器",message.guild_id):
        raw_mes = raw_mes.replace("武器","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            level = re.findall(r"[0-9]+", raw_mes)
            if len(level) == 1:
                mes = weapon_wiki(name,level=level[0])
            else:
                mes = weapon_wiki(name)
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "不存在该武器。"
    elif check_startwish(raw_mes,"材料",message.guild_id):
        raw_mes = raw_mes.replace("材料","")
        try:
            mes = char_wiki(raw_mes,"costs")
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "不存在该角色或类型。"
    elif check_startwish(raw_mes,"天赋",message.guild_id):
        raw_mes = raw_mes.replace("天赋","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            num = re.findall(r"[0-9]+", raw_mes)
            if len(num) == 1:
                mes = char_wiki(name,"talents",num[0])
            else:
                mes = "参数不正确。"
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "不存在该角色。"
    elif check_startwish(raw_mes,"命座",message.guild_id):
        raw_mes = raw_mes.replace("命座","")
        try:
            num = int(re.findall(r"\d+", raw_mes)[0])  # str
            m = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            if num<= 0 or num >6:
                mes = "不存在命座数。"
            else:
                mes = char_wiki(m, "constellations", num)
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "不存在该角色。"
    elif check_startwish(raw_mes,"攻略",message.guild_id):
        raw_mes = raw_mes.replace("攻略","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            image = "https://img.genshin.minigg.cn/guide/{}.jpg".format(urllib.parse.quote(name, safe=''))
            status = httpx.get(url = image).text
            if "404 Not Found" in status:
                image = None
                mes = "信息库中不存在该角色。"
            else:
                pass
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "发生错误。"
    elif check_startwish(raw_mes,"信息",message.guild_id):
        raw_mes = raw_mes.replace("信息","")
        try:
            name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
            image = "https://img.genshin.minigg.cn/info/{}.jpg".format(urllib.parse.quote(name, safe=''))
            status = httpx.get(url = image).text
            if "404 Not Found" in status:
                image = None
                mes = "信息库中不存在该角色。"
            else:
                pass
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "发生错误。"

    elif raw_mes == "御神签" and check_switch(message.guild_id,switch_list["御神签"]):
        try:
            raw_data = get_alots(message.author.id)
            mes = base64.b64decode(raw_data).decode("utf-8")
        except Exception as e:
            qqbot.logger.info(e.with_traceback)
            mes = "抽取御神签失败。"

    if ark:
        try:
            send = qqbot.MessageSendRequest(content = "",ark = ark, msg_id = message.id)
            msg_api.post_message(message.channel_id, send)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,"help")
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                msg_api.post_message(message.channel_id, send)
            except:
                pass
            qqbot.logger.info(e.args)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    elif audio:
        try:
            audio_api.post_audio(channel_id = message.channel_id,audio_control = audio_control)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,audio)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                msg_api.post_message(message.channel_id, send)
            except:
                pass
            qqbot.logger.info(e.args)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    elif image:
        try:
            send = qqbot.MessageSendRequest(content = "",image = image, msg_id = message.id)
            msg_api.post_message(message.channel_id, send)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,image)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                msg_api.post_message(message.channel_id, send)
            except:
                pass
            qqbot.logger.info(e.args)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    elif mes:
        try:
            send = qqbot.MessageSendRequest(mes, message.id)
            msg_api.post_message(message.channel_id, send)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                msg_api.post_message(message.channel_id, send)
            except:
                pass
            qqbot.logger.info(e.args)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    else:
        mes = "你可能发送了错误的指令或参数不正确,或者使用了未开启的功能，请查看帮助。"
        try:
            send = qqbot.MessageSendRequest(mes, message.id)
            msg_api.post_message(message.channel_id, send)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
        except Exception as e:
            qqbot.logger.info(e.args)
            record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    return

def _guild_handler(event, guild:Guild):
    up_guild_list()

def getGuildStatus():
    guild_list = api.me_guilds()
    guild_member_all_count = 0
    guild_status_mes  = ""
    for guild in guild_list:
        guild_data = guild_api.get_guild(guild.id)
        guild_status_mes += "【{}】{}人\n".format(guild.name,str(guild_data.member_count))
        guild_member_all_count += guild_data.member_count
    guild_status_mes += "【{}】总加入频道 {} 个,总人数为 {}".format(user.username,str(len(guild_list)),str(guild_member_all_count))
    return guild_status_mes

def weapon_wiki(name,level = None):
    data = GetWeaponInfo(name)
    if level:
        data2 = GetWeaponInfo(name,level+"plus" if level else level)
        if data["substat"] != "":
            sp = data["substat"] + "：" + '%.1f%%' % (data2["specialized"] * 100) if data["substat"] != "元素精通" else data["substat"] + "：" + str(math.floor(data2["specialized"]))
        else:
            sp = ""
        im = (data["name"] + "\n等级：" + str(data2["level"]) + "（突破" + str(data2["ascension"]) + "）" + 
                    "\n攻击力：" + str(math.floor(data2["attack"])) + "\n" + sp)
    else:
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


def char_wiki(name, mode="char", level=None):
    data = GetCharInfo(name, mode, level if mode == "char" else None)
    if mode == "char":
        if isinstance(data,str):
            raw_data = data.replace("[","").replace("\n","").replace("]","").replace(" ","").replace("'","").split(',')
            if data.replace("\n","").replace(" ","") == "undefined":
                im = "不存在该角色或类型。"
            else:
                im = ','.join(raw_data)
        elif level:
            data2 = GetCharInfo(name, mode)
            sp = data2["substat"] + "：" + '%.1f%%' % (data["specialized"] * 100) if data2["substat"] != "元素精通" else data2["substat"] + "：" + str(math.floor(data2["specialized"]))
            im = (data2["name"] + "\n等级：" + str(data["level"]) + "\n血量：" + str(math.floor(data["hp"])) +
                "\n攻击力：" + str(math.floor(data["attack"])) + "\n防御力：" + str(math.floor(data["defense"])) +
                "\n" + sp)
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
    elif mode == "costs":
        im = "【天赋材料(一份)】\n{}\n【突破材料】\n{}"
        im1 = ""
        im2 = ""
        
        talent_temp = {}
        talent_cost = data[1]["costs"]
        for i in talent_cost.values():
            for j in i:
                if j["name"] not in talent_temp:
                    talent_temp[j["name"]] = j["count"]
                else:
                    talent_temp[j["name"]] = talent_temp[j["name"]] + j["count"]
        for k in talent_temp:
            im1 = im1 + k + ":" + str(talent_temp[k]) + "\n"

        temp = {}
        cost = data[0]
        for i in range(1,7):
            for j in cost["ascend{}".format(i)]:
                if j["name"] not in temp:
                    temp[j["name"]] = j["count"]
                else:
                    temp[j["name"]] = temp[j["name"]] + j["count"]
                    
        for k in temp:
            im2 = im2 + k + ":" + str(temp[k]) + "\n"
        
        im = im.format(im1,im2)
    elif mode == "constellations":
        im = "【" + data["c{}".format(level)]['name'] + "】" + "：" + \
            "\n" + data["c{}".format(level)]['effect'].replace("*", "")
    elif mode == "talents":
        if int(level) <= 3 :
            if level == "1":
                data = data["combat1"]
            elif level == "2":
                data = data["combat2"]
            elif level == "3":
                data = data["combat3"]
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
            if level == "4":
                data = data["passive1"]
            elif level == "5":
                data = data["passive2"]
            elif level == "6":
                data = data["passive3"]
            elif level == "7":
                data = data["passive4"]
            skill_name = data["name"]
            skill_info = data["info"]
            im = "【{}】\n{}".format(skill_name,skill_info)
    return im

qqbot_handler2 = qqbot.Handler(qqbot.HandlerType.GUILD_EVENT_HANDLER, _guild_handler)
qqbot_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
qqbot.listen_events(token, False, qqbot_handler)
qqbot.listen_events(token, False, qqbot_handler2)
