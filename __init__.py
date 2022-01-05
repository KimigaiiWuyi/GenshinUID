import asyncio
import os
import re
import sqlite3
import threading
import time,math
import base64
import requests
from io import BytesIO
from base64 import b64encode
import random

import nonebot
from nonebot import *
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import *
from nonebot.adapters.cqhttp import Message, MessageSegment, permission, utils
from nonebot.rule import Rule
from loguru import logger

from .getDB import (CheckDB, GetAward, GetCharInfo, GetDaily, GetMysInfo,
                    GetSignInfo, GetSignList, GetWeaponInfo, MysSign, OpenPush,
                    connectDB, cookiesDB, deletecache, selectDB, get_alots,
                    GetEnemiesInfo,GetAudioInfo)
from .getImg import draw_abyss0_pic, draw_abyss_pic, draw_event_pic, draw_pic, draw_wordcloud

config = nonebot.get_driver().config
priority = config.genshinuid_priority if config.genshinuid_priority else 2
superusers = {int(x) for x in config.superusers}

draw_event = require("nonebot_plugin_apscheduler").scheduler
delet_cache = require("nonebot_plugin_apscheduler").scheduler
daily_sign = require("nonebot_plugin_apscheduler").scheduler
resin_notic = require("nonebot_plugin_apscheduler").scheduler

get_weapon = on_startswith("武器", priority=priority)
get_char = on_startswith("角色", priority=priority)
get_cost = on_startswith("材料", priority=priority)
get_polar = on_startswith("命座", priority=priority)
get_talents = on_startswith("天赋", priority=priority)
get_enemies = on_startswith("原魔", priority=priority)
get_audio = on_startswith("语音", priority=priority)

get_uid_info = on_startswith("uid", permission=GROUP, priority=priority)
get_mys_info = on_startswith("mys", permission=GROUP, priority=priority)

get_event = on_command("活动列表", priority=priority)
get_lots = on_command("御神签", priority=priority)

open_switch = on_startswith("开启", priority=priority)
close_switch = on_startswith("关闭", priority=priority)

link_mys = on_startswith("绑定mys", priority=priority)
link_uid = on_startswith("绑定uid", priority=priority)

month_data = on_command("每月统计", priority=priority)
daily_data = on_command("当前状态", priority=priority)

add_ck = on_startswith("添加", permission=PRIVATE_FRIEND, priority=priority)

search = on_command("查询", permission=GROUP, priority=priority)
get_sign = on_command("签到", priority=priority)
check = on_command("校验全部Cookies", priority=priority)


FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH, 'mys')
INDEX_PATH = os.path.join(FILE2_PATH, 'index')
Texture_PATH = os.path.join(FILE2_PATH, 'texture2d')

avatar_json = {
    "Albedo": "阿贝多",
    "Ambor": "安柏",
    "Barbara": "芭芭拉",
    "Beidou": "北斗",
    "Bennett": "班尼特",
    "Chongyun": "重云",
    "Diluc": "迪卢克",
    "Diona": "迪奥娜",
    "Eula": "优菈",
    "Fischl": "菲谢尔",
    "Ganyu": "甘雨",
    "Hutao": "胡桃",
    "Jean": "琴",
    "Kazuha": "枫原万叶",
    "Kaeya": "凯亚",
    "Ayaka": "神里绫华",
    "Keqing": "刻晴",
    "Klee": "可莉",
    "Lisa": "丽莎",
    "Mona": "莫娜",
    "Ningguang": "凝光",
    "Noel": "诺艾尔",
    "Qiqi": "七七",
    "Razor": "雷泽",
    "Rosaria": "罗莎莉亚",
    "Sucrose": "砂糖",
    "Tartaglia": "达达利亚",
    "Venti": "温迪",
    "Xiangling": "香菱",
    "Xiao": "魈",
    "Xingqiu": "行秋",
    "Xinyan": "辛焱",
    "Yanfei": "烟绯",
    "Zhongli": "钟离",
    "Yoimiya": "宵宫",
    "Sayu": "早柚",
    "Shogun": "雷电将军",
    "Aloy": "埃洛伊",
    "Sara": "九条裟罗",
    "Kokomi": "珊瑚宫心海",
    "Shenhe":"申鹤"
}

