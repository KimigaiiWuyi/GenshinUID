import re,os,random,sqlite3,sys,datetime,math,json,time
import base64,traceback
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from shutil import copyfile
import urllib.parse
import httpx

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from mihoyo_libs.get_data import *
from mihoyo_libs.get_image import *
from mihoyo_libs.get_mihoyo_bbs_data import *

from Config import Config
from get_guild_data import *

import yaml
import asyncio
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
from qqbot.model.user import ReqOption

logger = logging.getLogger(__name__)

with open('Config.yaml', encoding='UTF-8') as yaml_file:
    yaml_config = yaml.safe_load(yaml_file)

token = qqbot.Token(yaml_config["BotID"],yaml_config["BotToken"])
test_guild_id = yaml_config["TestGuildID"]

api = qqbot.AsyncUserAPI(token, False)
guild_api = qqbot.AsyncGuildAPI(token,False)
audio_api = qqbot.AsyncAudioAPI(token,False)
msg_api = qqbot.AsyncMessageAPI(token, False)
guild_member_api = qqbot.AsyncGuildMemberAPI(token,False)
channel_api = qqbot.AsyncChannelAPI(token,False)
dms_api = qqbot.AsyncDmsAPI(token, False)

async def up_guild_list():
    guild_list = []
    guild_list_temp = []

    while(1):
        if guild_list != [] and len(guild_list_temp) >= 100:
            guild_list_temp = await api.me_guilds(option = ReqOption(after = str(guild_list_temp[-1].id)))
            guild_list += guild_list_temp
        elif guild_list == []:
            guild_list = await api.me_guilds()
            guild_list_temp = guild_list
        else:
            break

    for guild in guild_list:
        await change_guild("new",guild.id,guild.name)

async def new_guild(guild:Guild):
    await change_guild("new",guild.id,guild.name)

async def delete_guild(guild):
    await change_guild("delete",guild.id,guild.name)

async def ready():
    user = await api.me()
    await up_guild_list()
    print(user.username)

loop = asyncio.get_event_loop()
loop.run_until_complete(ready())

scheduler = AsyncIOScheduler()
scheduler.add_job(delete_cache, 'cron', hour='0')
scheduler.start()

Config = Config()

async def check_cookies():
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
        await cookies_db(uid, i, 10086)

async def getChannelStatus(gid):
    channel_openlist = await subGuild_status(gid)
    mes = "\n当前开启频道："
    if channel_openlist:
        channel_list = await channel_api.get_channels(gid)
        for i in channel_list:
            for j in channel_openlist:
                if i.id == j:
                    mes += "\n<<#{}>>".format(i.id)
    if mes == "\n当前开启频道：":
        mes = "\n当前开启频道：\n可在所有频道使用。"
    return mes

async def check_startwish(raw_mes,key_word,gid):
    if raw_mes.startswith(key_word) and await check_switch(gid,Config.switch_list[key_word]):
        return True
    else:
        return False

async def check_endwish(raw_mes,key_word,gid):
    if raw_mes.endswith(key_word) and await check_switch(gid,Config.switch_list[key_word]):
        return True
    else:
        return False

async def GetUidUrl(uid,qid,nickname,mode = 2):
    try:
        while 1:
            use_cookies = cache_db(uid,mode-1)
            if use_cookies == '':
                return "绑定记录不存在。"
            elif use_cookies == "没有可以使用的Cookies！":
                return "没有可以使用的Cookies！"

            if mode == 3:
                mys_data = await get_mihoyo_bbs_info(uid,use_cookies)
                mysid_data = uid
                for i in mys_data['data']['list']:
                    if i['game_id'] != 2:
                        mys_data['data']['list'].remove(i)
                uid = mys_data['data']['list'][0]['game_role_id']
                nickname = mys_data['data']['list'][0]['nickname']
                #role_level = mys_data['data']['list'][0]['level']
                
            raw_data = await get_info(uid,use_cookies)
            if raw_data["retcode"] != 0:
                if raw_data["retcode"] == 10001:
                    #return ("Cookie已过期，可联系小灰灰处理！")
                    error_db(use_cookies,"error")
                elif raw_data["retcode"] == 10101:
                    #return ("当前查询接口已达到上限，可联系小灰灰处理！")
                    error_db(use_cookies,"limit30")
                elif raw_data["retcode"] == 10102:
                    return ("当前查询id已经设置了隐私，无法进行查询！")
                else:
                    return (
                        "Api报错，返回内容为：\r\n"
                        + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
                    )
            else:
                break
        style = "egenshin"
        url = "https://yuanshen.minigg.cn/generator/user_info?style=" + style + "&uid=" + uid + "&qid=" + qid + "&nickname=" + urllib.parse.quote(nickname) +"&quality=75"
        async with AsyncClient() as client:
            req = await client.post(
                url = url,
                json = raw_data
            )
        return req.text
    except TypeError as e:
        traceback.print_exc()
        return "请求数据为空，可能是绘制图片时出错。"
    except Exception as e:
        traceback.print_exc()
        return "发生错误，频道信息Api可能变动。"

