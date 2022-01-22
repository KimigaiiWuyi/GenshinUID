import asyncio
import os
import re
import sqlite3,random
import base64

import nonebot
from nonebot import *
from nonebot.adapters import Bot, Event
from nonebot.adapters.cqhttp import *
from nonebot.adapters.cqhttp import Message, MessageSegment, permission, utils
from nonebot.rule import Rule


from .getDB import (CheckDB, GetAward, GetCharInfo, GetDaily, GetMysInfo, GetAudioInfo,
                    GetSignInfo, GetSignList, GetWeaponInfo, MysSign, OpenPush,
                    connectDB, cookiesDB, deletecache, selectDB, get_alots)
from .getImg import draw_abyss0_pic, draw_abyss_pic, draw_event_pic, draw_pic, draw_wordcloud
from .getMes import foods_wiki, artifacts_wiki, enemies_wiki, sign, daily, weapon_wiki, char_wiki, audio_wiki, award, deal_ck

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
get_artifacts = on_startswith("圣遗物", priority=priority)
get_food = on_startswith("食物", priority=priority)

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

@get_audio.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('语音', "").replace(' ', "")
    name = ''.join(re.findall('[\u4e00-\u9fa5]', message))
    im = await audio_wiki(name,message)
    try:
        await get_audio.send(Message(im))
    except nonebot.adapters.cqhttp.exception.ActionFailed:
        await get_audio.send("不存在该语音ID或者不存在该角色。")
    except:
        await get_audio.send("可能是FFmpeg环境未配置。")

@get_lots.handle()
async def _(bot: Bot, event: Event):
    qid = event.sender.user_id
    raw_data = await get_alots(qid)
    im = base64.b64decode(raw_data).decode("utf-8")
    await get_lots.send(im)

@get_enemies.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('原魔', "").replace(' ', "")
    im = await enemies_wiki(message)
    await get_enemies.send(im)

@get_food.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('食物', "").replace(' ', "")
    im = await foods_wiki(message)
    await get_food.send(im)

@get_artifacts.handle()
async def _(bot: Bot, event: Event):
    message = str(event.get_message()).strip()
    message = message.replace('圣遗物', "").replace(' ', "")
    im = await artifacts_wiki(message)
    await get_artifacts.send(im)

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
    img_path = os.path.join(FILE2_PATH,"event.jpg")
    while(1):
        if os.path.exists(img_path):
            im = Message(f'[CQ:image,file=file://{img_path}]')
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
    temp_list = []
    for row in c_data:
        if row[4] == "on":
            im = await sign(str(row[0]))
            await bot.call_api(api='send_private_msg',
                                user_id=row[2], message=im)
        else:
            im = await sign(str(row[0]))
            message = f"[CQ:at,qq={row[2]}]\n{im}"
            for i in temp_list:
                if row[4] == i["push_group"]:
                    i["push_message"] = i["push_message"] + "\n" + message
                    break
            else:
                temp_list.append({"push_group":row[4],"push_message":message})
        await asyncio.sleep(6+random.randint(0,2))
    for i in temp_list:
        await bot.call_api(
            api='send_group_msg', group_id=i["push_group"], message=i["push_message"])
        await asyncio.sleep(3+random.randint(0,2))

# 每隔半小时检测树脂是否超过设定值
@resin_notic.scheduled_job('interval', hours=1)
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
        await deal_ck(mes,event.sender.user_id)
        await add_ck.send(f'添加Cookies成功！\nCookies属于个人重要信息，如果你是在不知情的情况下添加，请马上修改米游社账户密码，保护个人隐私！\n————\n如果需要【开启自动签到】和【开启推送】还需要使用命令“绑定uid”绑定你的uid。\n例如：绑定uid123456789。')
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
        im = await award(uid)
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


async def rule_all_recheck(Bot, Event, T_State):
    return Event.sender.user_id in superusers


all_recheck = on_command("全部重签", rule=Rule(
    rule_all_recheck), priority=priority)

@all_recheck.handle()
async def _(bot: Bot, event: Event):
    await all_recheck.send("已开始执行")
    await dailysign()