daily_im = '''
*数据刷新可能存在一定延迟，请以当前游戏实际数据为准{}
==============
原粹树脂：{}/{}{}
每日委托：{}/{} 奖励{}领取
周本减半：{}/{}
洞天宝钱：{}
探索派遣：
总数/完成/上限：{}/{}/{}
{}'''

month_im = '''
==============
{}
UID：{}
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
原石收入组成：
{}=============='''

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

@get_audio.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('语音', "").replace(' ', "")
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))

    if name == "列表":
        im = Message(f'[CQ:image,file=file:///{os.path.join(INDEX_PATH,"语音.png")}]')
        await get_audio.send(im)
    elif name == "":
        return
    else:
        audioid = re.findall(r"[0-9]+", message)[0]
        if audioid in audio_json:
            audioid = random.choice(audio_json[audioid])
        url = await GetAudioInfo(name,audioid)
        audio = BytesIO(requests.get(url).content)
        audios = 'base64://' + b64encode(audio.getvalue()).decode()
        resultmes = Message(f"[CQ:record,file={audios}]")
        try:
            await get_audio.send(resultmes)
        except nonebot.adapters.cqhttp.exception.ActionFailed:
            await get_audio.send("不存在该语音ID或者不存在该角色。")

@get_lots.handle()
async def _(bot: Bot, event: Event):
    qid = event.sender.user_id
    raw_data = await get_alots(qid)
    im = base64.b64decode(raw_data).decode("utf-8")
    await get_lots.send(im)

@get_weapon.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('武器', "")
    message = message.replace(' ', "")
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r"[0-9]+", message)
    if len(level) == 1:
        im = await weapon_wiki(name,level=level[0])
    else:
        im = await weapon_wiki(name)
    await get_weapon.send(im)

@get_enemies.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('原魔', "").replace(' ', "")
    im = await enemies_wiki(message)
    await get_enemies.send(im)

@get_talents.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('天赋', "")
    message = message.replace(' ', "")
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    num = re.findall(r"[0-9]+", message)
    if len(num) == 1:
        im = await char_wiki(name,"talents",num[0])
    else:
        im = "参数不正确。"
    await get_talents.send(im)

async def enemies_wiki(name):
    raw_data = await GetEnemiesInfo(name)
    reward = ""
    for i in raw_data["rewardpreview"]:
        reward += i["name"] + "：" + str(round(i["count"]*100,4)) + "%" if "count" in i.keys() else i["name"] + "：" + "可能"
        reward += "\n"
    im = "【{}】\n——{}——\n类型：{}\n信息：{}\n掉落物：\n{}".format(raw_data["name"],raw_data["specialname"],
                                                    raw_data["category"],raw_data["description"],reward)
    return im

@get_char.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('角色', "")
    message = message.replace(' ', "")
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    level = re.findall(r"[0-9]+", message)
    if len(level) == 1:
        im = await char_wiki(name,"char",level=level[0])
    else:
        im = await char_wiki(name)
    await get_char.send(im)

@get_cost.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('材料', "")
    message = message.replace(' ', "")
    im = await char_wiki(message,"costs")
    await get_weapon.send(im)

@get_polar.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('命座', "")
    message = message.replace(' ', "")
    num = int(re.findall(r"\d+", message)[0])  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if num <= 0 or num > 6:
        await get_weapon.finish("你家{}有{}命？".format(m, num))
    im = await char_wiki(m, "constellations", num)
    await get_weapon.send(im)

@draw_event.scheduled_job('cron', hour='2')
async def draw_event():
    await draw_event_pic()

@get_event.handle()
async def _(bot: Bot, event: Event):
    #await draw_event_pic()
    img_path = os.path.join(FILE2_PATH,"event.jpg")
    while(1):
        if os.path.exists(img_path):
            im = Message(f'[CQ:image,file=file:///{os.path.abspath(img_path)}]')
            break
        else:
            await draw_event_pic()
    await get_event.send(im)

# 每日零点清空cookies使用缓存


@delet_cache.scheduled_job('cron', hour='0')
async def delete():
    deletecache()

# 每日零点半进行米游社签到


@daily_sign.scheduled_job('cron', hour='0', minute="30")
async def _():
    await dailysign()


