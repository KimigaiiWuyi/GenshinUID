import os
from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from getData import (GetGenshinEvent)

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
CHAR_PATH = os.path.join(FILE2_PATH,'chars')
CHAR_DONE_PATH = os.path.join(FILE2_PATH,'char_done')
CHAR_IMG_PATH = os.path.join(FILE2_PATH,'char_img')
REL_PATH = os.path.join(FILE2_PATH,'reliquaries')
INDEX_PATH = os.path.join(FILE2_PATH,'index')
CHAR_WEAPON_PATH = os.path.join(FILE2_PATH,'char_weapon')
TEXT_PATH = os.path.join(FILE2_PATH,'texture2d')
WEAPON_PATH = os.path.join(FILE2_PATH,'weapon')
BG_PATH = os.path.join(FILE2_PATH,'bg')

def draw_event_pic():
    raw_data = GetGenshinEvent("List")
    raw_time_data = GetGenshinEvent("Calendar")

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