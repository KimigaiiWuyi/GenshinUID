import time
from base64 import b64encode
from io import BytesIO

import urllib
import math
import threading
import requests
from pydantic.utils import import_string
from wordcloud import WordCloud
import numpy as np

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .getDB import GetInfo,GetCharacter,GetSpiralAbyssInfo,GetMysInfo,cacheDB,errorDB,GetGenshinEvent,OwnerCookies

from nonebot import *
from nonebot.adapters.cqhttp import *

import os
import json
import random

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
CHAR_PATH = os.path.join(FILE2_PATH,'chars')
CHAR_DONE_PATH = os.path.join(FILE2_PATH,'char_done')
CHAR_IMG_PATH = os.path.join(FILE2_PATH,'char_img')
REL_PATH = os.path.join(FILE2_PATH,'reliquaries')
CHAR_WEAPON_PATH = os.path.join(FILE2_PATH,'char_weapon')
TEXT_PATH = os.path.join(FILE2_PATH,'texture2d')
WEAPON_PATH = os.path.join(FILE2_PATH,'weapon')
BG_PATH = os.path.join(FILE2_PATH,'bg')

#config = get_driver().config
#use_new_get_chars_method=config.genshinuid_use_new_get_chars_method

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

def get_charimg_pic(url):
    urllib.request.urlretrieve(url, os.path.join(CHAR_IMG_PATH, url.split('/')[-1]))

def get_rel_pic(url):
    urllib.request.urlretrieve(url, os.path.join(REL_PATH, url.split('/')[-1]))