async def dailysign():
    (bot,) = nonebot.get_bots().values()
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    cursor = c.execute(
        "SELECT *  FROM NewCookiesTable WHERE StatusB != ?", ("off",))
    c_data = cursor.fetchall()
    for row in c_data:
        im = await sign(str(row[0]))
        if row[4] == "on":
            await bot.call_api(api='send_private_msg',
                                user_id=row[2], message=im)
        else:
            await bot.call_api(
                api='send_group_msg', group_id=row[4], message=f"[CQ:at,qq={row[2]}]\n{im}")
        await asyncio.sleep(7)

# 每隔半小时检测树脂是否超过设定值


@resin_notic.scheduled_job('interval', minutes=30)
async def push():
    (bot,) = nonebot.get_bots().values()
    daily_data = await daily()
    if daily_data != None:
        for i in daily_data:
            if i['gid'] == "on":
                await bot.call_api(api='send_private_msg', **{'user_id': i['qid'], 'message': i['message']})
            else:
                await bot.call_api(api='send_group_msg', **{'group_id': i['gid'], 'message': f"[CQ:at,qq={i['qid']}]" + "\n" + i['message']})
    else:
        pass


@add_ck.handle()
async def _(bot: Bot, event: Event):
    try:
        mes = str(event.get_message()).strip().replace('添加', "")
        aid = re.search(r"account_id=(\d*)", mes)
        mysid_data = aid.group(0).split('=')
        mysid = mysid_data[1]
        cookie = ';'.join(filter(lambda x: x.split('=')[0] in [
                          "cookie_token", "account_id"], [i.strip() for i in mes.split(';')]))
        mys_data = await GetMysInfo(mysid, cookie)
        for i in mys_data['data']['list']:
            if i['game_id'] != 2:
                mys_data['data']['list'].remove(i)
        uid = mys_data['data']['list'][0]['game_role_id']
        await cookiesDB(uid, cookie, event.sender.user_id)
        await add_ck.send(f'添加Cookies成功！Cookies属于个人重要信息，如果你是在不知情的情况下添加，请马上修改米游社账户密码，保护个人隐私！')
    except:
        await add_ck.send('校验失败！请输入正确的Cookies！')

# 开启 自动签到 和 推送树脂提醒 功能


@open_switch.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('开启', "")
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

    qid = event.sender.user_id
    at = re.search(r"\[CQ:at,qq=(\d*)\]", message)

    if m == "自动签到":
        try:
            if at and qid in superusers:
                qid = at.group(1)
            elif at and at.group(1) != qid:
                await close_switch.send("你没有权限。", at_sender=True)
                return
            else:
                pass
            gid = event.get_session_id().split("_")[1] if len(
                event.get_session_id().split("_")) == 3 else "on"
            uid = await selectDB(qid, mode="uid")
            im = await OpenPush(int(uid[0]), qid, str(gid), "StatusB")
            await open_switch.send(im, at_sender=True)
        except:
            await open_switch.send("未绑定uid信息！", at_sender=True)
    elif m == "推送":
        try:
            if at and qid in superusers:
                qid = at.group(1)
            elif at and at.group(1) != qid:
                await close_switch.send("你没有权限。", at_sender=True)
                return
            else:
                pass
            gid = event.get_session_id().split("_")[1] if len(
                event.get_session_id().split("_")) == 3 else "on"
            uid = await selectDB(qid, mode="uid")
            im = await OpenPush(int(uid[0]), qid, str(gid), "StatusA")
            await open_switch.send(im, at_sender=True)
        except:
            await open_switch.send("未绑定uid信息！", at_sender=True)

# 关闭 自动签到 和 推送树脂提醒 功能


@close_switch.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('关闭', "")
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))

    qid = event.sender.user_id
    at = re.search(r"\[CQ:at,qq=(\d*)\]", message)

    if m == "自动签到":
        try:
            if at and qid in superusers:
                qid = at.group(1)
            elif at and at.group(1) != qid:
                await close_switch.send("你没有权限。", at_sender=True)
                return
            else:
                pass
            uid = await selectDB(qid, mode="uid")
            im = await OpenPush(int(uid[0]), qid, "off", "StatusB")
            await close_switch.send(im, at_sender=True)
        except:
            await close_switch.send("未绑定uid信息！", at_sender=True)
    elif m == "推送":
        try:
            if at and qid in superusers:
                qid = at.group(1)
            elif at and at.group(1) != qid:
                await close_switch.send("你没有权限。", at_sender=True)
                return
            else:
                pass
            uid = await selectDB(qid, mode="uid")
            im = await OpenPush(int(uid[0]), qid, "off", "StatusA")
            await close_switch.send(im, at_sender=True)
        except:
            await close_switch.send("未绑定uid信息！", at_sender=True)