async def _message_handler(event, message: Message):

    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)

    try:
        guild_data = await guild_api.get_guild(message.guild_id)
        at_mes = re.search(r'\<\@\![0-9]+\>',message.content)
        raw_mes = message.content.replace(at_mes.group(),"").replace(" ","").replace("/","")
        record_mes = raw_mes
    except Exception as e:
        qqbot.logger.info(e.with_traceback)
        traceback.print_exc()
        return

    mes = None
    image = None
    ark = None
    audio = None

    if raw_mes.startswith("开启"):
        raw_mes = raw_mes.replace("开启","")
        member_info = await guild_member_api.get_guild_member(message.guild_id, message.author.id)
        if "2" in member_info.roles or "4" in member_info.roles:
            try:
                await change_switch(message.guild_id,Config.switch_list[raw_mes],"on")
                mes = "成功。"
            except Exception as e:
                traceback.print_exc()
                mes = "发生错误，可能是输入的功能名不正确。"
        else:
            return
    elif raw_mes.startswith("关闭"):
        raw_mes = raw_mes.replace("关闭","")
        member_info = await guild_member_api.get_guild_member(message.guild_id, message.author.id)
        if "2" in member_info.roles or "4" in member_info.roles:
            try:
                await change_switch(message.guild_id,Config.switch_list[raw_mes],"off")
                mes = "成功。"
            except Exception as e:
                traceback.print_exc()
                mes = "发生错误，可能是输入的功能名不正确。"
        else:
            return
    elif raw_mes == "校验全部Cookies":
        try:
            if int(message.guild_id) == int(test_guild_id):
                raw_data = await check_db()
                mes = raw_data[0]
            else:
                return
        except Exception as e:
            traceback.print_exc()
            mes = "发生错误。"
    elif raw_mes.startswith("设置频道开启"):
        try:
            member_info = await guild_member_api.get_guild_member(message.guild_id, message.author.id)
            if "2" in member_info.roles or "4" in member_info.roles:
                channel_name = raw_mes.replace("设置频道开启","").replace("#","")
                channel_list = await channel_api.get_channels(message.guild_id)
                for i in channel_list:
                    temp_name = i.name.replace(" ","")
                    if temp_name == channel_name:
                        channel_id = i.id
                await change_subGuild_switch(message.guild_id,channel_id,"open")
                channel_status = await getChannelStatus(message.guild_id)
                mes = "已设置子频道使用该BOT。\n子频道名称：<<#{}>>\n子频道ID：{}".format(channel_id,channel_id)
                mes += channel_status
            else:
                return
        except Exception as e:
            traceback.print_exc()
            mes = "发生错误，可能是输入的功能名不正确。"
    elif raw_mes.startswith("设置频道关闭"):
        try:
            member_info = await guild_member_api.get_guild_member(message.guild_id, message.author.id)
            if "2" in member_info.roles or "4" in member_info.roles:
                channel_name = raw_mes.replace("设置频道关闭","").replace("#","")
                channel_list = await channel_api.get_channels(message.guild_id)
                for i in channel_list:
                    temp_name = i.name.replace(" ","")
                    if temp_name == channel_name:
                        channel_id = i.id
                await change_subGuild_switch(message.guild_id,channel_id,"closed")
                channel_status = await getChannelStatus(message.guild_id)
                mes = "已禁止子频道使用该BOT。\n子频道名称：<<#{}>>\n子频道ID：{}".format(channel_id,channel_id)
                mes += channel_status
            else:
                return
        except Exception as e:
            traceback.print_exc()
            mes = "发生错误，可能是输入的功能名不正确。"


    if not await check_subGuild_switch(message.guild_id,message.channel_id):
        mes = await getChannelStatus(message.guild_id)
    else:
        if raw_mes == "频道信息":
            member_info = await guild_member_api.get_guild_member(message.guild_id, message.author.id)
            if "2" in member_info.roles or "4" in member_info.roles or "5" in member_info.roles:
                try:
                    mes = await getGuildStatus()
                except Exception as e:
                    traceback.print_exc()
                    qqbot.logger.info(e.with_traceback)
                    mes = "发生错误，频道信息Api可能变动。"
            else:
                return
        elif raw_mes == "help":
            ark = MessageArk(data = await Config.load_ark("helpARK"))
        elif raw_mes == "master":
            ark = MessageArk(data = await Config.load_ark("masterARK"))
        elif raw_mes == "整理cookies":
            try:
                await check_cookies()
                mes = "成功!"
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "ck添加错误。"
        elif raw_mes == "当前状态" and await check_switch(message.guild_id,Config.switch_list["当前状态"]):
            try:
                uid = await select_db(message.author.id, mode="uid")
                uid = uid[0]
                data = await daily("ask", uid)
                mes = data[0]['message']
            except TypeError:
                mes = "没有找到绑定信息。"
                traceback.print_exc()
            except Exception as e:
                mes = "发生错误 {},请检查后台输出。".format(e)
                traceback.print_exc()
        elif raw_mes == "每月统计" and await check_switch(message.guild_id,Config.switch_list["每月统计"]):
            try:
                uid = await select_db(message.author.id, mode="uid")
                uid = uid[0]
                mes = await award(uid)
            except TypeError:
                mes = "没有找到绑定信息。"
                traceback.print_exc()
            except Exception as e:
                mes = "发生错误 {},请检查后台输出。".format(e)
                traceback.print_exc()
        elif raw_mes == "签到" and await check_switch(message.guild_id,Config.switch_list["签到"]):
            try:
                uid = await select_db(message.author.id, mode="uid")
                uid = uid[0]
                mes = await sign(uid)
            except TypeError:
                mes = "没有找到绑定信息。"
                traceback.print_exc()
            except Exception as e:
                mes = "发生错误 {},请检查后台输出。".format(e)
                traceback.print_exc()
        elif await check_startwish(raw_mes,"语音",message.guild_id):
            raw_mes = raw_mes.replace("语音","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                if name == "列表":
                    image = "https://img.genshin.minigg.cn/audio-favicon/audioid.png"
                elif name == "":
                    return
                else:
                    audioid = re.findall(r"[0-9]+", raw_mes)[0]

                    tmp_json=json.loads(audio_json)
                    for _ in range(3):#重试3次
                        if audioid in tmp_json:
                            if not tmp_json[audioid]:
                                return
                            audioid1 = random.choice(tmp_json[audioid])
                        else:
                            audioid1=audioid
                        url = "https://bot.q.minigg.cn/audio/?characters=" + name + "&audioid=" + audioid1 + "&language=cn"
                        req=requests.get(url)
                        if req.headers["Content-Type"].startswith("audio"):
                            audio_url = url
                        else:
                            if audioid in tmp_json:
                                tmp_json[audioid].remove(audioid1)

                    audio_img = "https://img.genshin.minigg.cn/avatar/{}.png".format(name)
                    audio_str = "{}语音{}".format(name,audioid)
                    audio_raw_ark = await Config.load_ark(ark = "audioARK")
                    audio_raw_ark["kv"][0]["value"] = "角色语音"
                    audio_raw_ark["kv"][1]["value"] = "角色语音"
                    audio_raw_ark["kv"][2]["value"] = audio_str
                    audio_raw_ark["kv"][3]["value"] = "原神角色的语音"
                    audio_raw_ark["kv"][4]["value"] = audio_img
                    audio_raw_ark["kv"][5]["value"] = audio_url
                    audio_raw_ark["kv"][6]["value"] = "原神语音"
                    ark = MessageArk(data = audio_raw_ark)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = e.with_traceback

        elif raw_mes == "查询" and await check_switch(message.guild_id,Config.switch_list["查询"]):
            try:
                uid = await select_db(message.author.id)
                author = await guild_member_api.get_guild_member(message.guild_id,message.author.id)
                nickname = author.user.username
                get_url = await GetUidUrl(uid[0],message.author.id,nickname,uid[1])
                url = json.loads(get_url)
                if url["url"].startswith("/"):
                    image = "https://yuanshen.minigg.cn" + url["url"]
                    status = urllib.request.urlopen(image).code
                    if status == 200:
                        pass
                    else:
                        image = None
                        mes = "输入格式有误，请检查输入是否为9位国服或者大陆渠道服的UID。\n\n例如：/uid137727130\n\n输入/help查看完整帮助"
                else:
                    mes = image
            except json.JSONDecodeError:
                mes = get_url
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "没有找到绑定信息。"
        elif await check_startwish(raw_mes,"uid",message.guild_id):
            raw_mes = raw_mes.replace("uid","")
            try:
                uid = re.findall(r"[0-9]+", raw_mes)[0]
                if len(uid) != 9:
                    mes = "你输入了错误的uid，请检查输入是否正确。"
                else:
                    get_url = await GetUidUrl(uid,message.author.id,message.author.username)
                    url = json.loads(get_url)
                    if url["url"].startswith("/"):
                        image = "https://yuanshen.minigg.cn" + url["url"]
                        status = urllib.request.urlopen(image).code
                        if status == 200:
                            pass
                        else:
                            image = None
                            mes = "链接不存在，可能由于上游接口查询限制，请稍后重试"
                    else:
                        mes = image
            except json.JSONDecodeError:
                mes = get_url
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "UID输入格式有误，请检查输入是否为9位国服或者大陆渠道服的UID。\n\n例如：/uid137727130\n\n输入/help查看完整帮助"
        elif await check_startwish(raw_mes,"mys",message.guild_id):
            raw_mes = raw_mes.replace("mys","")
            try:
                uid = re.findall(r"[0-9]+", raw_mes)[0]
                get_url = await GetUidUrl(uid,message.author.id,message.author.username,mode=3)
                url = json.loads(get_url)
                if url["url"].startswith("/"):
                    image = "https://yuanshen.minigg.cn" + url["url"]
                    status = urllib.request.urlopen(image).code
                    if status == 200:
                        pass
                    else:
                        image = None
                        mes = "链接不存在，可能由于上游接口查询限制，请稍后重试。"
                else:
                    mes = image
            except json.JSONDecodeError:
                mes = get_url
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "输入格式有误，请检查输入是否为米游社ID。\n\n例如：/mys137727130\n\n输入/help查看完整帮助"
        #elif raw_mes.startswith("活动列表"):
            #draw_event_pic()
        #    pass
        elif await check_startwish(raw_mes,"绑定uid",message.guild_id):
            uid = raw_mes.replace("绑定uid","")
            try:
                await connect_db(userid = message.author.id,uid = uid)
                mes = "绑定uid成功。"
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "绑定失败。"
        elif await check_startwish(raw_mes,"绑定mys",message.guild_id):
            uid = raw_mes.replace("绑定mys","")
            try:
                await connect_db(userid = message.author.id,mys = uid)
                mes = "绑定mysid成功。"
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "绑定失败。"
        elif await check_endwish(raw_mes,"用什么",message.guild_id):
            raw_mes = raw_mes.replace("用什么","")
            name = raw_mes
            try:
                mes = await char_adv(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "没有找到该角色的培养建议。"
        elif await check_endwish(raw_mes,"给谁用",message.guild_id):
            raw_mes = raw_mes.replace("给谁用","")
            name = raw_mes
            try:
                mes = await weapon_adv(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "没有找到该武器的使用建议。"
        elif await check_startwish(raw_mes,"角色",message.guild_id):
            raw_mes = raw_mes.replace("角色","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                level = re.findall(r"[0-9]+", raw_mes)
                if len(level) == 1:
                    mes = await char_wiki(name,"char",level=level[0])
                else:
                    mes = await char_wiki(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误，请联系管理员检查后台。"
        elif await check_startwish(raw_mes,"武器",message.guild_id):
            raw_mes = raw_mes.replace("武器","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                level = re.findall(r"[0-9]+", raw_mes)
                if len(level) == 1:
                    mes = await weapon_wiki(name,level=level[0])
                else:
                    mes = await weapon_wiki(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误，请联系管理员检查后台。"
        elif await check_startwish(raw_mes,"食物",message.guild_id):
            raw_mes = raw_mes.replace("食物","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                mes = await foods_wiki(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误，请联系管理员检查后台。"
        elif await check_startwish(raw_mes,"原魔",message.guild_id):
            raw_mes = raw_mes.replace("原魔","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                mes = await enemies_wiki(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误，请联系管理员检查后台。"
        elif await check_startwish(raw_mes,"圣遗物",message.guild_id):
            raw_mes = raw_mes.replace("圣遗物","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                mes = await artifacts_wiki(name)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误，请联系管理员检查后台。"
        elif await check_startwish(raw_mes,"材料",message.guild_id):
            raw_mes = raw_mes.replace("材料","")
            try:
                mes = await char_wiki(raw_mes,"costs")
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "不存在该角色或类型。"
        elif await check_startwish(raw_mes,"天赋",message.guild_id):
            raw_mes = raw_mes.replace("天赋","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                num = re.findall(r"[0-9]+", raw_mes)
                if len(num) == 1:
                    mes = await char_wiki(name,"talents",num[0])
                else:
                    mes = "暂无该天赋数，天赋可查询数量为1~7。\n\n输入/help可查看完整帮助"
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "暂无该角色攻略，请检查角色名字是否正确，需输入完整名字。\n\n输入/help可查看完整帮助"
        elif await check_startwish(raw_mes,"命座",message.guild_id):
            raw_mes = raw_mes.replace("命座","")
            try:
                try:
                    num = int(re.findall(r"\d+", raw_mes)[0])  # str
                except:
                    mes = "参数输入有误。"
                m = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                if num<= 0 or num >6:
                    mes = "暂无该命座数量，命座可查询数量为1-6命。\n\n输入/help可查看完整帮助"
                else:
                    mes = await char_wiki(m, "constellations", num)
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "暂无该角色攻略，请检查角色名字是否正确，需输入完整名字。\n\n输入/help可查看完整帮助"
        elif await check_startwish(raw_mes,"攻略",message.guild_id):
            raw_mes = raw_mes.replace("攻略","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                image = "https://img.genshin.minigg.cn/guide/{}.jpg".format(urllib.parse.quote(name, safe=''))
                status = httpx.get(url = image).text
                if "404 Not Found" in status:
                    image = None
                    mes = "暂无该角色攻略，请检查角色名字是否正确，需输入完整名字。\n\n例如：/攻略申鹤\n\n输入/help可查看完整帮助"
                else:
                    pass
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误。"
        elif await check_startwish(raw_mes,"信息",message.guild_id):
            raw_mes = raw_mes.replace("信息","")
            try:
                name = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
                image = "https://img.genshin.minigg.cn/info/{}.jpg".format(urllib.parse.quote(name, safe=''))
                status = httpx.get(url = image).text
                if "404 Not Found" in status:
                    image = None
                    mes = "暂无该角色攻略，请检查角色名字是否正确，需输入完整名字。\n\n例如：/攻略申鹤\n\n输入/help可查看完整帮助"
                else:
                    pass
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "发生错误。"

        elif raw_mes == "御神签" and await check_switch(message.guild_id,Config.switch_list["御神签"]):
            try:
                raw_data = await get_a_lots(message.author.id)
                mes = base64.b64decode(raw_data).decode("utf-8")
            except Exception as e:
                traceback.print_exc()
                qqbot.logger.info(e.with_traceback)
                mes = "御神签见底了，稍后再来试试吧！"
    
    """
    elif audio:
        try:
            await audio_api.post_audio(channel_id = message.channel_id,audio_control = audio_control)
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,audio)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                await msg_api.post_message(message.channel_id, send)
            except:
                pass
            traceback.print_exc()
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    """
    
    if ark:
        try:
            send = qqbot.MessageSendRequest(content = "",ark = ark, msg_id = message.id)
            await msg_api.post_message(message.channel_id, send)
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,"help")
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                await msg_api.post_message(message.channel_id, send)
            except:
                pass
            traceback.print_exc()
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    elif image:
        try:
            send = qqbot.MessageSendRequest(content = "",image = image, msg_id = message.id)
            await msg_api.post_message(message.channel_id, send)
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,image)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                await msg_api.post_message(message.channel_id, send)
            except:
                pass
            traceback.print_exc()
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    elif mes:
        try:
            send = qqbot.MessageSendRequest(mes, message.id)
            await msg_api.post_message(message.channel_id, send)
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
        except Exception as e:
            try:
                send = qqbot.MessageSendRequest(str(e), message.id)
                await msg_api.post_message(message.channel_id, send)
            except:
                pass
            traceback.print_exc()
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    else:
        mes = "你可能发送了错误的指令或者管理员关闭了该功能，请输入/help查看帮助。"
        try:
            send = qqbot.MessageSendRequest(mes, message.id)
            await msg_api.post_message(message.channel_id, send)
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,mes)
        except Exception as e:
            traceback.print_exc()
            await record(guild_data.name,message.guild_id,message.author.username,message.author.id,record_mes,str(e))
    return

async def _dms_handler(event, message: Message):
    qqbot.logger.info("event %s" % event + ",receive message %s" % message.content)

    try:
        raw_mes = message.content.replace(" ","").replace("/","")
        record_mes = raw_mes
    except Exception as e:
        qqbot.logger.info(e.with_traceback)
        traceback.print_exc()
        return

    mes = None
    if raw_mes.startswith("添加"):
        try:
            await deal_ck(raw_mes.replace("添加",""),message.author.id)
            mes = "添加Cookies成功。"
        except:
            traceback.print_exc()
            mes = "添加Cookies失败，请检查格式。"
    
    if mes:
        try:
            msg_request = qqbot.MessageSendRequest(content=mes, msg_id=message.id)
            msg = await dms_api.post_direct_message(message.guild_id, msg_request)
            await record("私信",message.guild_id,message.author.username,message.author.id,record_mes,mes)
        except Exception as e:
            traceback.print_exc()
            await record("私信",message.guild_id,message.author.username,message.author.id,record_mes,str(e))
        

async def _guild_handler(event, guild:Guild):
    print("\n频道已刷新。\n")
    if event == "GUILD_CREATE":
        await new_guild(guild)
    elif event == "GUILD_DELETE":
        await delete_guild(guild)

async def getGuildStatus():

    guild_list = []
    guild_list_temp = []

    while(1):
        if guild_list != [] and len(guild_list_temp) >= 100:
            guild_list_temp = await api.me_guilds(option = ReqOption(after = str(guild_list_temp[-1].id)))
            guild_list += guild_list_temp
        elif guild_list == []:
            guild_list = await api.me_guilds()
            guild_list_temp = guild_list
        else:
            break

    guild_member_all_count = 0
    guild_status_mes  = ""

    for guild in guild_list:
        try:
            guild_data = await guild_api.get_guild(guild.id)
            #guild_status_mes += "【{}】{}人\n".format(guild.name,str(guild_data.member_count))
            guild_member_all_count += guild_data.member_count
        except Exception as e:
            qqbot.logger.info(e.args)
            traceback.print_exc()
    user = await api.me()
    guild_status_mes = "【{}】总加入频道 {} 个,总人数为 {}".format(user.username,str(len(guild_list)),str(guild_member_all_count))
    return guild_status_mes

qqbot_guildevent_handler = qqbot.Handler(qqbot.HandlerType.GUILD_EVENT_HANDLER, _guild_handler)
qqbot_atmessage_handler = qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, _message_handler)
qqbot_dms_handler = qqbot.Handler(qqbot.HandlerType.DIRECT_MESSAGE_EVENT_HANDLER, _dms_handler)
qqbot.async_listen_events(token, False, qqbot_guildevent_handler,qqbot_atmessage_handler,qqbot_dms_handler)