async def draw_wordcloud(uid,image = None,mode = 2):
    while 1:
        use_cookies = cacheDB(uid,mode-1)
        if use_cookies == '':
            return "绑定记录不存在。"
        elif use_cookies == "没有可以使用的Cookies！":
            return "没有可以使用的Cookies！"

        if mode == 3:
            mys_data = await GetMysInfo(uid,use_cookies)
            mysid_data = uid
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            role_level = mys_data['data']['list'][0]['level']
            raw_data = await GetInfo(uid,use_cookies)
            raw_Abyss_data = await GetSpiralAbyssInfo(uid,use_cookies)
        else:
            raw_Abyss_data = await GetSpiralAbyssInfo(uid,use_cookies)
            raw_data = await GetInfo(uid,use_cookies)
        
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

    raw_Abyss_data = raw_Abyss_data['data']
    raw_data = raw_data['data']

    char_data = raw_data["avatars"]
    char_num = len(raw_data["avatars"])

    char_datas = []
    def get_charid(start,end):
        for i in range(start,end):
            char_rawdata = GetCharacter(uid,[i],use_cookies)
        
            if char_rawdata["retcode"] == -1:
                pass
            else:
                char_datas.append(char_rawdata["data"]['avatars'][0])

    thread_list = []
    st = 8
    for i in range(0,8):
        thread = threading.Thread(target = get_charid,args = (10000002+i*st,10000002+(i+1)*st))
        thread_list.append(thread)

    for t in thread_list:
        t.setDaemon(True)
        t.start()
    
    for t in thread_list:
        t.join()

    weapons_datas = []
    for i in char_datas:
        weapons_datas.append(i['weapon'])
    
    l1_size = 2
    l2_size = 4
    l3_size = 6
    l4_size = 7
    l5_size = 10

    word_str = {}

    star4weapon = 0
    star5weapon = 0
    star5weaponcon = 0
    star3weapon = 0
    for i in weapons_datas:
        if i['rarity'] == 5:
            star5weapon += 1
            star5weaponcon += i['affix_level']
        elif i['rarity'] == 4:
            star4weapon += 1
        elif i['rarity'] == 3:
            star4weapon += 1

    g3d1 = 0
    ly3c = 0
    star5num = 0
    star5numcon = 0

    for i in char_datas:
        if i["name"] in ['雷电将军','温迪','钟离','枫原万叶']:
            g3d1 += 1
        if i["name"] in ['甘雨','魈','胡桃']:
            ly3c += 1
        if i['rarity'] == 5:
            star5num += 1
            if i['name'] != '旅行者':
                star5numcon += 1 + i['actived_constellation_num']

        if i["level"] >= 80:
            if i['name'] == "迪卢克":
                word_str["落魄了家人们"] = l3_size
            if i['name'] == "刻晴":
                word_str["斩尽牛杂"] = l3_size
            if i['name'] == "旅行者":
                word_str["旅行者真爱党"] = l3_size
        
        if i['actived_constellation_num'] == 6:
            if i['rarity'] == 5:
                if i['name'] == "旅行者":
                    word_str["满命{}".format(i['name'])] = l1_size
                if i['name'] == "魈":
                    word_str['魈深氪的救赎'] = l5_size
                if i['name'] == "甘雨":
                    word_str['璃月自走归终机'] = l5_size
                if i['name'] == "胡桃":
                    word_str['一波送走全送走'] = l5_size
                else:
                    word_str["满命{}".format(i['name'])] = l5_size
            else:
                word_str["满命{}".format(i['name'])] = l2_size

    game_time = time.mktime(time.strptime('20200915','%Y%m%d'))
    now_time = time.time()
    total_s = now_time - game_time
    total_d = (((total_s)/60)/60)/24

    if math.floor(total_d) - 5 <= raw_data['stats']['active_day_number']:
        word_str["开服玩家"] = l4_size

    if g3d1 >= 4:
        word_str["三神一帝"] = l3_size
    if ly3c >= 3:
        word_str["璃月3C"] = l3_size
    if star5num >= 16:
        word_str["五星众多"] = l3_size
    
    if len(weapons_datas) - star4weapon <= 3:
        word_str["武器基本四星"] = l3_size

    if raw_data['stats']['achievement_number'] // (star5weaponcon + star5numcon) >= 23:
        word_str["平民玩家"] = l2_size
    elif raw_data['stats']['achievement_number'] // (star5weaponcon + star5numcon) <= 15:
        word_str["氪金玩家"] = l3_size

    if raw_data['stats']['anemoculus_number'] + raw_data['stats']['geoculus_number'] + raw_data['stats']['electroculus_number'] == 378:
        word_str["全神瞳"] = l2_size
    if raw_data['world_explorations'][3]['exploration_percentage']+raw_data['world_explorations'][2]['exploration_percentage']+raw_data['world_explorations'][1]['exploration_percentage']+raw_data['world_explorations'][0]['exploration_percentage'] >= 3950:
        word_str["全探索"] = l4_size
    if raw_data['stats']['achievement_number'] >= 510:
        word_str["全成就"] = l5_size
    elif raw_data['stats']['achievement_number'] >= 490:
        word_str["成就达人"] = l3_size
    if raw_data['stats']['spiral_abyss'] == '12-3':
        word_str["深境的探究者"] = l2_size
    if len(raw_data['avatars']) >= 42:
        word_str["全角色"] = l3_size

    if raw_data['stats']['active_day_number'] <= 40:
        word_str["刚入坑"] = l1_size
    elif raw_data['stats']['active_day_number'] <= 100:
        word_str["初心者"] = l2_size
    elif raw_data['stats']['active_day_number'] <= 300:
        word_str["老玩家"] = l2_size

    if raw_data['stats']['active_day_number'] >=365 and raw_data['stats']['magic_chest_number'] + raw_data['stats']['common_chest_number']+raw_data['stats']['exquisite_chest_number']+raw_data['stats']['precious_chest_number']+raw_data['stats']['luxurious_chest_number'] <=2500:
        word_str["老咸鱼"] = l3_size
    if raw_data['stats']['magic_chest_number'] >= 46:
        word_str["迷失在黑夜里"] = l2_size
    if raw_data['homes'][0]['comfort_num'] >= 25000:
        word_str["团雀附体"] = l2_size

    if raw_Abyss_data["reveal_rank"] != []:
        if raw_Abyss_data['total_battle_times'] <= 12 and raw_Abyss_data['max_floor'] == '12-3':
            word_str["PVP资格证"] = l4_size
        if raw_Abyss_data["damage_rank"][0]["value"] >= 150000:
            word_str["这一击，贯穿星辰"] = l4_size
    else:
        pass

    bg_list = random.choice([x for x in os.listdir(BG_PATH)
               if os.path.isfile(os.path.join(BG_PATH, x))])

    bg2_path = os.path.join(BG_PATH,bg_list)

    based_w = 900
    based_h = 1000
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

    bg_img = bg_img2.crop((0, 0, based_w, based_h))

    x, y = 50, 153 
    radius = 50
    cropped_img = bg_img.crop((x, y, x+800, y+800))
    blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
    bg_img.paste(blurred_img, (x, y), create_rounded_rectangle_mask(cropped_img,radius))

    panle = Image.open(os.path.join(TEXT_PATH,'wordcloud_0.png'))

    mask = np.array(Image.open(os.path.join(TEXT_PATH,'wordcloudmask.png')))
    
    wc = WordCloud(
        font_path = os.path.join(FILE2_PATH,"yuanshen.ttf"),
        mask = mask,
        background_color="rgba(255, 255, 255, 0)",
        mode="RGBA",
        max_words=200,
        max_font_size=80
        #color_func=multi_color_func
        #color_func=similar_color_func
    ).generate_from_frequencies(word_str, max_font_size=100)

    image_produce = wc.to_image()

    bg_img.paste(panle,(0,0),panle)
    bg_img.paste(image_produce,(0,0),image_produce)
    bg_img = bg_img.convert('RGB')

    text_draw = ImageDraw.Draw(bg_img)
    text_draw.text((450, 105), 'UID ' + f"{uid}", (40,136,168), ys_font(26), anchor="mm")

    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = Message(f"[CQ:image,file={imgmes}]")
    return resultmes