# 群聊内 每月统计 功能


@month_data.handle()
async def _(bot: Bot, event: Event):
    try:
        qid = event.sender.user_id
        uid = await selectDB(qid, mode="uid")
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
            group_str = group_str + \
                i['action'] + "：" + str(i['num']) + \
                "（" + str(i['percent']) + "%）" + '\n'

        im = month_im.format(nickname, uid, day_stone, day_mora, lastday_stone, lastday_mora,
                             month_stone, month_mora, lastmonth_stone, lastmonth_mora, group_str)
        await month_data.send(im, at_sender=True)
    except Exception as e:
        nonebot.logger.warning(e.with_traceback)
        await month_data.send('未找到绑定信息', at_sender=True)

# 群聊内 签到 功能


@get_sign.handle()
async def _(bot: Bot, event: Event):
    try:
        qid = event.sender.user_id
        uid = await selectDB(qid, mode="uid")
        uid = uid[0]
        im = await sign(uid)
    except TypeError:
        im = "没有找到绑定信息。"
    except Exception as e:
        nonebot.logger.warning(e.with_traceback)
        im = "发生错误。"
    finally:
        await get_sign.send(im, at_sender=True)

# 群聊内 校验Cookies 是否正常的功能，不正常自动删掉


@check.handle()
async def _(bot: Bot, event: Event):
    im = await CheckDB()
    await check.send(im)

# 群聊内 查询当前树脂状态以及派遣状态 的命令


@daily_data.handle()
async def _(bot: Bot, event: Event):
    try:
        uid = await selectDB(event.sender.user_id, mode="uid")
        uid = uid[0]
        mes = await daily("ask", uid)
        im = mes[0]['message']
    except Exception as e:
        nonebot.logger.warning(e.with_traceback)
        im = "没有找到绑定信息。"

    await daily_data.send(im, at_sender=True)

# 群聊内 查询uid 的命令


@get_uid_info.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('uid', "")
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", message)
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if m == "深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image)
                await get_uid_info.send(im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid, event.sender.nickname, image)
                await get_uid_info.send(im, at_sender=True)
        except:
            await get_uid_info.send('深渊输入错误！')
    elif m == "上期深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 2, "2")
                await get_uid_info.send(im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid, event.sender.nickname, image, 2, "2")
                await get_uid_info.send(im, at_sender=True)
        except:
            await get_uid_info.send(im, '深渊输入错误！')
    else:
        try:
            im = await draw_pic(uid, event.sender.nickname, image, 2)
            await get_uid_info.send(im, at_sender=True)
        except Exception as e:
            nonebot.logger.error("发生错误 {}，请检查日志。".format(e))
            nonebot.logger.warning(e.with_traceback)
            await get_uid_info.send('输入错误！')

# 群聊内 绑定uid 的命令，会绑定至当前qq号上


@link_uid.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('绑定uid', "")
    uid = re.findall(r"\d+", message)[0]  # str
    await connectDB(event.sender.user_id, uid)
    await link_uid.send('绑定uid成功！', at_sender=True)

# 群聊内 绑定米游社通行证 的命令，会绑定至当前qq号上，和绑定uid不冲突，两者可以同时绑定


@link_mys.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('绑定mys', "")
    mys = re.findall(r"\d+", message)[0]  # str
    await connectDB(event.sender.user_id, None, mys)
    await link_mys.send('绑定米游社id成功！', at_sender=True)

# 群聊内 绑定过uid/mysid的情况下，可以查询，默认优先调用米游社通行证，多出世界等级一个参数


