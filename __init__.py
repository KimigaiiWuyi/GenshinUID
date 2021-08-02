import re

#from nonebot import on_command
#from nonebot.adapters.cqhttp import Event, Bot, Message

from .getImg import draw_pic

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
    try:
        uid = re.findall(r"\d+", message)[0]  # str
        im = await draw_pic(uid,ev.sender['nickname'],image)
        await bot.send(ev, im, at_sender=True)
    except:
        await bot.send(ev,'输入错误！')