def similar_color_func(word=None, font_size=None,
                       position=None, orientation=None,
                       font_path=None, random_state=None):
    h = 40 # 0 - 360
    s = 100 # 0 - 100
    l = random_state.randint(30, 70) # 0 - 100
    return "hsl({}, {}%, {}%)".format(h, s, l)

def multi_color_func(word=None, font_size=None,
                     position=None, orientation=None,
                     font_path=None, random_state=None):
    colors = [[4, 77, 82],
              [25, 74, 85],
              [82, 43, 84],
              [158, 48, 79]]
    rand = random_state.randint(0, len(colors) - 1)
    return "hsl({}, {}%, {}%)".format(colors[rand][0], colors[rand][1], colors[rand][2])

async def draw_abyss0_pic(uid,nickname,image = None,mode = 2,date = "1"):
    while 1:
        use_cookies = cacheDB(uid,mode-1)
        if use_cookies == '':
            return "绑定记录不存在。"
        elif use_cookies == "没有可以使用的Cookies！":
            return "没有可以使用的Cookies！"

        if mode == 3:
            mys_data = await GetMysInfo(uid,use_cookies)
            mysid_data = uid
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            #role_region = mys_data['data']['list'][0]['region']
            role_level = mys_data['data']['list'][0]['level']

        raw_data = await GetSpiralAbyssInfo(uid,use_cookies,date)
        raw_char_data = await GetInfo(uid,use_cookies)

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
    based_h = 660+levels_num*315
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

    x1, y1 = 65, 276
    radius = 15
    cropped_img1 = bg_img.crop((x1, y1, 836, 607))
    blurred_img1 = cropped_img1.filter(ImageFilter.GaussianBlur(5),).convert("RGBA")
    bg_img.paste(blurred_img1, (x1, y1), create_rounded_rectangle_mask(cropped_img1,radius))

    for i in range(0,len(floors_data['levels'])):
        x2, y2 = 65, 630 + 315*i 
        radius = 15
        cropped_img2 = bg_img.crop((x2, y2, 836, 925+315*i))
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
        char_crop = (82 + 130*i,300)
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
        char_crop = (685,470)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,1):
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
        char_crop = (82 + 123*i,470)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,1):
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
        char_crop = (232 + 123*i,470)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,1):
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
        char_crop = (382 + 123*i,470)
        abyss0.paste(char_img,char_crop,char_img)

    for i in range(0,1):
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
        char_crop = (532 + 123*i,470)
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
        bg_img.paste(abyss2,(0,605+j*315),abyss2)
    
    bg_img.paste(abyss3,(0,len(floors_data["levels"])*315+610),abyss3)
 
    text_draw = ImageDraw.Draw(bg_img)

    text_draw.text((250, 115), f"{nickname}", (217,217,217), ys_font(32))
    text_draw.text((260, 155), 'UID ' + f"{uid}", (217,217,217), ys_font(14))

    text_draw.text((690, 82),raw_data['max_floor'], (65, 65, 65), ys_font(26))
    text_draw.text((690, 127),str(raw_data['total_battle_times']), (65, 65, 65), ys_font(26))
    text_draw.text((690, 172),str(raw_data['total_star']), (65, 65, 65), ys_font(26))

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    #bg_img.save(result_buffer, format='PNG')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = Message(f"[CQ:image,file={imgmes}]")
    return resultmes