@search.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('查询', "")
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", message)
    at = re.search(r"\[CQ:at,qq=(\d*)\]", message)
    if at:
        qid = at.group(1)
        mi = await bot.call_api('get_group_member_info', **{'group_id': event.group_id, 'user_id': qid})
        nickname = mi["nickname"]
        uid = await selectDB(qid)
        message = message.replace(at.group(0), '')
    else:
        nickname = event.sender.nickname
        uid = await selectDB(event.sender.user_id)

    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if uid:
        if m == "深渊":
            try:
                if len(re.findall(r"\d+", message)) == 1:
                    floor_num = re.findall(r"\d+", message)[0]
                    im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1])
                    await search.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid[0], nickname, image, uid[1])
                    await search.send(im, at_sender=True)
            except:
                await search.send('获取失败，请检查 cookie 及网络状态。')
        elif m == "上期深渊":
            try:
                if len(re.findall(r"\d+", message)) == 1:
                    floor_num = re.findall(r"\d+", message)[0]
                    im = await draw_abyss_pic(uid[0], nickname, floor_num, image, uid[1], "2")
                    await search.send(im, at_sender=True)
                else:
                    im = await draw_abyss0_pic(uid[0], nickname, image, uid[1], "2")
                    await search.send(im, at_sender=True)
            except:
                await search.send('获取失败，请检查数据状态。')
        elif m == "词云":
            try:
                im = await draw_wordcloud(uid[0], image, uid[1])
                await search.send(im, at_sender=True)
            except:
                await search.send('遇到错误！')
        elif m == "":
            try:
                bg = await draw_pic(uid[0], nickname, image, uid[1])
                await search.send(bg, at_sender=True)
            except:
                await search.send('输入错误！')
        else:
            pass
    else:
        await search.send('未找到绑定记录！')

# 群聊内 查询米游社通行证 的命令


@get_mys_info.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip().replace(
        ' ', "").replace('mys', "")
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", message)
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    if m == "深渊":
        try:
            if len(re.findall(r"\d+", message)) == 2:
                floor_num = re.findall(r"\d+", message)[1]
                im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 3)
                await get_mys_info.send(im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid, event.sender.nickname, image, 3)
                await get_mys_info.send(im, at_sender=True)
        except:
            await get_mys_info.send('深渊输入错误！')
    elif m == "上期深渊":
        try:
            if len(re.findall(r"\d+", message)) == 1:
                floor_num = re.findall(r"\d+", message)[0]
                im = await draw_abyss_pic(uid, event.sender.nickname, floor_num, image, 3, "2")
                await get_mys_info.send(im, at_sender=True)
            else:
                im = await draw_abyss0_pic(uid, event.sender.nickname, image, 3, "2")
                await get_mys_info.send(im, at_sender=True)
        except:
            await get_mys_info.send('深渊输入错误！')
    else:
        try:
            im = await draw_pic(uid, event.sender.nickname, image, 3)
            await get_mys_info.send(im, at_sender=True)
        except:
            await get_mys_info.send('输入错误！')

# 签到函数
async def sign(uid):
    try:
        sign_data = await MysSign(uid)
        sign_info = await GetSignInfo(uid)
        sign_info = sign_info['data']
        sign_list = await GetSignList()
        status = sign_data['message']
        getitem = sign_list['data']['awards'][int(
            sign_info['total_sign_day'])-1]['name']
        getnum = sign_list['data']['awards'][int(
            sign_info['total_sign_day'])-1]['cnt']
        get_im = f"本次签到获得{getitem}x{getnum}"
        if status == "OK" and sign_info['is_sign'] == True:
            mes_im = "签到成功"
        else:
            mes_im = status
        sign_missed = sign_info['sign_cnt_missed']
        im = mes_im + "!" + "\n" + get_im + "\n" + f"本月漏签次数：{sign_missed}"
    except:
        im = "签到失败，请检查Cookies是否失效。"
    return im

# 统计状态函数


