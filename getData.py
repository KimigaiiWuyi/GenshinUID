# https://github.com/Womsxd/YuanShen_User_Info
#import hashlib
#import json
#import random
#import string
import sys
#import time

from httpx import AsyncClient

from .getDB import cookiesDB,cacheDB

from nonebot import *
import json
from random import randint
import requests,random,os,json,re
from hoshino import Service,R,priv,util
from hoshino.typing import MessageSegment,CQEvent, HoshinoBot
from hoshino.util import FreqLimiter,pic2b64
import hoshino
import asyncio
import time
import string
import random
import hashlib
import requests
import os
from  PIL  import   Image,ImageFont,ImageDraw
from io import BytesIO
import base64

mhyVersion = "2.11.1"

def md5(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()

def DSGet(q = "",b = None):
    if b:
        br = json.dumps(b)
    else:
        br = ""
    s = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    t = str(int(time.time()))
    r = str(random.randint(100000, 200000))
    c = md5("salt=" + s + "&t=" + t + "&r=" + r + "&b=" + br + "&q=" + q)
    return t + "," + r + "," + c

async def GetInfo(Uid,ServerID="cn_gf01",Schedule_type="1",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/index?role_id=" + Uid + "&server=" + ServerID,
                headers={
                    #'Accept': 'application/json, text/plain, */*',
                    'DS': DSGet("role_id=" + Uid + "&server=" + ServerID),
                    #'Origin': 'https://webstatic.mihoyo.com',
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    #'Accept-Encoding': 'gzip, deflate',
                    #'Accept-Language': 'zh-CN,en-US;q=0.8',
                    #'X-Requested-With': 'com.mihoyo.hyperion',
                    "Cookie": await cacheDB(Uid,1,mysid)})
            data = json.loads(req.text)
        return data
    except:
        print("访问失败，请重试！")
        sys.exit(1)

async def GetSpiralAbyssInfo(Uid, ServerID="cn_gf01",Schedule_type="1",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/app/genshin/api/spiralAbyss?schedule_type=" + Schedule_type + "&server="+ ServerID +"&role_id=" + Uid,
                headers={
                    'Accept': 'application/json, text/plain, */*',
                    'DS': DSGet("role_id=" + Uid + "&schedule_type=" + Schedule_type + "&server="+ ServerID),
                    'Origin': 'https://webstatic.mihoyo.com',
                    'Cookie': await cacheDB(Uid,1,mysid),                
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'zh-CN,en-US;q=0.8',
                    'X-Requested-With': 'com.mihoyo.hyperion'
                    }
                )
            data = json.loads(req.text)
        return data
    except:
        print("1访问失败，请重试！")
        sys.exit(1)


async def GetCharacter(Uid,Character_ids, ServerID="cn_gf01",mysid = None):
    if Uid[0] == '5':
        ServerID = "cn_qd01"
    try:
        req = requests.post(
            url = "https://api-takumi.mihoyo.com/game_record/app/genshin/api/character",
            headers={
                'Accept': 'application/json, text/plain, */*',
                'DS': DSGet('',{"character_ids": Character_ids ,"role_id": Uid ,"server": ServerID}),
                'Origin': 'https://webstatic.mihoyo.com',
                'Cookie': await cacheDB(Uid,1,mysid),
                'x-rpc-app_version': mhyVersion,
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                'x-rpc-client_type': '5',
                'Referer': 'https://webstatic.mihoyo.com/',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,en-US;q=0.8',
                'X-Requested-With': 'com.mihoyo.hyperion'
            },
            json = {"character_ids": Character_ids ,"role_id": Uid ,"server": ServerID}
        )
        data2 = json.loads(req.text)
        return data2
    except:
        print("访问失败，请重试！")
        sys.exit(1)

async def GetMysInfo(mysid):
    try:
        async with AsyncClient() as client:
            req = await client.get(
                url="https://api-takumi.mihoyo.com/game_record/card/wapi/getGameRecordCard?uid=" + mysid,
                headers={
                    #'Accept': 'application/json, text/plain, */*',
                    'DS': DSGet("uid="+mysid),
                    #'Origin': 'https://webstatic.mihoyo.com',
                    'x-rpc-app_version': mhyVersion,
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.11.1',
                    'x-rpc-client_type': '5',
                    'Referer': 'https://webstatic.mihoyo.com/',
                    #'Accept-Encoding': 'gzip, deflate',
                    #'Accept-Language': 'zh-CN,en-US;q=0.8',
                    #'X-Requested-With': 'com.mihoyo.hyperion',
                    "Cookie": await cacheDB(mysid,2)})
            data = json.loads(req.text)
        return [data,mysid]
    except:
        print ("访问失败，请重试！")
        return