async def draw_abyss_pic(uid,nickname,floor_num,image = None,mode = 2,date = "1"):
    while 1:
        use_cookies = cacheDB(uid,mode-1)
        if use_cookies == '':
            return "绑定记录不存在。"
        elif use_cookies == "没有可以使用的Cookies！":
            return "没有可以使用的Cookies！"

        if mode == 3:
            mys_data = await GetMysInfo(uid,use_cookies)
            mysid_data = uid
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            #role_region = mys_data['data']['list'][0]['region']
            role_level = mys_data['data']['list'][0]['level']

        raw_data = await GetSpiralAbyssInfo(uid,use_cookies,date)
        raw_char_data = await GetInfo(uid,use_cookies)

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
        x, y = 65, 220 + 340*i 
        radius = 10
        cropped_img = bg_img.crop((x, y, 836, 517+340*i))
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
    #获取Cookies，如果没有能使用的则return
    while 1:
        use_cookies = cacheDB(uid,mode-1)
        if use_cookies == '':
            return "绑定记录不存在。"
        elif use_cookies == "没有可以使用的Cookies！":
            return "没有可以使用的Cookies！"

        if mode == 3:
            mys_data = await GetMysInfo(uid,use_cookies)
            mysid_data = uid
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            role_level = mys_data['data']['list'][0]['level']
            
        raw_data = await GetInfo(uid,use_cookies)
            
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
    
    #获取背景图片
    bg2_path = os.path.join(BG_PATH,random.choice([x for x in os.listdir(BG_PATH)
               if os.path.isfile(os.path.join(BG_PATH, x))]))
    
    if image:
        image_data = image.group(2)
        edit_bg = Image.open(BytesIO(requests.get(image_data).content))
    else:
        edit_bg = Image.open(bg2_path)
    
    #获取背景主色
    q = edit_bg.quantize(colors=3,method=2)
    bg_num_temp = 0
    for i in range(0,3):
        bg = tuple(q.getpalette()[i*3:(i*3)+3])
        bg_num = bg[0] + bg[1] + bg[2]
        if bg_num >= bg_num_temp:
            bg_num_temp = bg_num
            bg_color = (bg[0],bg[1],bg[2])
    
    #通过背景主色（bg_color）确定文字主色
    r =  140
    if max(*bg_color) > 255 - r:
        r *= -1
    new_color = (math.floor(bg_color[0] + r if bg_color[0] + r <= 255 else 255),
                 math.floor(bg_color[1] + r if bg_color[1] + r <= 255 else 255), 
                 math.floor(bg_color[2] + r if bg_color[2] + r <= 255 else 255))

    #确定texture2D路径
    panle1_path = os.path.join(TEXT_PATH,"panle_1.png")
    panle3_path = os.path.join(TEXT_PATH,"panle_3.png")

    avatar_bg_path = os.path.join(TEXT_PATH,"avatar_bg.png")
    avatar_fg_path = os.path.join(TEXT_PATH,"avatar_fg.png")

    all_mask_path = os.path.join(TEXT_PATH,"All_Mask.png")
    
    #记录数据
    raw_data = raw_data['data']
    char_data = raw_data["avatars"]
    
    char_datas = []
    char_ids = []
    char_rawdata = []

    for i in char_data:
        char_ids.append(i["id"])

    char_rawdata = GetCharacter(uid,char_ids,use_cookies)
    char_datas = char_rawdata["data"]["avatars"]

    #确定角色占用行数
    char_num = len(char_datas)
    char_hang = 1 + (char_num-1)//6 if char_num > 8 else char_num

    #确定整体图片的长宽
    based_w = 900
    based_h = 890+char_hang*130 if char_num > 8 else 890+char_hang*110
    based_scale = '%.3f' % (based_w/based_h)

    #通过确定的长宽比，缩放背景图片
    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h*float(scale_f))
    new_h = math.ceil(based_w/float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h),Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h),Image.ANTIALIAS)
    bg_img = bg_img2.crop((0, 0, 900, based_h))

    #转换遮罩的颜色、大小匹配，并paste上去
    all_mask = Image.open(all_mask_path).resize(bg_img.size,Image.ANTIALIAS)
    all_mask_img = Image.new("RGBA",(based_w,based_h),bg_color)
    bg_img.paste(all_mask_img,(0,0),all_mask)

    #操作图片
    panle1 = Image.open(panle1_path)
    panle3 = Image.open(panle3_path)
    avatar_bg = Image.open(avatar_bg_path)
    avatar_fg = Image.open(avatar_fg_path)

    #确定主体框架
    avatar_bg_color = Image.new("RGBA",(316,100),bg_color)
    panle1_color = Image.new("RGBA",(900,800),new_color)
    bg_img.paste(panle1_color,(0,0),panle1)
    bg_img.paste(panle3,(0,char_hang*130+800) if char_num > 8 else (0,char_hang*110+800),panle3)
    bg_img.paste(avatar_bg_color,(113,98),avatar_bg)
    bg_img.paste(avatar_fg,(114,95),avatar_fg)
 
    #绘制基础信息文字
    text_draw = ImageDraw.Draw(bg_img)

    if role_level:
        text_draw.text((140,200), "冒险等级：" + f"{role_level}", new_color, ys_font(20))

    text_draw.text((220,123), f"{nickname}", new_color, ys_font(32))
    text_draw.text((235, 163), 'UID ' + f"{uid}", new_color, ys_font(14))

    #活跃天数/成就数量/深渊信息
    text_draw.text((640, 94.8),str(raw_data['stats']['active_day_number']), new_color, ys_font(26))
    text_draw.text((640, 139.3),str(raw_data['stats']['achievement_number']), new_color, ys_font(26))
    text_draw.text((640, 183.9),raw_data['stats']['spiral_abyss'], new_color, ys_font(26))

    #宝箱
    text_draw.text((258, 375.4),str(raw_data['stats']['magic_chest_number']), new_color, ys_font(24))
    text_draw.text((258, 425.4),str(raw_data['stats']['common_chest_number']),new_color, ys_font(24))
    text_draw.text((258, 475.4),str(raw_data['stats']['exquisite_chest_number']),new_color, ys_font(24))
    text_draw.text((258, 525.4),str(raw_data['stats']['precious_chest_number']), new_color, ys_font(24))
    text_draw.text((258, 575.4),str(raw_data['stats']['luxurious_chest_number']), new_color, ys_font(24))

    #已获角色
    text_draw.text((740, 547),str(raw_data['stats']['avatar_number']),new_color, ys_font(24))

    #开启锚点和秘境数量
    text_draw.text((258, 625.4),str(raw_data['stats']['way_point_number']),new_color, ys_font(24))
    text_draw.text((258, 675.4),str(raw_data['stats']['domain_number']),new_color, ys_font(24))

    #蒙德
    text_draw.text((490, 370),str(raw_data['world_explorations'][4]['exploration_percentage']/10) + '%',new_color, ys_font(22))
    text_draw.text((490, 400),'lv.' + str(raw_data['world_explorations'][4]['level']),new_color, ys_font(22))
    text_draw.text((513, 430), str(raw_data['stats']['anemoculus_number']), new_color, ys_font(22))

    #璃月
    text_draw.text((490, 490),str(raw_data['world_explorations'][3]['exploration_percentage']/10) + '%',new_color, ys_font(22))
    text_draw.text((490, 520),'lv.' + str(raw_data['world_explorations'][3]['level']),new_color, ys_font(22))
    text_draw.text((513, 550), str(raw_data['stats']['geoculus_number']), new_color, ys_font(22))

    #雪山
    text_draw.text((745, 373.5),str(raw_data['world_explorations'][2]['exploration_percentage']/10) + '%',new_color, ys_font(22))
    text_draw.text((745, 407.1),'lv.' + str(raw_data['world_explorations'][2]['level']),new_color, ys_font(22))

    #稻妻
    text_draw.text((490, 608),str(raw_data['world_explorations'][1]['exploration_percentage']/10) + '%',new_color, ys_font(22))
    text_draw.text((490, 635),'lv.' + str(raw_data['world_explorations'][1]['level']),new_color, ys_font(22))
    text_draw.text((490, 662),'lv.' + str(raw_data['world_explorations'][1]['offerings'][0]['level']),new_color, ys_font(22))
    text_draw.text((513, 689), str(raw_data['stats']['electroculus_number']), new_color, ys_font(22))

    #渊下宫
    text_draw.text((745, 480),str(raw_data['world_explorations'][0]['exploration_percentage']/10) + '%',new_color, ys_font(22))

    #家园
    if len(raw_data['homes']):
        text_draw.text((693, 582.4),'lv.' + str(raw_data['homes'][0]['level']),new_color, ys_font(22))
        text_draw.text((693, 620.4),str(raw_data['homes'][0]['visit_num']),new_color, ys_font(22))
        text_draw.text((693, 658.4),str(raw_data['homes'][0]['item_num']),new_color, ys_font(22))
        text_draw.text((693, 696.4),str(raw_data['homes'][0]['comfort_num']),new_color, ys_font(22))
    else:
        text_draw.text((693, 582.4),"未开",new_color, ys_font(22))
        text_draw.text((693, 620.4),"未开",new_color, ys_font(22))
        text_draw.text((693, 658.4),"未开",new_color, ys_font(22))
        text_draw.text((693, 696.4),"未开",new_color, ys_font(22))
    
    #确定texture2D路径
    charpic_mask_path = os.path.join(TEXT_PATH,"charpic_mask.png")
    weaponpic_mask_path = os.path.join(TEXT_PATH,"weaponpic_mask.png")

    def getText(star,step):
        return os.path.join(TEXT_PATH,"{}s_{}.png".format(str(star),str(step)))

    charpic_mask = Image.open(charpic_mask_path)
    weaponpic_mask = Image.open(weaponpic_mask_path)
    s5s1=Image.open(getText(5,1))
    s5s2=Image.open(getText(5,2))
    s5s3=Image.open(getText(5,3))
    s5s4=Image.open(getText(5,4))
    s4s1=Image.open(getText(4,1))
    s4s2=Image.open(getText(4,2))
    s4s3=Image.open(getText(4,3))
    s4s4=Image.open(getText(4,4))
    s3s3=Image.open(getText(3,3))
    s2s3=Image.open(getText(2,3))
    s1s3=Image.open(getText(1,3))

    char_bg_path = os.path.join(TEXT_PATH, "char_bg.png")
    char_fg_path = os.path.join(TEXT_PATH, "char_fg.png")

    char_bg = Image.open(char_bg_path)
    char_fg = Image.open(char_fg_path)

    char_color = (math.floor(bg_color[0] + 10 if bg_color[0] + r <= 255 else 255),
                 math.floor(bg_color[1] + 10 if bg_color[1] + r <= 255 else 255), 
                 math.floor(bg_color[2] + 10 if bg_color[2] + r <= 255 else 255))

    charset_mask = Image.new("RGBA",(900,130),char_color)

    num = 0
    char_datas.sort(key=lambda x: (-x['rarity'],-x['level'],-x['fetter']))

    if char_num > 8 :
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

            char_weapon_star = i['weapon']['rarity']
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
    else:
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
            char_img_icon = i["image"]

            char_weapon_star = i['weapon']['rarity']
            char_weapon_level = i['weapon']['level']
            char_weapon_jinglian = i['weapon']['affix_level']
            char_weapon_icon = i['weapon']['icon']

            if not os.path.exists(os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))):
                get_weapon_pic(char_weapon_icon)
            if not os.path.exists(os.path.join(CHAR_IMG_PATH, str(char_img_icon.split('/')[-1]))):
                get_charimg_pic(char_img_icon)
            if not os.path.exists(os.path.join(CHAR_PATH,str(i['id']) + ".png")):
                get_char_pic(i['id'],i['icon'])

            char = os.path.join(CHAR_PATH,str(char_id) + ".png")
            weapon = os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))
            char_stand_img = os.path.join(CHAR_IMG_PATH,str(char_img_icon.split('/')[-1]))
            char_stand_mask = Image.open(os.path.join(TEXT_PATH,"stand_mask.png"))

            char_stand = Image.open(char_stand_img)
            char_img = Image.open(char)
            char_img = char_img.resize((100,100),Image.ANTIALIAS)
            weapon_img = Image.open(weapon)
            weapon_img = weapon_img.resize((47,47),Image.ANTIALIAS)

            charpic = Image.new("RGBA", (900, 130))
            charpic_temp = Image.new("RGBA", (900, 130))

            charpic.paste(charset_mask,(0,0),char_bg)

            weapon_bg = Image.open(getText(char_weapon_star,3))
            charpic.paste(weapon_bg,(72,10),weapon_bg)
            charpic_temp.paste(char_img,(81,13),charpic_mask)
            charpic_temp.paste(char_stand,(395,-99),char_stand_mask)
            charpic_temp.paste(char_fg,(0,0),char_fg)
            charpic_temp.paste(weapon_img,(141,72),weaponpic_mask)
            #temp = Image.composite(weapon_img, basedb, weaponpic_mask)
            charpic.paste(charpic_temp,(0,0),charpic_temp)


            for _,k in enumerate(i["reliquaries"]):
                if not os.path.exists(os.path.join(REL_PATH, str(k["icon"].split('/')[-1]))):
                    get_rel_pic(k["icon"])
                rel = os.path.join(REL_PATH,str(k["icon"].split('/')[-1]))
                rel_img = Image.open(rel).resize((43,43),Image.ANTIALIAS)
                rel_bg = Image.open(getText(k["rarity"],3))

                if k["pos_name"] == "生之花":
                    charpic.paste(rel_bg,(287 + 55 * 0,-14),rel_bg)
                    charpic.paste(rel_img,(360 + 55 * 0,49),rel_img)
                elif k["pos_name"] == "死之羽":
                    charpic.paste(rel_bg,(287 + 55 * 1,-14),rel_bg)
                    charpic.paste(rel_img,(360 + 55 * 1,49),rel_img)
                elif k["pos_name"] == "时之沙":
                    charpic.paste(rel_bg,(287 + 55 * 2,-14),rel_bg)
                    charpic.paste(rel_img,(360 + 55 * 2,49),rel_img)
                elif k["pos_name"] == "空之杯":
                    charpic.paste(rel_bg,(287 + 55 * 3,-14),rel_bg)
                    charpic.paste(rel_img,(360 + 55 * 3,49),rel_img)
                elif k["pos_name"] == "理之冠":
                    charpic.paste(rel_bg,(287 + 55 * 4,-14),rel_bg)
                    charpic.paste(rel_img,(360 + 55 * 4,49),rel_img)

            char_draw = ImageDraw.Draw(charpic)

            char_draw.text((188,30),i["name"] + " " + f'Lv.{str(char_level)}',new_color,ys_font(22))
            #char_draw.text((272,45),f'Lv.{str(char_level)}',new_color,ys_font(18))

            #char_draw.text((104.5,91.5),f'{str(char_weapon_jinglian)}',new_color,ys_font(10))

            char_draw.text((222,87),f'{str(i["fetter"])}' if str(char_name) != "旅行者" else "10",new_color,ys_font(15),anchor = "mm")
            char_draw.text((255,87),f'{str(char_mingzuo)}',new_color,ys_font(15),anchor = "mm")
            char_draw.text((218,67),f'{str(char_weapon_level)}级{str(char_weapon_jinglian)}精',new_color,ys_font(15),anchor = "lm")
            char_crop = (0,800+110*num)
            num += 1
            bg_img.paste(charpic,char_crop,charpic)

    #转换之后发送
    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    img_msg=f"[CQ:image,file={imgmes}]"
    if char_num<=8:
        img_msg='*由于米游社接口限制，现仅能查询部分角色信息\n'+img_msg
    resultmes = Message(img_msg)
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

