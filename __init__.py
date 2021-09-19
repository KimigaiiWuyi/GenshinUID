import re

#from nonebot import on_command
#from nonebot.adapters.cqhttp import Event, Bot, Message

from .getImg import draw_pic,draw_abyss_pic
from .getData import GetMysInfo
from .getDB import connectDB,selectDB

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

import urllib

sv = Service('genshinuid')
bot = get_bot()

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
Texture_PATH = os.path.join(FILE2_PATH,'texture2d')

@sv.on_prefix('uid')
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "深渊":
        try:
            floor_num = re.findall(r"\d+", message)[1]
            im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image)
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
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = await selectDB(ev.sender['user_id'])
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if uid:
        if m == "深渊":
            try:
                floor_num = re.findall(r"\d+", message)[0]
                im = await draw_abyss_pic(uid[0],ev.sender['nickname'],floor_num,image,uid[1])
                await bot.send(ev, im, at_sender=True)
            except:
                await bot.send(ev,'输入错误！')
        elif m == "":
            try:
                bg = await draw_pic(uid[0],ev.sender['nickname'],image,uid[1])
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
            floor_num = re.findall(r"\d+", message)[1]
            im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image,3)
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

