# from nonebot import on_command
# from nonebot.adapters.onebot.v11 import Event, Bot, Message

import os
import re

from hoshino import Service
from hoshino.typing import CQEvent, HoshinoBot
from nonebot import *

from .getImg import draw_pic, draw_char_pic, new_draw_pic, draw_abyss_pic

sv = Service('genshinuid')
bot = get_bot()

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH, 'mys')
Texture_PATH = os.path.join(FILE2_PATH, 'texture2d')


@sv.on_prefix('uid')
async def _(bot: HoshinoBot, ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    m = ''.join(re.findall('[\u4e00-\u9fa5]',message))
    if m == "角色":
        #try:
        im = await draw_char_pic(uid,ev.sender['nickname'],image)
        await bot.send(ev, im, at_sender=True)
        #except:
        #    await bot.send(ev,'输入也许错误！')
    elif m == "深渊":
        try:
            floor_num = re.findall(r"\d+", message)[1]
            im = await draw_abyss_pic(uid,ev.sender['nickname'],floor_num,image)
            await bot.send(ev, im, at_sender=True)
        except:
            await bot.send(ev,'深渊输入错误！')
    else:
        #try:
        im = await new_draw_pic(uid,ev.sender['nickname'],image)
        await bot.send(ev, im, at_sender=True)
        #except:
        #    await bot.send(ev,'输入错误！')


@sv.on_prefix('UID')
async def _(bot:HoshinoBot,  ev: CQEvent):
    image = re.search(r"\[CQ:image,file=(.*),url=(.*)\]", str(ev.message))
    message = ev.message.extract_plain_text()
    uid = re.findall(r"\d+", message)[0]  # str
    try:
        im = await draw_pic(uid,ev.sender['nickname'],image)
        await bot.send(ev, im, at_sender=True)
    except:
        await bot.send(ev,'输入错误！')

