import time
from base64 import b64encode
from io import BytesIO

import urllib
import math

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .getDB import GetInfo,GetCharacter,GetSpiralAbyssInfo,GetMysInfo

from nonebot import *
from nonebot.adapters.cqhttp import *

import os
import json
import random

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
CHAR_PATH = os.path.join(FILE2_PATH,'chars')
CHAR_DONE_PATH = os.path.join(FILE2_PATH,'char_done')
CHAR_WEAPON_PATH = os.path.join(FILE2_PATH,'char_weapon')
TEXT_PATH = os.path.join(FILE2_PATH,'texture2d')
WEAPON_PATH = os.path.join(FILE2_PATH,'weapon')
BG_PATH = os.path.join(FILE2_PATH,'bg')

def ys_font(size):
    return ImageFont.truetype(os.path.join(FILE2_PATH,"yuanshen.ttf"), size=size)

def get_char_pic(id,url):
    urllib.request.urlretrieve(f'{url}', os.path.join(CHAR_PATH,f'{id}.png'))

def get_chardone_pic(id,url,star):
    urllib.request.urlretrieve(f'{url}', os.path.join(CHAR_DONE_PATH,f'{id}.png'))
    char_path = os.path.join(CHAR_DONE_PATH,f'{id}.png')
    if star == 4:
        star4_1_path = os.path.join(TEXT_PATH,'4star_1.png')
        star4_2_path = os.path.join(TEXT_PATH,'4star_2.png')
        star4_1 = Image.open(star4_1_path)
        star4_2 = Image.open(star4_2_path)
        char_path = os.path.join(CHAR_DONE_PATH,str(id) + '.png')
        char_img = Image.open(char_path)
        char_img = char_img.resize((104,104),Image.ANTIALIAS)
        star4_1.paste(char_img,(12,15),char_img)
        star4_1.paste(star4_2,(0,0),star4_2)
        star4_1.save(os.path.join(CHAR_DONE_PATH,str(id) + '.png'))
    else:
        star5_1_path = os.path.join(TEXT_PATH,'5star_1.png')
        star5_2_path = os.path.join(TEXT_PATH,'5star_2.png')
        star5_1 = Image.open(star5_1_path)
        star5_2 = Image.open(star5_2_path)
        char_path = os.path.join(CHAR_DONE_PATH,str(id) + '.png')
        char_img = Image.open(char_path)
        char_img = char_img.resize((104,104),Image.ANTIALIAS)
        star5_1.paste(char_img,(12,15),char_img)
        star5_1.paste(star5_2,(0,0),star5_2)
        star5_1.save(os.path.join(CHAR_DONE_PATH,str(id) + '.png'))
    
def get_weapon_pic(url):
    urllib.request.urlretrieve(url, os.path.join(WEAPON_PATH, url.split('/')[-1]))