async def draw_event_pic():
    raw_data = await GetGenshinEvent("List")
    raw_time_data = await GetGenshinEvent("Calendar")

    data = raw_data["data"]["list"][1]["list"]

    event_data = {"gacha_event":[],"normal_event":[],"other_event":[]}
    for k in data:
        for i in raw_time_data["data"]["act_list"]:
            if i["name"] == k["title"]:
                k["act_begin_time"] = i["act_begin_time"]
                k["act_end_time"] = i["act_end_time"]
            elif "神铸赋形" in k["title"] and "神铸赋形" in i["name"]:
                k["act_begin_time"] = i["act_begin_time"]
                k["act_end_time"] = i["act_end_time"]
            elif "传说任务" in k["title"]:
                k["act_begin_time"] = k["start_time"]
                k["act_end_time"] = "永久开放"
            elif k["subtitle"] in i["name"]:
                k["act_begin_time"] = i["act_begin_time"]
                k["act_end_time"] = i["act_end_time"]
            else:
                k["act_begin_time"] = "{}-{}-{} {}".format(k["start_time"].split()[0].split("-")[0], 
                                                           k["start_time"].split()[0].split("-")[1],
                                                           str(int(k["start_time"].split()[0].split("-")[2])+2),
                                                           "10:00:00(?)")
                k["act_end_time"] = k["end_time"]
                
        if "冒险助力礼包" in k["title"] or "纪行" in k["title"]:
            continue
        #if "角色试用" in k["title"] or "传说任务" in k["title"]:
        #    event_data['other_event'].append(k)
        elif k["tag_label"] == "扭蛋":
            event_data['gacha_event'].append(k)
        elif k["tag_label"] == "活动":
            event_data['normal_event'].append(k)

    #base_h = 900 + ((1 + (len(event_data['normal_event'])+len(event_data['other_event'])))//2)*390 + ((1 + len(event_data['gacha_event']))//2)*533
    base_h = 600 + len(event_data['normal_event'])*(390+90) + len(event_data['gacha_event'])*(533+90)
    base_img = Image.new(mode="RGB",size=(1080,base_h),color=(237,217,195))

    event1_path = os.path.join(TEXT_PATH,"event_1.png")
    event2_path = os.path.join(TEXT_PATH,"event_2.png")
    #event3_path = os.path.join(TEXT_PATH,"event_3.png")
    event1 = Image.open(event1_path)
    event2 = Image.open(event2_path)
    #event3 = Image.open(event3_path)

    base_img.paste(event1,(0,0),event1)
    #base_img.paste(event2,(0,300+((1+len(event_data['normal_event']))//2)*390),event2)
    base_img.paste(event2,(0,len(event_data['normal_event'])*(390+90) + 300),event2)
    #base_img.paste(event3,(0,600+((1+len(event_data['normal_event']))//2)*390 + ((1 + len(event_data['gacha_event']))//2)*533),event3)

    time_img1 = Image.new(mode="RGB",size=(1080,len(event_data['normal_event'])*(390+90)),color=(237,130,116))
    time_img2 = Image.new(mode="RGB",size=(1080,len(event_data['gacha_event'])*(533+90)),color=(237,130,116))
    base_img.paste(time_img1,(0,300))
    base_img.paste(time_img2,(0,600+len(event_data['normal_event'])*(390+90)))
    base_draw = ImageDraw.Draw(base_img)
    for index,value in enumerate(event_data['normal_event']):
        img = Image.open(BytesIO(requests.get(value["banner"]).content))
        base_draw.text((540, 300 + 45 + 390 + (390+90)*index+1), value["act_begin_time"] + " —— " + value["act_end_time"], (255,255,255), ys_font(42), anchor="mm")
        #base_img.paste(img,((index%2)*1080,300 + 390*(index//2)))
        base_img.paste(img,(0,300 + (390+90)*index))

    for index,value in enumerate(event_data['gacha_event']):
        img = Image.open(BytesIO(requests.get(value["banner"]).content))
        base_draw.text((540,600 + 45 + (390+90)*len(event_data['normal_event']) + 533 + index * (533 + 90)), value["act_begin_time"] + " —— " + value["act_end_time"], (255,255,255), ys_font(42), anchor="mm")
        #base_img.paste(img,((index%2)*1080,600 + ((1 + len(event_data['normal_event']))//2)*390 + 533*(index//2)))
        base_img.paste(img,(0,600 + (390+90) * len(event_data['normal_event']) + index * (533 + 90)))
    #for index,value in enumerate(event_data['other_event']):
    #    img = Image.open(BytesIO(requests.get(value["banner"]).content))
    #    base_img.paste(img,((index%2)*1080,900 + ((1 + len(event_data['normal_event']))//2)*390 + ((1 + len(event_data['gacha_event']))//2)*533 + 390*(index//2)))

    base_img = base_img.convert('RGB')
    base_img.save(os.path.join(FILE2_PATH,'event.jpg'), format='JPEG', subsampling=0, quality=90)
    return