async def daily(mode="push", uid=None):

    def seconds2hours(seconds: int) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)

    temp_list = []
    conn = sqlite3.connect('ID_DATA.db')
    c = conn.cursor()
    if mode == "push":
        cursor = c.execute(
            "SELECT *  FROM NewCookiesTable WHERE StatusA != ?", ("off",))
        c_data = cursor.fetchall()
    elif mode == "ask":
        c_data = ([uid, 0, 0, 0, 0, 0, 0],)

    for row in c_data:
        raw_data = await GetDaily(str(row[0]))
        if raw_data["retcode"] != 0:
            temp_list.append(
                {"qid": row[2], "gid": row[3], "message": "你的推送状态有误；可能是uid绑定错误或没有在米游社打开“实时便筏”功能。"})
        else:
            dailydata = raw_data["data"]
            current_resin = dailydata['current_resin']

            if current_resin >= row[6]:
                tip = ''

                if row[1] != 0:
                    tip = "\n==============\n你的树脂快满了！"
                max_resin = dailydata['max_resin']
                rec_time = ''
                # print(dailydata)
                if current_resin < 160:
                    resin_recovery_time = seconds2hours(
                        dailydata['resin_recovery_time'])
                    next_resin_rec_time = seconds2hours(
                        8 * 60 - ((dailydata['max_resin'] - dailydata['current_resin']) * 8 * 60 - int(dailydata['resin_recovery_time'])))
                    rec_time = f' ({next_resin_rec_time}/{resin_recovery_time})'

                finished_task_num = dailydata['finished_task_num']
                total_task_num = dailydata['total_task_num']
                is_extra_got = '已' if dailydata['is_extra_task_reward_received'] else '未'

                resin_discount_num_limit = dailydata['resin_discount_num_limit']
                used_resin_discount_num = resin_discount_num_limit - \
                    dailydata['remain_resin_discount_num']

                current_expedition_num = dailydata['current_expedition_num']
                max_expedition_num = dailydata['max_expedition_num']
                finished_expedition_num = 0
                expedition_info: list[str] = []
                for expedition in dailydata['expeditions']:
                    avatar: str = expedition['avatar_side_icon'][89:-4]
                    try:
                        avatar_name: str = avatar_json[avatar]
                    except KeyError:
                        avatar_name: str = avatar

                    if expedition['status'] == 'Finished':
                        expedition_info.append(f"{avatar_name} 探索完成")
                        finished_expedition_num += 1
                    else:
                        remained_timed: str = seconds2hours(
                            expedition['remained_time'])
                        expedition_info.append(
                            f"{avatar_name} 剩余时间{remained_timed}")
                expedition_data = "\n".join(expedition_info)

                coin = str(dailydata["current_home_coin"]) + "/" + str(dailydata["max_home_coin"])
                send_mes = daily_im.format(tip, current_resin, max_resin, rec_time, finished_task_num, total_task_num, is_extra_got, used_resin_discount_num,
                                        resin_discount_num_limit, coin,current_expedition_num, finished_expedition_num, max_expedition_num, expedition_data)

                temp_list.append(
                    {"qid": row[2], "gid": row[3], "message": send_mes})
    return temp_list


async def weapon_wiki(name,level = None):
    data = await GetWeaponInfo(name)
    if level:
        data2 = await GetWeaponInfo(name,level+"plus" if level else level)
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


async def char_wiki(name, mode="char", level=None):
    data = await GetCharInfo(name, mode, level if mode == "char" else None)
    if mode == "char":
        if isinstance(data,str):
            raw_data = data.replace("[","").replace("\n","").replace("]","").replace(" ","").replace("'","").split(',')
            if data.replace("\n","").replace(" ","") == "undefined":
                im = "不存在该角色或类型。"
            else:
                im = ','.join(raw_data)
        elif level:
            data2 = await GetCharInfo(name, mode)
            sp = data2["substat"] + "：" + '%.1f%%' % (data["specialized"] * 100) if data2["substat"] != "元素精通" else data2["substat"] + "：" + str(math.floor(data["specialized"]))
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

async def rule_all_recheck(Bot, Event, T_State):
    return Event.sender.user_id in superusers


all_recheck = on_command("全部重签", rule=Rule(
    rule_all_recheck), priority=priority)


@all_recheck.handle()
async def _(bot: Bot, event: Event):
    await all_recheck.send("已开始执行")
    await dailysign()

async def init():
    logger.info("正在更新活动列表")
    try:
        await draw_event_pic()
    except:
        logger.error("活动列表更新失败\n"+traceback.format_exc())
    else:
        logger.info("活动列表更新完毕")

asyncio.get_event_loop().run_until_complete(init())
