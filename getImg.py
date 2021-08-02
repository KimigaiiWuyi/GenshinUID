import time
from base64 import b64encode
from io import BytesIO

import urllib
import math

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .getData import GetInfo,GetCharacter

import os

FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH,'mys')
CHAR_PATH = os.path.join(FILE2_PATH,'chars')
TEXT_PATH = os.path.join(FILE2_PATH,'texture2d')

def ys_font(size):
    return ImageFont.truetype(os.path.join(FILE2_PATH,"yuanshen.ttf"), size=size)

async def draw_pic(uid,nickname,image = None):

    is_edit = False
    if image != None:
        image_file= image.group(1)
        image_data = image.group(2)
        urllib.request.urlretrieve(f'{image_data}', os.path.join(TEXT_PATH,nickname + '.png'))
        is_edit = True

    raw_data = await GetInfo(uid)

    if (raw_data["retcode"] != 0):
        if (raw_data["retcode"] == 10001):
            return ("Cookie错误/过期，请重置Cookie")
        return (
                "Api报错，返回内容为：\r\n"
                + str(raw_data) + "\r\n出现这种情况可能的UID输入错误 or 不存在"
        )
    else:
        pass

    bg_path = os.path.join(TEXT_PATH,"bg.png")
    bg2_path = os.path.join(TEXT_PATH,"bg_img.png")
    fg_path = os.path.join(TEXT_PATH,"fg_img.png")
    mask_path = os.path.join(TEXT_PATH,"mask_img.png")

    if is_edit == True:
        bg_path_edit = os.path.join(TEXT_PATH,f"{nickname}.png")
        edit_bg = Image.open(bg_path_edit)
        w, h = edit_bg.size
        scale_f = w / h
        scale = '%.4f' % scale_f
        new_w = math.ceil(1200*float(scale))
        new_h = math.ceil(800/float(scale))
        if w > h:
            bg_img2 = edit_bg.resize((new_w, 1200),Image.ANTIALIAS)
        else:
            bg_img2 = edit_bg.resize((800, new_h),Image.ANTIALIAS)
        bg_img = bg_img2.crop((0, 0, 800, 1200))
    else:
        bg_img = Image.open(bg2_path)

    raw_data = raw_data['data']

    fg_img = Image.open(fg_path)
    mask_img = Image.open(mask_path)

    #img = Image.open(bg_path)
    area = (37, 268, 764, 1154)
    img_bb = bg_img.crop(area)
    img_blur = img_bb.filter(ImageFilter.GaussianBlur(5))
    
    bg_img.paste(img_blur, (37,268),mask_img)

    bg_img.paste(fg_img,(0,0),fg_img)
    text_draw = ImageDraw.Draw(bg_img)

    text_draw.text((192.6,128.3), f"{nickname}", (217,217,217), ys_font(32))
    text_draw.text((210.6, 165.3), 'UID ' + f"{uid}", (217,217,217), ys_font(14))

    char_data = raw_data["avatars"]

    index_char = ["神里绫华","琴","迪卢克","温迪","魈","可莉","钟离","达达利亚","七七","甘雨","阿贝多","莫娜","刻晴","胡桃","枫原万叶","优菈","丽莎","芭芭拉","凯亚","雷泽","安柏","香菱","北斗","行秋","凝光","菲谢尔","班尼特","诺艾尔","重云","迪奥娜","砂糖","辛焱","罗莎莉亚","烟绯","旅行者"]

    five_star_char = ["神里绫华","琴","迪卢克","温迪","魈","可莉","钟离","达达利亚","七七","甘雨","阿贝多","莫娜","刻晴","胡桃","枫原万叶","优菈"]
    four_star_char = ["丽莎","芭芭拉","凯亚","雷泽","安柏","香菱","北斗","行秋","凝光","菲谢尔","班尼特","诺艾尔","重云","迪奥娜","砂糖","辛焱","罗莎莉亚","烟绯","旅行者"]
    
    for k in raw_data['avatars']:
        if k['name'] in five_star_char:
            k['star'] = 5
        if k['name'] in four_star_char:
            k['star'] = 4
        if k['name'] == '旅行者':
            k['star'] = 3
    
    #char_data.sort(key=lambda x: index_char.index(x['name']))

    char_data.sort(key=lambda x: (-x['star'],-x['level'],-x['fetter']))

    text_draw.text((590, 94.8),str(raw_data['stats']['active_day_number']), (21, 21, 21), ys_font(26))
    text_draw.text((590, 139.3),str(raw_data['stats']['achievement_number']), (21, 21, 21), ys_font(26))
    text_draw.text((590, 183.9),raw_data['stats']['spiral_abyss'], (21, 21, 21), ys_font(26))


    text_draw.text((635.4, 462.8), str(raw_data['stats']['anemoculus_number']), 'white', ys_font(26))
    text_draw.text((635.4, 493.6), str(raw_data['stats']['geoculus_number']), 'white', ys_font(26))
    text_draw.text((635.4, 524.8), str(raw_data['stats']['electroculus_number']), 'white', ys_font(26))

    text_draw.text((224.6, 379.1),str(raw_data['stats']['common_chest_number']),'white', ys_font(28))
    text_draw.text((436.5, 379.1),str(raw_data['stats']['exquisite_chest_number']),'white', ys_font(28))
    text_draw.text((224.6, 416),str(raw_data['stats']['precious_chest_number']), 'white', ys_font(28))
    text_draw.text((436.5, 416),str(raw_data['stats']['luxurious_chest_number']), 'white', ys_font(28))

    text_draw.text((646.3, 379.1),str(raw_data['stats']['avatar_number']),'white', ys_font(26))
    text_draw.text((646.3, 416),str(raw_data['stats']['way_point_number']),'white', ys_font(26))


    text_draw.text((228.9, 502),str(raw_data['world_explorations'][3]['exploration_percentage']/10) + '%','white', ys_font(20))
    text_draw.text((228.9, 538),'lv.' + str(raw_data['world_explorations'][3]['level']),'white', ys_font(20))

    text_draw.text((451.1, 502),str(raw_data['world_explorations'][2]['exploration_percentage']/10) + '%','white', ys_font(20))
    text_draw.text((451.1, 538),'lv.' + str(raw_data['world_explorations'][2]['level']),'white', ys_font(20))

    text_draw.text((228.9, 606.4),str(raw_data['world_explorations'][1]['exploration_percentage']/10) + '%','white', ys_font(20))
    text_draw.text((228.9, 641),'lv.' + str(raw_data['world_explorations'][1]['level']),'white', ys_font(20))

    text_draw.text((451.1, 597),str(raw_data['world_explorations'][0]['exploration_percentage']/10) + '%','white', ys_font(20))
    text_draw.text((451.1, 624),'lv.' + str(raw_data['world_explorations'][0]['level']),'white', ys_font(20))
    text_draw.text((451.1, 652),'lv.' + str(raw_data['world_explorations'][0]['offerings'][0]['level']),'white', ys_font(20))

    if len(raw_data['homes']):
        text_draw.text((594.5, 565),'lv.' + str(raw_data['homes'][0]['level']),'white', ys_font(26))
        text_draw.text((594.5, 598),str(raw_data['homes'][0]['visit_num']),'white', ys_font(26))
        text_draw.text((594.5, 630),str(raw_data['homes'][0]['item_num']),'white', ys_font(26))
        text_draw.text((594.5, 662),str(raw_data['homes'][0]['comfort_num']),'white', ys_font(26))
    else:
        text_draw.text((594.5, 616.6),'未开',(0, 0, 0), ys_font(26))

    num = 0

    for i in raw_data['avatars']:
        if num < 15:
            char = os.path.join(CHAR_PATH,str(char_data[num]['id']) + ".png")
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            char_draw.text((38.6,108),f'Lv.{str(char_data[num]["level"])}',(21,21,21),ys_font(18))
            char_draw.text((97,19),f'{str(char_data[num]["actived_constellation_num"])}','white',ys_font(18))
            if str(char_data[num]["fetter"]) == "10":
                char_draw.text((97,40),"F",(21,21,21),ys_font(17))
            else:
                char_draw.text((97,40),f'{str(char_data[num]["fetter"])}',(21,21,21),ys_font(18))
        
            if num < 5:
                char_crop = (74+133*num,750)
                bg_img.paste(char_img,char_crop,char_img)
            elif num >= 5 and num < 10:
                char_crop = (74+133*(num-5),875)
                bg_img.paste(char_img,(char_crop),char_img)
            elif num >= 10 and num < 15:
                char_crop = (74+133*(num-10),1000)
                bg_img.paste(char_img,(char_crop),char_img)
            else:
                break
            num = num+1

    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='png')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = f"[CQ:image,file={imgmes}]"
    #return 'base64://' + b64encode(result_buffer.getvalue()).decode()
    return resultmes


if __name__ == '__main__':
    pass