async def draw_abyss0_pic(uid,nickname,image = None,mode = 2,date = "1"):
    if mode == 3:
        mys_data = await GetMysInfo(uid)
        mysid_data = mys_data[1]
        mys_data = mys_data[0]
        for i in mys_data['data']['list']:
            if i['data'][0]['name'] != '活跃天数':
                mys_data['data']['list'].remove(i)
        uid = mys_data['data']['list'][0]['game_role_id']
        nickname = mys_data['data']['list'][0]['nickname']
        #role_region = mys_data['data']['list'][0]['region']
        role_level = mys_data['data']['list'][0]['level']
        raw_data = await GetSpiralAbyssInfo(uid,"cn_gf01",date,mysid_data)
        raw_char_data = await GetInfo(uid,"cn_gf01",date,mysid_data)
    else:
        raw_data = await GetSpiralAbyssInfo(uid,"cn_gf01",date)
        raw_char_data = await GetInfo(uid,"cn_gf01",date)

    if (raw_data["retcode"] != 0):
        if (raw_data["retcode"] == 10001):
            return ("Cookie错误/过期，请重置Cookie")
        elif (raw_data["retcode"] == 10101):
            return ("当前cookies已达到30人上限！")
        elif (raw_data["retcode"] == 10102):
            return ("当前查询id已经设置了隐私，无法查询！")
        return (
            "Api报错，返回内容为：\r\n"
            + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
        )
    else:
        pass

    raw_data = raw_data["data"]
    raw_char_data = raw_char_data['data']["avatars"]

    is_edit = False
    if image != None:
        image_file= image.group(1)
        image_data = image.group(2)
        urllib.request.urlretrieve(f'{image_data}', os.path.join(TEXT_PATH,nickname + '.png'))
        is_edit = True

    bg_list = random.choice([x for x in os.listdir(BG_PATH)
            if os.path.isfile(os.path.join(BG_PATH, x))])

    bg2_path = os.path.join(BG_PATH,bg_list)

    abyss0_path = os.path.join(TEXT_PATH,"abyss_0.png")
    abyss2_path = os.path.join(TEXT_PATH,"abyss_2.png")
    abyss3_path = os.path.join(TEXT_PATH,"abyss_3.png")
    abyss_star0_path = os.path.join(TEXT_PATH,"abyss_star0.png")
    abyss_star1_path = os.path.join(TEXT_PATH,"abyss_star1.png")

    floors_data = raw_data['floors'][-1]
    levels_num = len(floors_data['levels'])

    based_w = 900
    based_h = 880+levels_num*315
    based_scale = '%.3f' % (based_w/based_h)

    if is_edit == True:
        bg_path_edit = os.path.join(TEXT_PATH,f"{nickname}.png")
    else:
        bg_path_edit = bg2_path

    edit_bg = Image.open(bg_path_edit)
    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h*float(scale_f))
    new_h = math.ceil(based_w/float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h),Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h),Image.ANTIALIAS)

    bg_img = bg_img2.crop((0, 0, based_w, based_h))

    x1, y1 = 45, 271
    radius = 10
    cropped_img1 = bg_img.crop((x1, y1, 857, 831))
    blurred_img1 = cropped_img1.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
    bg_img.paste(blurred_img1, (x1, y1), create_rounded_rectangle_mask(cropped_img1,radius))

    for i in range(0,len(floors_data['levels'])):
        x2, y2 = 45, 850 + 315*i 
        radius = 10
        cropped_img2 = bg_img.crop((x2, y2, 855, 1145+315*i))
        blurred_img2 = cropped_img2.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
        bg_img.paste(blurred_img2, (x2, y2), create_rounded_rectangle_mask(cropped_img2,radius))

    abyss0 = Image.open(abyss0_path)
    abyss3 = Image.open(abyss3_path)
    abyss_star0 = Image.open(abyss_star0_path)
    abyss_star1 = Image.open(abyss_star1_path)

    for i in range(0,4):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["reveal_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["reveal_rank"][i]["avatar_id"],raw_data["reveal_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["reveal_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["reveal_rank"][i]["avatar_id"]:
                char_draw.text((63.5,117),f'{str(raw_data["reveal_rank"][i]["value"])}次',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (70 + 123*i,331)
        abyss0.paste(char_img,char_crop,char_img)
    
    for i in range(0,1):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["damage_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["damage_rank"][i]["avatar_id"],raw_data["damage_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["damage_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["damage_rank"][i]["avatar_id"]:
                char_draw.text((63.5,117),f'{str(raw_data["damage_rank"][i]["value"])}',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (592,331)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,3):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["defeat_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["defeat_rank"][i]["avatar_id"],raw_data["defeat_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["defeat_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["defeat_rank"][i]["avatar_id"]:
                char_draw.text((63.5,117),f'{str(raw_data["defeat_rank"][i]["value"])}',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (70 + 123*i,503)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,3):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["take_damage_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["take_damage_rank"][i]["avatar_id"],raw_data["take_damage_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["take_damage_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["take_damage_rank"][i]["avatar_id"]:
                char_draw.text((63.5,117),f'{str(raw_data["take_damage_rank"][i]["value"])}',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (466 + 123*i,503)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,3):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["normal_skill_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["normal_skill_rank"][i]["avatar_id"],raw_data["normal_skill_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["normal_skill_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["normal_skill_rank"][i]["avatar_id"]:
                char_draw.text((63.5,117),f'{str(raw_data["normal_skill_rank"][i]["value"])}',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (70 + 123*i,676)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,3):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(raw_data["energy_skill_rank"][i]["avatar_id"]) + ".png")):
            get_chardone_pic(raw_data["energy_skill_rank"][i]["avatar_id"],raw_data["energy_skill_rank"][i]["avatar_icon"],raw_data["reveal_rank"][i]["rarity"])
        char = os.path.join(CHAR_DONE_PATH,str(raw_data["energy_skill_rank"][i]["avatar_id"]) + ".png")
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data["energy_skill_rank"][i]["avatar_id"]:
                char_draw.text((63.5,118),f'{str(raw_data["energy_skill_rank"][i]["value"])}',(21,21,21),ys_font(18), anchor="mm")
                char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                    char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                else:
                    char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
        char_crop = (466 + 123*i,676)
        abyss0.paste(char_img,char_crop,char_img)

    bg_img.paste(abyss0,(0,0),abyss0)

    for j in range(0,len(floors_data["levels"])):
        abyss2 = Image.open(abyss2_path)
        num_1 = 0
        for i in floors_data['levels'][j]['battles'][0]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")):
                get_chardone_pic(i['id'],i['icon'],i['rarity'])
            char = os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40,108),f'Lv.{str(k["level"])}',(21,21,21),ys_font(18))
                    char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                    if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                        char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                    else:
                        char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
            char_crop = (70 + 125*(num_1%4),46)
            abyss2.paste(char_img,char_crop,char_img)
            num_1 = num_1 + 1
        num_2 = 0
        for i in floors_data['levels'][j]['battles'][1]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")):
                get_chardone_pic(i['id'],i['icon'],i['rarity'])
            char = os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40,108),f'Lv.{str(k["level"])}',(21,21,21),ys_font(18))
                    char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                    if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                        char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                    else:
                        char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
            char_crop = (70 + 125*(num_2%4),180)
            abyss2.paste(char_img,char_crop,char_img)
            num_2 = num_2 + 1
        star_num = floors_data['levels'][j]['star']
        if star_num == 1:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star0,(685,155),abyss_star0)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        elif star_num == 0:
            abyss2.paste(abyss_star0,(640,155),abyss_star0)
            abyss2.paste(abyss_star0,(685,155),abyss_star0)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        elif star_num == 2:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star1,(685,155),abyss_star1)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        else:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star1,(685,155),abyss_star1)
            abyss2.paste(abyss_star1,(730,155),abyss_star1)
        abyss2_text_draw = ImageDraw.Draw(abyss2)
        abyss2_text_draw.text((87,30),f"第{j+1}间", (20,20,20), ys_font(21))
        timeStamp1 = int(floors_data['levels'][j]['battles'][0]['timestamp'])
        timeStamp2 = int(floors_data['levels'][j]['battles'][1]['timestamp'])
        timeArray1 = time.localtime(timeStamp1)
        timeArray2 = time.localtime(timeStamp2)
        otherStyleTime1 = time.strftime("%Y--%m--%d %H:%M:%S", timeArray1)
        otherStyleTime2 = time.strftime("%Y--%m--%d %H:%M:%S", timeArray2)
        abyss2_text_draw.text((167,33), f"{otherStyleTime1}/{otherStyleTime2}", (40,40,40), ys_font(19))
        bg_img.paste(abyss2,(0,830+j*315),abyss2)
    
    bg_img.paste(abyss3,(0,len(floors_data["levels"])*315+840),abyss3)
 
    text_draw = ImageDraw.Draw(bg_img)

    text_draw.text((250, 85), f"{nickname}", (217,217,217), ys_font(32))
    text_draw.text((260, 125), 'UID ' + f"{uid}", (217,217,217), ys_font(14))

    text_draw.text((690, 52),raw_data['max_floor'], (65, 65, 65), ys_font(26))
    text_draw.text((690, 97),str(raw_data['total_battle_times']), (65, 65, 65), ys_font(26))
    text_draw.text((690, 142),str(raw_data['total_star']), (65, 65, 65), ys_font(26))

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    #bg_img.save(result_buffer, format='PNG')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = Message(f"[CQ:image,file={imgmes}]")
    return resultmes

async def draw_abyss_pic(uid,nickname,floor_num,image = None,mode = 2,date = "1"):
    if mode == 3:
        mys_data = await GetMysInfo(uid)
        mysid_data = mys_data[1]
        mys_data = mys_data[0]
        for i in mys_data['data']['list']:
            if i['data'][0]['name'] != '活跃天数':
                mys_data['data']['list'].remove(i)
        uid = mys_data['data']['list'][0]['game_role_id']
        nickname = mys_data['data']['list'][0]['nickname']
        #role_region = mys_data['data']['list'][0]['region']
        role_level = mys_data['data']['list'][0]['level']
        raw_data = await GetSpiralAbyssInfo(uid,"cn_gf01",date,mysid_data)
        raw_char_data = await GetInfo(uid,"cn_gf01",date,mysid_data)
    else:
        raw_data = await GetSpiralAbyssInfo(uid,"cn_gf01",date)
        raw_char_data = await GetInfo(uid,"cn_gf01",date)

    if (raw_data["retcode"] != 0):
        if (raw_data["retcode"] == 10001):
            return ("Cookie错误/过期，请重置Cookie")
        elif (raw_data["retcode"] == 10101):
            return ("当前cookies已达到30人上限！")
        elif (raw_data["retcode"] == 10102):
            return ("当前查询id已经设置了隐私，无法查询！")
        return (
            "Api报错，返回内容为：\r\n"
            + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
        )
    else:
        pass

    
    is_edit = False
    if image != None:
        image_file= image.group(1)
        image_data = image.group(2)
        urllib.request.urlretrieve(f'{image_data}', os.path.join(TEXT_PATH,nickname + '.png'))
        is_edit = True

    raw_data = raw_data["data"]
    raw_char_data = raw_char_data['data']["avatars"]

    floors_data = raw_data['floors']

    based_data = []
    for i in floors_data:
        if str(i['index']) == floor_num:
            based_data = i

    #floor_star = based_data['star']
    #floors1_star = based_data['levels'][0]['star']
    #floors2_star = based_data['levels'][1]['star']
    #floors3_star = based_data['levels'][2]['star']
    #start_time1 = based_data['levels'][0]['battles'][0]['timestamp']
    #start_time2 = based_data['levels'][0]['battles'][1]['timestamp']

    bg_list = random.choice([x for x in os.listdir(BG_PATH)
               if os.path.isfile(os.path.join(BG_PATH, x))])

    bg2_path = os.path.join(BG_PATH,bg_list)

    abyss1_path = os.path.join(TEXT_PATH,"abyss_1.png")
    abyss2_path = os.path.join(TEXT_PATH,"abyss_2.png")
    abyss3_path = os.path.join(TEXT_PATH,"abyss_3.png")
    abyss_star0_path = os.path.join(TEXT_PATH,"abyss_star0.png")
    abyss_star1_path = os.path.join(TEXT_PATH,"abyss_star1.png")

    levels_num = len(based_data['levels'])

    based_w = 900
    based_h = 240+levels_num*340
    based_scale = '%.3f' % (based_w/based_h)

    if is_edit == True:
        bg_path_edit = os.path.join(TEXT_PATH,f"{nickname}.png")
    else:
        bg_path_edit = bg2_path

    edit_bg = Image.open(bg_path_edit)
    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h*float(scale_f))
    new_h = math.ceil(based_w/float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h),Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h),Image.ANTIALIAS)

    bg_img = bg_img2.crop((0, 0, based_w, based_h))

    for i in range(0,len(based_data['levels'])):
        x, y = 45, 220 + 340*i 
        radius = 10
        cropped_img = bg_img.crop((x, y, 855, 517+340*i))
        blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
        bg_img.paste(blurred_img, (x, y), create_rounded_rectangle_mask(cropped_img,radius))

    abyss1 = Image.open(abyss1_path)
    abyss3 = Image.open(abyss3_path)
    abyss_star0 = Image.open(abyss_star0_path)
    abyss_star1 = Image.open(abyss_star1_path)

    bg_img.paste(abyss1,(0,0),abyss1)

    for j in range(0,len(based_data['levels'])):
        abyss2 = Image.open(abyss2_path)
        num_1 = 0
        avatars = based_data['levels'][j]['battles'][0]['avatars'] + based_data['levels'][j]['battles'][1]['avatars']
        for i in based_data['levels'][j]['battles'][0]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")):
                get_chardone_pic(i['id'],i['icon'],i['rarity'])
            char = os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40,108),f'Lv.{str(k["level"])}',(21,21,21),ys_font(18))
                    char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                    if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                        char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                    else:
                        char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
            char_crop = (70 + 125*(num_1%4),46)
            abyss2.paste(char_img,char_crop,char_img)
            num_1 = num_1 + 1
        num_2 = 0
        for i in based_data['levels'][j]['battles'][1]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")):
                get_chardone_pic(i['id'],i['icon'],i['rarity'])
            char = os.path.join(CHAR_DONE_PATH,str(i['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40,108),f'Lv.{str(k["level"])}',(21,21,21),ys_font(18))
                    char_draw.text((95.3,19),f'{str(k["actived_constellation_num"])}','white',ys_font(18))
                    if str(k["fetter"]) == "10" or str(k["name"]) == "旅行者":
                        char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
                    else:
                        char_draw.text((95.3,40.5),f'{str(k["fetter"])}',(21,21,21),ys_font(18))
            char_crop = (70 + 125*(num_2%4),180)
            abyss2.paste(char_img,char_crop,char_img)
            num_2 = num_2 + 1
        star_num = based_data['levels'][j]['star']
        if star_num == 1:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star0,(685,155),abyss_star0)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        elif star_num == 0:
            abyss2.paste(abyss_star0,(640,155),abyss_star0)
            abyss2.paste(abyss_star0,(685,155),abyss_star0)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        elif star_num == 2:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star1,(685,155),abyss_star1)
            abyss2.paste(abyss_star0,(730,155),abyss_star0)
        else:
            abyss2.paste(abyss_star1,(640,155),abyss_star1)
            abyss2.paste(abyss_star1,(685,155),abyss_star1)
            abyss2.paste(abyss_star1,(730,155),abyss_star1)
        abyss2_text_draw = ImageDraw.Draw(abyss2)
        abyss2_text_draw.text((87,30),f"第{j+1}间", (20,20,20), ys_font(21))
        timeStamp1 = int(based_data['levels'][j]['battles'][0]['timestamp'])
        timeStamp2 = int(based_data['levels'][j]['battles'][1]['timestamp'])
        timeArray1 = time.localtime(timeStamp1)
        timeArray2 = time.localtime(timeStamp2)
        otherStyleTime1 = time.strftime("%Y--%m--%d %H:%M:%S", timeArray1)
        otherStyleTime2 = time.strftime("%Y--%m--%d %H:%M:%S", timeArray2)
        abyss2_text_draw.text((167,33), f"{otherStyleTime1}/{otherStyleTime2}", (40,40,40), ys_font(19))
        bg_img.paste(abyss2,(0,200+j*340),abyss2)
    
    bg_img.paste(abyss3,(0,len(based_data['levels'])*340+200),abyss3)
 
    text_draw = ImageDraw.Draw(bg_img)

    text_draw.text((210,77), f"{nickname}", (217,217,217), ys_font(32))
    text_draw.text((228, 110), 'UID ' + f"{uid}", (217,217,217), ys_font(14))
    if floor_num == "9":
        text_draw.text((687, 67), f"{floor_num}", (29,30,63), ys_font(50))
    else:
        text_draw.text((670, 67), f"{floor_num}", (29,30,63), ys_font(50))

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    #bg_img.save(result_buffer, format='PNG')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = Message(f"[CQ:image,file={imgmes}]")
    return resultmes

async def draw_pic(uid,nickname,image = None,mode = 2,role_level = None):
    if mode == 3:
        mys_data = await GetMysInfo(uid)
        mysid_data = mys_data[1]
        mys_data = mys_data[0]
        for i in mys_data['data']['list']:
            if i['data'][0]['name'] != '活跃天数':
                mys_data['data']['list'].remove(i)
        uid = mys_data['data']['list'][0]['game_role_id']
        nickname = mys_data['data']['list'][0]['nickname']
        role_level = mys_data['data']['list'][0]['level']
        raw_data = await GetInfo(uid,"cn_gf01","1",mysid_data)
    else:
        raw_data = await GetInfo(uid)
        
    if (raw_data["retcode"] != 0):
        if (raw_data["retcode"] == 10001):
            return ("Cookie错误/过期，请重置Cookie")
        elif (raw_data["retcode"] == 10101):
            return ("当前cookies已达到30人上限！")
        elif (raw_data["retcode"] == 10102):
            return ("当前查询id已经设置了隐私，无法查询！")
        return (
            "Api报错，返回内容为：\r\n"
            + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
        )
    else:
        pass

    bg_list = random.choice([x for x in os.listdir(BG_PATH)
               if os.path.isfile(os.path.join(BG_PATH, x))])

    bg2_path = os.path.join(BG_PATH,bg_list)

    if role_level:
        panle1_path = os.path.join(TEXT_PATH,"mys_1.png")
    else:
        panle1_path = os.path.join(TEXT_PATH,"panle_1.png")
    panle2_path = os.path.join(TEXT_PATH,"panle_2.png")
    panle3_path = os.path.join(TEXT_PATH,"panle_3.png")
    
    raw_data = raw_data['data']
    char_data = raw_data["avatars"]
    char_num = len(raw_data["avatars"])
    if mode == 2:
        char_ids = []
        char_rawdata = []
        
        for i in char_data:
            char_ids.append(i["id"])

        char_rawdata = await GetCharacter(uid,char_ids)
        char_datas = char_rawdata["data"]["avatars"]

    elif mode == 3:
        char_ids = []
        char_rawdata = []
        
        for i in char_data:
            char_ids.append(i["id"])

        char_rawdata = await GetCharacter(uid,char_ids,"cn_gf01",mysid_data)
        char_datas = char_rawdata["data"]["avatars"]
        
    char_hang = 1 + (char_num-1)//6
    char_lie = char_num%6

    based_w = 900
    based_h = 890+char_hang*130
    based_scale = '%.3f' % (based_w/based_h)

    is_edit = False
    if image:
        image_file= image.group(1)
        image_data = image.group(2)
        urllib.request.urlretrieve(f'{image_data}', os.path.join(TEXT_PATH,nickname + '.png'))
        is_edit = True

    if is_edit == True:
        bg_path_edit = os.path.join(TEXT_PATH,f"{nickname}.png")
    else:
        bg_path_edit = bg2_path
        
    edit_bg = Image.open(bg_path_edit)
    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h*float(scale_f))
    new_h = math.ceil(based_w/float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h),Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h),Image.ANTIALIAS)

    bg_img = bg_img2.crop((0, 0, 900, based_h))

    x, y = 45, 268 
    radius = 50
    cropped_img = bg_img.crop((x, y, 856, based_h-45))
    blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
    bg_img.paste(blurred_img, (x, y), create_rounded_rectangle_mask(cropped_img,radius))

    panle1 = Image.open(panle1_path)
    panle2 = Image.open(panle2_path)
    panle3 = Image.open(panle3_path)

    bg_img.paste(panle1,(0,0),panle1)
    for i in range(0,char_hang):
        bg_img.paste(panle2,(0,800+i*130),panle2)
    bg_img.paste(panle3,(0,char_hang*130+800),panle3)
 
    text_draw = ImageDraw.Draw(bg_img)

    if role_level:
        text_draw.text((310,193), f"{role_level}", (29,30,63), ys_font(20))

    text_draw.text((242.6,128.3), f"{nickname}", (217,217,217), ys_font(32))
    text_draw.text((260.6, 165.3), 'UID ' + f"{uid}", (217,217,217), ys_font(14))

    text_draw.text((640, 94.8),str(raw_data['stats']['active_day_number']), (65, 65, 65), ys_font(26))
    text_draw.text((640, 139.3),str(raw_data['stats']['achievement_number']), (65, 65, 65), ys_font(26))
    text_draw.text((640, 183.9),raw_data['stats']['spiral_abyss'], (65, 65, 65), ys_font(26))

    text_draw.text((258, 382.4),str(raw_data['stats']['magic_chest_number']), (65, 65, 65), ys_font(24))
    text_draw.text((258, 442),str(raw_data['stats']['common_chest_number']),(65, 65, 65), ys_font(24))
    text_draw.text((258, 501.6),str(raw_data['stats']['exquisite_chest_number']),(65, 65, 65), ys_font(24))
    text_draw.text((258, 561.2),str(raw_data['stats']['precious_chest_number']), (65, 65, 65), ys_font(24))
    text_draw.text((258, 620.8),str(raw_data['stats']['luxurious_chest_number']), (65, 65, 65), ys_font(24))

    text_draw.text((258, 680.4),str(raw_data['stats']['avatar_number']),(65, 65, 65), ys_font(24))

    text_draw.text((745, 474.5),str(raw_data['stats']['way_point_number']),(65, 65, 65), ys_font(24))
    text_draw.text((745, 514),str(raw_data['stats']['domain_number']),(65, 65, 65), ys_font(24))

    #蒙德
    text_draw.text((490, 370),str(raw_data['world_explorations'][3]['exploration_percentage']/10) + '%',(65, 65, 65), ys_font(22))
    text_draw.text((490, 400),'lv.' + str(raw_data['world_explorations'][3]['level']),(65, 65, 65), ys_font(22))
    text_draw.text((513, 430), str(raw_data['stats']['anemoculus_number']), (65, 65, 65), ys_font(22))

    #璃月
    text_draw.text((490, 490),str(raw_data['world_explorations'][2]['exploration_percentage']/10) + '%',(65, 65, 65), ys_font(22))
    text_draw.text((490, 520),'lv.' + str(raw_data['world_explorations'][2]['level']),(65, 65, 65), ys_font(22))
    text_draw.text((513, 550), str(raw_data['stats']['geoculus_number']), (65, 65, 65), ys_font(22))

    #雪山
    text_draw.text((745, 379.5),str(raw_data['world_explorations'][1]['exploration_percentage']/10) + '%',(65, 65, 65), ys_font(22))
    text_draw.text((745, 413.1),'lv.' + str(raw_data['world_explorations'][1]['level']),(65, 65, 65), ys_font(22))

    #稻妻
    text_draw.text((490, 608),str(raw_data['world_explorations'][0]['exploration_percentage']/10) + '%',(65, 65, 65), ys_font(22))
    text_draw.text((490, 635),'lv.' + str(raw_data['world_explorations'][0]['level']),(65, 65, 65), ys_font(22))
    text_draw.text((490, 662),'lv.' + str(raw_data['world_explorations'][0]['offerings'][0]['level']),(65, 65, 65), ys_font(22))
    text_draw.text((513, 689), str(raw_data['stats']['electroculus_number']), (65, 65, 65), ys_font(22))

    if len(raw_data['homes']):
        text_draw.text((693, 572.4),'lv.' + str(raw_data['homes'][0]['level']),(65, 65, 65), ys_font(22))
        text_draw.text((693, 610.4),str(raw_data['homes'][0]['visit_num']),(65, 65, 65), ys_font(22))
        text_draw.text((693, 648.4),str(raw_data['homes'][0]['item_num']),(65, 65, 65), ys_font(22))
        text_draw.text((693, 686.4),str(raw_data['homes'][0]['comfort_num']),(65, 65, 65), ys_font(22))
    else:
        text_draw.text((693, 572.4),"未开",(65, 65, 65), ys_font(22))
        text_draw.text((693, 610.4),"未开",(65, 65, 65), ys_font(22))
        text_draw.text((693, 648.4),"未开",(65, 65, 65), ys_font(22))
        text_draw.text((693, 686.4),"未开",(65, 65, 65), ys_font(22))
    
    if mode == 1:
        char_data.sort(key=lambda x: (-x['rarity'],-x['level'],-x['fetter']))
        num = 0
        for i in raw_data['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH,str(char_data[num]['id']) + ".png")):
                get_char_pic(char_data[num]['id'],char_data[num]['image'],char_data[num]['rarity'])
            char = os.path.join(CHAR_DONE_PATH,str(char_data[num]['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((40,108),f'Lv.{str(char_data[num]["level"])}',(21,21,21),ys_font(18))
            char_draw.text((95.3,19),f'{str(char_data[num]["actived_constellation_num"])}','white',ys_font(18))
            if str(char_data[num]["fetter"]) == "10" or str(char_data[num]["name"]) == "旅行者":
                char_draw.text((93,41.5),"♥",(21,21,21),ys_font(15))
            else:
                char_draw.text((95.3,40.5),f'{str(char_data[num]["fetter"])}',(21,21,21),ys_font(18))
        
            char_crop = (68+129*(num%6),800+130*(num//6))
            bg_img.paste(char_img,char_crop,char_img)
            num = num+1
    else:
        charpic_mask_path = os.path.join(TEXT_PATH,"charpic_mask.png")
        weaponpic_mask_path = os.path.join(TEXT_PATH,"weaponpic_mask.png")
        s5s1_path = os.path.join(TEXT_PATH,"5s_1.png")
        s5s2_path = os.path.join(TEXT_PATH,"5s_2.png")
        s5s3_path = os.path.join(TEXT_PATH,"5s_3.png")
        s5s4_path = os.path.join(TEXT_PATH,"5s_4.png")
        s4s1_path = os.path.join(TEXT_PATH,"4s_1.png")
        s4s2_path = os.path.join(TEXT_PATH,"4s_2.png")
        s4s3_path = os.path.join(TEXT_PATH,"4s_3.png")
        s4s4_path = os.path.join(TEXT_PATH,"4s_4.png")

        s3s3_path = os.path.join(TEXT_PATH,"3s_3.png")
        s2s3_path = os.path.join(TEXT_PATH,"2s_3.png")
        s1s3_path = os.path.join(TEXT_PATH,"1s_3.png")

        charpic_mask = Image.open(charpic_mask_path)
        weaponpic_mask = Image.open(weaponpic_mask_path)
        s5s1=Image.open(s5s1_path)
        s5s2=Image.open(s5s2_path)
        s5s3=Image.open(s5s3_path)
        s5s4=Image.open(s5s4_path)
        s4s1=Image.open(s4s1_path)
        s4s2=Image.open(s4s2_path)
        s4s3=Image.open(s4s3_path)
        s4s4=Image.open(s4s4_path)

        s3s3=Image.open(s3s3_path)
        s2s3=Image.open(s2s3_path)
        s1s3=Image.open(s1s3_path)

        num = 0
        char_datas.sort(key=lambda x: (-x['rarity'],-x['level'],-x['fetter']))

        for i in char_datas:
            char_mingzuo = 0
            for k in i['constellations']:
                if  k['is_actived'] == True:
                    char_mingzuo += 1

            char_name = i["name"]
            char_id = i["id"]
            char_level = i["level"]
            char_fetter = i['fetter']
            char_rarity = i['rarity']

            char_weapon = i['weapon']
            char_weapon_star = i['weapon']['rarity']
            char_weapon_name = i['weapon']['name']
            char_weapon_level = i['weapon']['level']
            char_weapon_jinglian = i['weapon']['affix_level']
            char_weapon_icon = i['weapon']['icon']

            if not os.path.exists(os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))):
                get_weapon_pic(char_weapon_icon)
            if not os.path.exists(os.path.join(CHAR_PATH,str(i['id']) + ".png")):
                get_char_pic(i['id'],i['icon'])

            char = os.path.join(CHAR_PATH,str(char_id) + ".png")
            weapon = os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))

            char_img = Image.open(char)
            char_img = char_img.resize((100,100),Image.ANTIALIAS)
            weapon_img = Image.open(weapon)
            weapon_img = weapon_img.resize((47,47),Image.ANTIALIAS)

            charpic = Image.new("RGBA", (125, 140))

            if char_rarity == 5:
                charpic.paste(s5s1,(0,0),s5s1)
                baseda = Image.new("RGBA", (100, 100))
                cc = Image.composite(char_img, baseda, charpic_mask)
                charpic.paste(cc,(6,15),cc)
                charpic.paste(s5s2,(0,0),s5s2)
                if char_weapon_star == 5:
                    charpic.paste(s5s3,(0,0),s5s3)
                elif char_weapon_star == 4:
                    charpic.paste(s4s3,(0,0),s4s3)
                elif char_weapon_star == 3:
                    charpic.paste(s3s3,(0,0),s3s3)
                elif char_weapon_star == 2:
                    charpic.paste(s2s3,(0,0),s2s3)
                elif char_weapon_star == 1:
                    charpic.paste(s1s3,(0,0),s1s3)
                basedb = Image.new("RGBA", (47, 47))
                dd = Image.composite(weapon_img, basedb, weaponpic_mask)
                charpic.paste(dd,(69,62),dd)
                charpic.paste(s5s4,(0,0),s5s4)

            else:
                charpic.paste(s4s1,(0,0),s4s1)
                baseda = Image.new("RGBA", (100, 100))
                cc = Image.composite(char_img, baseda, charpic_mask)
                charpic.paste(cc,(6,15),cc)
                charpic.paste(s4s2,(0,0),s4s2)
                if char_weapon_star == 5:
                    charpic.paste(s5s3,(0,0),s5s3)
                elif char_weapon_star == 4:
                    charpic.paste(s4s3,(0,0),s4s3)
                elif char_weapon_star == 3:
                    charpic.paste(s3s3,(0,0),s3s3)
                elif char_weapon_star == 2:
                    charpic.paste(s2s3,(0,0),s2s3)
                elif char_weapon_star == 1:
                    charpic.paste(s1s3,(0,0),s1s3)
                basedb = Image.new("RGBA", (47, 47))
                dd = Image.composite(weapon_img, basedb, weaponpic_mask)
                charpic.paste(dd,(69,62),dd)
                charpic.paste(s4s4,(0,0),s4s4)

            char_draw = ImageDraw.Draw(charpic)
            char_draw.text((38,106),f'Lv.{str(char_level)}',(21,21,21),ys_font(18))
            char_draw.text((104.5,91.5),f'{str(char_weapon_jinglian)}','white',ys_font(10))
            char_draw.text((99,19.5),f'{str(char_mingzuo)}','white',ys_font(18))
            if str(i["fetter"]) == "10" or str(char_name) == "旅行者":
                char_draw.text((98,42),"♥",(21,21,21),ys_font(14))
            else:
                char_draw.text((100,41),f'{str(char_fetter)}',(21,21,21),ys_font(16))
            
            char_crop = (68+129*(num%6),800+130*(num//6))
            bg_img.paste(charpic,char_crop,charpic)
            num = num+1

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = Message(f"[CQ:image,file={imgmes}]")
    return resultmes

def create_rounded_rectangle_mask(rectangle, radius):
    solid_fill =  (50,50,50,255) 
    i = Image.new("RGBA",rectangle.size,(0,0,0,0))

    corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
    draw = ImageDraw.Draw(corner)
    draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill = solid_fill)

    mx,my = rectangle.size

    i.paste(corner, (0, 0), corner)
    i.paste(corner.rotate(90), (0, my - radius),corner.rotate(90))
    i.paste(corner.rotate(180), (mx - radius,   my - radius),corner.rotate(180))
    i.paste(corner.rotate(270), (mx - radius, 0),corner.rotate(270))

    draw = ImageDraw.Draw(i)
    draw.rectangle( [(radius,0),(mx-radius,my)],fill=solid_fill)
    draw.rectangle( [(0,radius),(mx,my-radius)],fill=solid_fill)

    return i