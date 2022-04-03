import asyncio
import math
import threading
from base64 import b64encode
from io import BytesIO
from re import Match, findall
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from bs4 import BeautifulSoup
from httpx import get
from wordcloud import WordCloud

from .get_data import *

STATUS = []
FILE_PATH = os.path.dirname(__file__)
FILE2_PATH = os.path.join(FILE_PATH, 'mihoyo_libs/mihoyo_bbs')
CHAR_PATH = os.path.join(FILE2_PATH, 'chars')
CHAR_DONE_PATH = os.path.join(FILE2_PATH, 'char_done')
CHAR_IMG_PATH = os.path.join(FILE2_PATH, 'char_img')
CHAR_NAMECARD_PATH = os.path.join(FILE2_PATH, 'char_namecard')
REL_PATH = os.path.join(FILE2_PATH, 'reliquaries')
CHAR_WEAPON_PATH = os.path.join(FILE2_PATH, 'char_weapon')
TEXT_PATH = os.path.join(FILE2_PATH, 'texture2d')
WEAPON_PATH = os.path.join(FILE2_PATH, 'weapon')
BG_PATH = os.path.join(FILE2_PATH, 'bg')


class CustomizeImage:
    def __init__(self, image: Match, based_w: int, based_h: int) -> None:

        self.bg_img = self.get_image(image, based_w, based_h)
        self.bg_color = self.get_bg_color(self.bg_img)
        self.text_color = self.get_text_color(self.bg_color)
        self.highlight_color = self.get_highlight_color(self.bg_color)
        self.char_color = self.get_char_color(self.bg_color)
        self.bg_detail_color = self.get_bg_detail_color(self.bg_color)
        self.char_high_color = self.get_char_high_color(self.bg_color)

    @staticmethod
    def get_image(image: Match, based_w: int, based_h: int) -> Image:
        # 获取背景图片
        bg2_path = os.path.join(BG_PATH, random.choice([x for x in os.listdir(BG_PATH)
                                                        if os.path.isfile(os.path.join(BG_PATH, x))]))

        if image:
            image_data = image.group(2)
            edit_bg = Image.open(BytesIO(get(image_data).content))
        else:
            edit_bg = Image.open(bg2_path)

        # 确定图片的长宽
        based_scale = '%.3f' % (based_w / based_h)

        w, h = edit_bg.size
        scale_f = '%.3f' % (w / h)
        new_w = math.ceil(based_h * float(scale_f))
        new_h = math.ceil(based_w / float(scale_f))
        if scale_f > based_scale:
            bg_img2 = edit_bg.resize((new_w, based_h), Image.ANTIALIAS)
        else:
            bg_img2 = edit_bg.resize((based_w, new_h), Image.ANTIALIAS)
        bg_img = bg_img2.crop((0, 0, based_w, based_h))

        return bg_img

    @staticmethod
    def get_bg_color(edit_bg: Image) -> Tuple[int, int, int]:
        # 获取背景主色
        color = 8
        q = edit_bg.quantize(colors=color, method=2)
        bg_color = None
        based_light = 195
        temp = 9999
        for i in range(0, color):
            bg = tuple(q.getpalette()[i * 3:(i * 3) + 3])
            light_value = bg[0] * 0.3 + bg[1] * 0.6 + bg[2] * 0.1
            if abs(light_value - based_light) < temp:
                bg_color = bg
                temp = abs(light_value - based_light)
            # if max(*bg) < 240 and min(*bg) > 20:
            #    bg_color = bg
        return bg_color

    @staticmethod
    def get_text_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        # 通过背景主色（bg_color）确定文字主色
        r = 125
        if max(*bg_color) > 255 - r:
            r *= -1
        text_color = (math.floor(bg_color[0] + r if bg_color[0] + r <= 255 else 255),
                      math.floor(bg_color[1] + r if bg_color[1] + r <= 255 else 255),
                      math.floor(bg_color[2] + r if bg_color[2] + r <= 255 else 255))
        return text_color

    @staticmethod
    def get_char_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        char_color = (math.floor(bg_color[0] + 5 if bg_color[0] + r <= 255 else 255),
                      math.floor(bg_color[1] + 5 if bg_color[1] + r <= 255 else 255),
                      math.floor(bg_color[2] + 5 if bg_color[2] + r <= 255 else 255))
        return char_color

    @staticmethod
    def get_char_high_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        r = 140
        d = 20
        if max(*bg_color) > 255 - r:
            r *= -1
        char_color = (math.floor(bg_color[0] + d if bg_color[0] + r <= 255 else 255),
                      math.floor(bg_color[1] + d if bg_color[1] + r <= 255 else 255),
                      math.floor(bg_color[2] + d if bg_color[2] + r <= 255 else 255))
        return char_color

    @staticmethod
    def get_bg_detail_color(bg_color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        r = 140
        if max(*bg_color) > 255 - r:
            r *= -1
        bg_detail_color = (math.floor(bg_color[0] - 20 if bg_color[0] + r <= 255 else 255),
                           math.floor(bg_color[1] - 20 if bg_color[1] + r <= 255 else 255),
                           math.floor(bg_color[2] - 20 if bg_color[2] + r <= 255 else 255))
        return bg_detail_color

    @staticmethod
    def get_highlight_color(color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        red_color = color[0]
        green_color = color[1]
        blue_color = color[2]

        highlight_color = {'red'  : red_color - 127 if red_color > 127 else 127,
                           'green': green_color - 127 if green_color > 127 else 127,
                           'blue' : blue_color - 127 if blue_color > 127 else 127}

        max_color = max(highlight_color.values())

        name = ''
        for _highlight_color in highlight_color:
            if highlight_color[_highlight_color] == max_color:
                name = str(_highlight_color)

        if name == 'red':
            return red_color, highlight_color['green'], highlight_color['blue']
        elif name == 'green':
            return highlight_color['red'], green_color, highlight_color['blue']
        elif name == 'blue':
            return highlight_color['red'], highlight_color['green'], blue_color
        else:
            return 0, 0, 0  # Error


def genshin_font(size: int):
    return ImageFont.truetype(os.path.join(FILE2_PATH, 'yuanshen.ttf'), size=size)


def get_char_pic(_id: str, url: str):
    with open(os.path.join(CHAR_PATH, f'{_id}.png'), 'wb') as f:
        f.write(get(url).content)


def get_char_done_pic(_id: str, url: str, star: int):
    char_data = get(url).content
    if star == 4:
        star1_path = os.path.join(TEXT_PATH, '4star_1.png')
        star2_path = os.path.join(TEXT_PATH, '4star_2.png')
    else:
        star1_path = os.path.join(TEXT_PATH, '5star_1.png')
        star2_path = os.path.join(TEXT_PATH, '5star_2.png')
    star_1 = Image.open(star1_path)
    star_2 = Image.open(star2_path)
    char_img = Image.open(BytesIO(char_data)).resize((104, 104), Image.ANTIALIAS)
    star_1.paste(char_img, (12, 15), char_img)
    star_1.paste(star_2, (0, 0), star_2)
    star_1.save(os.path.join(CHAR_DONE_PATH, str(_id) + '.png'))


def get_weapon_pic(url: str):
    with open(os.path.join(WEAPON_PATH, url.split('/')[-1]), 'wb') as f:
        f.write(get(url).content)


def get_char_img_pic(url: str):
    with open(os.path.join(CHAR_IMG_PATH, url.split('/')[-1]), 'wb') as f:
        f.write(get(url).content)


def get_rel_pic(url: str):
    with open(os.path.join(REL_PATH, url.split('/')[-1]), 'wb') as f:
        f.write(get(url).content)


class GetCookies:
    def __init__(self) -> None:
        self.useable_cookies: Optional[str] = None
        self.uid: Optional[str] = None
        self.mode: Optional[int] = None
        self.raw_abyss_data: Optional[dict] = None
        self.raw_data: Optional[dict] = None
        self.nickname: Optional[int] = None
        self.schedule_type: Optional[str] = None

    async def get_useable_cookies(self, uid: str, mode: int = 2, schedule_type: str = '1'):
        self.uid = uid
        self.schedule_type = schedule_type
        while True:
            self.useable_cookies = cache_db(uid, mode - 1)
            if self.useable_cookies == '':
                return '绑定记录不存在。'
            elif self.useable_cookies == '没有可以使用的Cookies！':
                return '没有可以使用的Cookies！'
            if mode == 3:
                await self.get_mihoyo_bbs_data()
            else:
                await self.get_uid_data()

            msg = await self.check_cookies_useable()
            if isinstance(msg, str):
                return msg
            elif isinstance(msg, bool):
                if msg:
                    return True

    async def get_mihoyo_bbs_data(self):
        mys_data = await get_mihoyo_bbs_info(self.uid, self.useable_cookies)
        for i in mys_data['data']['list']:
            if i['game_id'] != 2:
                mys_data['data']['list'].remove(i)
        self.uid = mys_data['data']['list'][0]['game_role_id']
        self.nickname = mys_data['data']['list'][0]['nickname']
        self.raw_data = await get_info(self.uid, self.useable_cookies)
        self.raw_abyss_data = await get_spiral_abyss_info(self.uid, self.useable_cookies, self.schedule_type)

    async def get_uid_data(self):
        self.raw_abyss_data = await get_spiral_abyss_info(self.uid, self.useable_cookies, self.schedule_type)
        self.raw_data = await get_info(self.uid, self.useable_cookies)

    async def check_cookies_useable(self):
        if self.raw_data:
            if self.raw_data['retcode'] != 0:
                if self.raw_data['retcode'] == 10001:
                    error_db(self.useable_cookies, 'error')
                    return False
                elif self.raw_data['retcode'] == 10101:
                    error_db(self.useable_cookies, 'limit30')
                    return False
                elif self.raw_data['retcode'] == 10102:
                    return '当前查询id已经设置了隐私，无法查询！'
                else:
                    return (
                            'Api报错，返回内容为：\r\n'
                            + str(self.raw_data) + '\r\n出现这种情况可能的UID输入错误 or 不存在'
                    )
            else:
                return True
        else:
            return '没有可以使用的Cookies！'


async def draw_word_cloud(uid: str, image: Optional[Match] = None, mode: int = 2):
    def create_rounded_rectangle_mask(rectangle, _radius):
        solid_fill = (50, 50, 50, 255)
        img = Image.new('RGBA', rectangle.size, (0, 0, 0, 0))

        corner = Image.new('RGBA', (_radius, _radius), (0, 0, 0, 0))
        draw = ImageDraw.Draw(corner)
        draw.pieslice(((0, 0), (_radius * 2, _radius * 2)), 180, 270, fill=solid_fill)

        mx, my = rectangle.size

        img.paste(corner, (0, 0), corner)
        img.paste(corner.rotate(90), (0, my - _radius), corner.rotate(90))
        img.paste(corner.rotate(180), (mx - _radius, my - _radius), corner.rotate(180))
        img.paste(corner.rotate(270), (mx - _radius, 0), corner.rotate(270))

        draw = ImageDraw.Draw(img)
        draw.rectangle(((_radius, 0), (mx - _radius, my)), fill=solid_fill)
        draw.rectangle(((0, _radius), (mx, my - _radius)), fill=solid_fill)

        return img

    nickname = ''
    while True:
        use_cookies = cache_db(uid, mode - 1)
        if use_cookies == '':
            return '绑定记录不存在。'
        elif use_cookies == '没有可以使用的Cookies！':
            return '没有可以使用的Cookies！'

        if mode == 3:
            mys_data = await get_mihoyo_bbs_info(uid, use_cookies)
            for i in mys_data['data']['list']:
                if i['game_id'] != 2:
                    mys_data['data']['list'].remove(i)
            uid = mys_data['data']['list'][0]['game_role_id']
            nickname = mys_data['data']['list'][0]['nickname']
            # role_level = mys_data['data']['list'][0]['level']
            raw_data = await get_info(uid, use_cookies)
            raw_abyss_data = await get_spiral_abyss_info(uid, use_cookies)
        else:
            raw_abyss_data = await get_spiral_abyss_info(uid, use_cookies)
            raw_data = await get_info(uid, use_cookies)

        if raw_data['retcode'] != 0:
            if raw_data['retcode'] == 10001:
                # return ('Cookie错误/过期，请重置Cookie')
                error_db(use_cookies, 'error')
            elif raw_data['retcode'] == 10101:
                # return ('当前cookies已达到30人上限！')
                error_db(use_cookies, 'limit30')
            elif raw_data['retcode'] == 10102:
                return '当前查询id已经设置了隐私，无法查询！'
            else:
                return (
                        'Api报错，返回内容为：\r\n'
                        + str(raw_data) + '\r\n出现这种情况可能的UID输入错误 or 不存在'
                )
        else:
            break

    raw_abyss_data = raw_abyss_data['data']
    raw_data = raw_data['data']

    # char_data = raw_data['avatars']
    # char_num = len(raw_data['avatars'])

    char_datas = []

    def get_char_id(start, end):
        for char in range(start, end):
            char_rawdata = get_character(uid, [char], use_cookies)

            if char_rawdata['retcode'] != -1:
                char_datas.append(char_rawdata['data']['avatars'][0])

    thread_list = []
    st = 8
    for i in range(0, 8):
        thread = threading.Thread(target=get_char_id, args=(10000002 + i * st, 10000002 + (i + 1) * st))
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
    star5weapon_con = 0
    # star3weapon = 0
    for i in weapons_datas:
        if i['rarity'] == 5:
            star5weapon += 1
            star5weapon_con += i['affix_level']
        elif i['rarity'] == 4:
            star4weapon += 1
        elif i['rarity'] == 3:
            star4weapon += 1

    g3d1 = 0
    ly3c = 0
    star5num = 0
    star5num_con = 0

    for i in char_datas:
        if i['name'] in ['雷电将军', '温迪', '钟离', '枫原万叶']:
            g3d1 += 1
        if i['name'] in ['甘雨', '魈', '胡桃']:
            ly3c += 1
        if i['rarity'] == 5:
            star5num += 1
            if i['name'] != '旅行者':
                star5num_con += 1 + i['actived_constellation_num']

        if i['level'] >= 80:
            if i['name'] == '迪卢克':
                word_str['落魄了家人们'] = l3_size
            if i['name'] == '刻晴':
                word_str['斩尽牛杂'] = l3_size
            if i['name'] == '旅行者':
                word_str['旅行者真爱党'] = l3_size

        if i['actived_constellation_num'] == 6:
            if i['rarity'] == 5:
                if i['name'] == '旅行者':
                    word_str['满命{}'.format(i['name'])] = l1_size
                if i['name'] == '魈':
                    word_str['魈深氪的救赎'] = l5_size
                if i['name'] == '甘雨':
                    word_str['璃月自走归终机'] = l5_size
                if i['name'] == '胡桃':
                    word_str['一波送走全送走'] = l5_size
                else:
                    word_str['满命{}'.format(i['name'])] = l5_size
            else:
                word_str['满命{}'.format(i['name'])] = l2_size

    game_time = time.mktime(time.strptime('20200915', '%Y%m%d'))
    now_time = time.time()
    total_s = now_time - game_time
    total_d = ((total_s / 60) / 60) / 24

    if math.floor(total_d) - 5 <= raw_data['stats']['active_day_number']:
        word_str['开服玩家'] = l4_size

    if g3d1 >= 4:
        word_str['三神一帝'] = l3_size
    if ly3c >= 3:
        word_str['璃月3C'] = l3_size
    if star5num >= 16:
        word_str['五星众多'] = l3_size

    if len(weapons_datas) - star4weapon <= 3:
        word_str['武器基本四星'] = l3_size

    if raw_data['stats']['achievement_number'] // (star5weapon_con + star5num_con) >= 23:
        word_str['平民玩家'] = l2_size
    elif raw_data['stats']['achievement_number'] // (star5weapon_con + star5num_con) <= 15:
        word_str['氪金玩家'] = l3_size

    if raw_data['stats']['anemoculus_number'] + raw_data['stats']['geoculus_number'] + \
            raw_data['stats']['electroculus_number'] == 378:
        word_str['全神瞳'] = l2_size
    if raw_data['world_explorations'][3]['exploration_percentage'] + raw_data['world_explorations'][2][
        'exploration_percentage'] + raw_data['world_explorations'][1]['exploration_percentage'] + \
            raw_data['world_explorations'][0]['exploration_percentage'] >= 3950:
        word_str['全探索'] = l4_size
    if raw_data['stats']['achievement_number'] >= 510:
        word_str['全成就'] = l5_size
    elif raw_data['stats']['achievement_number'] >= 490:
        word_str['成就达人'] = l3_size
    if raw_data['stats']['spiral_abyss'] == '12-3':
        word_str['深境的探究者'] = l2_size
    if len(raw_data['avatars']) >= 42:
        word_str['全角色'] = l3_size

    if raw_data['stats']['active_day_number'] <= 40:
        word_str['刚入坑'] = l1_size
    elif raw_data['stats']['active_day_number'] <= 100:
        word_str['初心者'] = l2_size
    elif raw_data['stats']['active_day_number'] <= 300:
        word_str['老玩家'] = l2_size
    if raw_data['stats']['active_day_number'] >= 365 and raw_data['stats']['magic_chest_number'] + raw_data['stats'][
        'common_chest_number'] + raw_data['stats']['exquisite_chest_number'] + \
            raw_data['stats']['precious_chest_number'] + raw_data['stats']['luxurious_chest_number'] <= 2500:
        word_str['老咸鱼'] = l3_size
    if raw_data['stats']['magic_chest_number'] >= 46:
        word_str['迷失在黑夜里'] = l2_size
    if raw_data['homes'][0]['comfort_num'] >= 25000:
        word_str['团雀附体'] = l2_size

    if raw_abyss_data['reveal_rank']:
        if raw_abyss_data['total_battle_times'] <= 12 and raw_abyss_data['max_floor'] == '12-3':
            word_str['PVP资格证'] = l4_size
        if raw_abyss_data['damage_rank'][0]['value'] >= 150000:
            word_str['这一击，贯穿星辰'] = l4_size
    else:
        pass

    bg_list = random.choice([x for x in os.listdir(BG_PATH)
                             if os.path.isfile(os.path.join(BG_PATH, x))])

    bg2_path = os.path.join(BG_PATH, bg_list)

    based_w = 900
    based_h = 1000
    based_scale = '%.3f' % (based_w / based_h)

    is_edit = False
    if image:
        image_data = image.group(2)
        with open(os.path.join(TEXT_PATH, nickname + '.png'), 'wb') as f:
            f.write(get(image_data).content)
        is_edit = True

    if is_edit:
        bg_path_edit = os.path.join(TEXT_PATH, f'{nickname}.png')
    else:
        bg_path_edit = bg2_path

    edit_bg = Image.open(bg_path_edit)
    w, h = edit_bg.size
    scale_f = '%.3f' % (w / h)
    new_w = math.ceil(based_h * float(scale_f))
    new_h = math.ceil(based_w / float(scale_f))
    if scale_f > based_scale:
        bg_img2 = edit_bg.resize((new_w, based_h), Image.ANTIALIAS)
    else:
        bg_img2 = edit_bg.resize((based_w, new_h), Image.ANTIALIAS)

    bg_img = bg_img2.crop((0, 0, based_w, based_h))

    x, y = 50, 153
    radius = 50
    cropped_img = bg_img.crop((x, y, x + 800, y + 800))
    blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(5), ).convert('RGBA')
    bg_img.paste(blurred_img, (x, y), create_rounded_rectangle_mask(cropped_img, radius))

    panle = Image.open(os.path.join(TEXT_PATH, 'wordcloud_0.png'))

    mask = np.array([Image.open(os.path.join(TEXT_PATH, 'wordcloudmask.png'))])

    wc = WordCloud(
        font_path=os.path.join(FILE2_PATH, 'yuanshen.ttf'),
        mask=mask,
        background_color='rgba(255, 255, 255, 0)',
        mode='RGBA',
        max_words=200,
        max_font_size=80
        # color_func=multi_color_func
        # color_func=similar_color_func
    ).generate_from_frequencies(word_str, max_font_size=100)

    image_produce = wc.to_image()

    bg_img.paste(panle, (0, 0), panle)
    bg_img.paste(image_produce, (0, 0), image_produce)
    bg_img = bg_img.convert('RGB')

    text_draw = ImageDraw.Draw(bg_img)
    text_draw.text((450, 105), 'UID ' + f'{uid}', (40, 136, 168), genshin_font(26), anchor='mm')

    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = imgmes
    return resultmes


async def draw_abyss0_pic(uid, nickname, image=None, mode=2, date='1'):
    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid, mode, date)
    if not retcode:
        return retcode
    raw_char_data = data_def.raw_data
    raw_data = data_def.raw_abyss_data
    uid = data_def.uid
    nickname = data_def.nickname if data_def.nickname else nickname

    # 获取数据
    raw_data = raw_data['data']
    raw_char_data = raw_char_data['data']['avatars']

    # 获取查询者数据
    floors_data = raw_data['floors'][-1]
    levels_num = len(floors_data['levels'])

    # 获取背景图片各项参数
    based_w = 900
    based_h = 660 + levels_num * 315
    image_def = CustomizeImage(image, based_w, based_h)
    bg_img = image_def.bg_img
    bg_color = image_def.bg_color
    text_color = image_def.text_color
    # highlight_color = image_def.highlight_color

    # 确定贴图路径
    abyss0_path = os.path.join(TEXT_PATH, 'abyss_0.png')
    abyss3_path = os.path.join(TEXT_PATH, 'abyss_3.png')
    abyss_star0_path = os.path.join(TEXT_PATH, 'abyss_star0.png')
    abyss_star1_path = os.path.join(TEXT_PATH, 'abyss_star1.png')
    avatar_bg_path = os.path.join(TEXT_PATH, 'avatar_bg.png')
    avatar_fg_path = os.path.join(TEXT_PATH, 'avatar_fg.png')

    all_mask_path = os.path.join(TEXT_PATH, 'All_Mask.png')

    # 转换遮罩的颜色、大小匹配，并paste上去
    all_mask = Image.open(all_mask_path).resize(bg_img.size, Image.ANTIALIAS)
    all_mask_img = Image.new('RGBA', (based_w, based_h), bg_color)
    bg_img.paste(all_mask_img, (0, 0), all_mask)

    # 开启图片
    avatar_bg = Image.open(avatar_bg_path)
    avatar_fg = Image.open(avatar_fg_path)

    # 确定主体框架
    avatar_bg_color = Image.new('RGBA', (316, 100), bg_color)
    bg_img.paste(avatar_bg_color, (113, 98), avatar_bg)
    bg_img.paste(avatar_fg, (114, 95), avatar_fg)

    """
    x1, y1 = 65, 276
    radius = 15
    cropped_img1 = bg_img.crop((x1, y1, 836, 607))
    blurred_img1 = cropped_img1.filter(ImageFilter.GaussianBlur(5),).convert('RGBA')
    bg_img.paste(blurred_img1, (x1, y1), create_rounded_rectangle_mask(cropped_img1,radius))
    for i in range(0,len(floors_data['levels'])):
        x2, y2 = 65, 630 + 315*i 
        radius = 15
        cropped_img2 = bg_img.crop((x2, y2, 836, 925+315*i))
        blurred_img2 = cropped_img2.filter(ImageFilter.GaussianBlur(5),).convert('RGBA')
        bg_img.paste(blurred_img2, (x2, y2), create_rounded_rectangle_mask(cropped_img2,radius))
    """

    abyss0_bg_color = Image.new('RGBA', (900, 620), text_color)
    abyss0 = Image.new('RGBA', (900, 620), (0, 0, 0, 0))

    abyss0_pic = Image.open(abyss0_path)
    abyss0.paste(abyss0_bg_color, (0, 0), abyss0_pic)
    abyss3 = Image.open(abyss3_path)
    abyss_star0 = Image.open(abyss_star0_path)
    abyss_star1 = Image.open(abyss_star1_path)

    for i in range(0, 4):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(raw_data['reveal_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['reveal_rank'][i]['avatar_id'], raw_data['reveal_rank'][i]['avatar_icon'],
                              raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['reveal_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['reveal_rank'][i]['avatar_id']:
                char_draw.text((63.5, 117), f'{str(raw_data["reveal_rank"][i]["value"])}次', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (82 + 130 * i, 300)
        abyss0.paste(char_img, char_crop, char_img)

    for i in range(0, 1):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(raw_data['damage_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['damage_rank'][i]['avatar_id'], raw_data['damage_rank'][i]['avatar_icon'],
                              raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['damage_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['damage_rank'][i]['avatar_id']:
                char_draw.text((63.5, 117), f'{str(raw_data["damage_rank"][i]["value"])}', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (685, 470)
        abyss0.paste(char_img, char_crop, char_img)

    for i in range(0, 1):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(raw_data['defeat_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['defeat_rank'][i]['avatar_id'], raw_data['defeat_rank'][i]['avatar_icon'],
                              raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['defeat_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['defeat_rank'][i]['avatar_id']:
                char_draw.text((63.5, 117), f'{str(raw_data["defeat_rank"][i]["value"])}', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (82 + 123 * i, 470)
        abyss0.paste(char_img, char_crop, char_img)

    for i in range(0, 1):
        if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(raw_data['take_damage_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['take_damage_rank'][i]['avatar_id'],
                              raw_data['take_damage_rank'][i]['avatar_icon'], raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['take_damage_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['take_damage_rank'][i]['avatar_id']:
                char_draw.text((63.5, 117), f'{str(raw_data["take_damage_rank"][i]["value"])}', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (232 + 123 * i, 470)
        abyss0.paste(char_img, char_crop, char_img)

    for i in range(0, 1):
        if not os.path.exists(
                os.path.join(CHAR_DONE_PATH, str(raw_data['normal_skill_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['normal_skill_rank'][i]['avatar_id'],
                              raw_data['normal_skill_rank'][i]['avatar_icon'], raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['normal_skill_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['normal_skill_rank'][i]['avatar_id']:
                char_draw.text((63.5, 117), f'{str(raw_data["normal_skill_rank"][i]["value"])}', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (382 + 123 * i, 470)
        abyss0.paste(char_img, char_crop, char_img)

    for i in range(0, 1):
        if not os.path.exists(
                os.path.join(CHAR_DONE_PATH, str(raw_data['energy_skill_rank'][i]['avatar_id']) + '.png')):
            get_char_done_pic(raw_data['energy_skill_rank'][i]['avatar_id'],
                              raw_data['energy_skill_rank'][i]['avatar_icon'], raw_data['reveal_rank'][i]['rarity'])
        char = os.path.join(CHAR_DONE_PATH, str(raw_data['energy_skill_rank'][i]['avatar_id']) + '.png')
        char_img = Image.open(char)
        char_draw = ImageDraw.Draw(char_img)
        for k in raw_char_data:
            if k['id'] == raw_data['energy_skill_rank'][i]['avatar_id']:
                char_draw.text((63.5, 118), f'{str(raw_data["energy_skill_rank"][i]["value"])}', (21, 21, 21),
                               genshin_font(18), anchor='mm')
                char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                    char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                else:
                    char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
        char_crop = (532 + 123 * i, 470)
        abyss0.paste(char_img, char_crop, char_img)

    bg_img.paste(abyss0, (0, 0), abyss0)

    for j in range(0, len(floors_data['levels'])):
        abyss2 = Image.new('RGBA', (900, 340), (0, 0, 0, 0))
        # abyss2 = Image.open(abyss2_path)
        num_1 = 0
        for i in floors_data['levels'][j]['battles'][0]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')):
                get_char_done_pic(i['id'], i['icon'], i['rarity'])
            char = os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40, 108), f'Lv.{str(k["level"])}', (21, 21, 21), genshin_font(18))
                    char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                    if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                        char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                    else:
                        char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
            char_crop = (70 + 125 * (num_1 % 4), 46)
            abyss2.paste(char_img, char_crop, char_img)
            num_1 = num_1 + 1
        num_2 = 0
        for i in floors_data['levels'][j]['battles'][1]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')):
                get_char_done_pic(i['id'], i['icon'], i['rarity'])
            char = os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40, 108), f'Lv.{str(k["level"])}', (21, 21, 21), genshin_font(18))
                    char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                    if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                        char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                    else:
                        char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
            char_crop = (70 + 125 * (num_2 % 4), 180)
            abyss2.paste(char_img, char_crop, char_img)
            num_2 = num_2 + 1
        star_num = floors_data['levels'][j]['star']
        if star_num == 1:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star0, (685, 155), abyss_star0)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        elif star_num == 0:
            abyss2.paste(abyss_star0, (640, 155), abyss_star0)
            abyss2.paste(abyss_star0, (685, 155), abyss_star0)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        elif star_num == 2:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star1, (685, 155), abyss_star1)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        else:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star1, (685, 155), abyss_star1)
            abyss2.paste(abyss_star1, (730, 155), abyss_star1)
        abyss2_text_draw = ImageDraw.Draw(abyss2)
        abyss2_text_draw.text((87, 30), f'第{j + 1}间', text_color, genshin_font(21))
        timestamp1 = int(floors_data['levels'][j]['battles'][0]['timestamp'])
        timestamp2 = int(floors_data['levels'][j]['battles'][1]['timestamp'])
        time_array1 = time.localtime(timestamp1)
        time_array2 = time.localtime(timestamp2)
        other_style_time1 = time.strftime('%Y--%m--%d %H:%M:%S', time_array1)
        other_style_time2 = time.strftime('%Y--%m--%d %H:%M:%S', time_array2)
        abyss2_text_draw.text((167, 33), f'{other_style_time1}/{other_style_time2}', text_color, genshin_font(19))
        bg_img.paste(abyss2, (0, 605 + j * 315), abyss2)

    bg_img.paste(abyss3, (0, len(floors_data['levels']) * 315 + 610), abyss3)

    text_draw = ImageDraw.Draw(bg_img)
    text_draw.text((220, 123), f'{nickname}', text_color, genshin_font(32))
    text_draw.text((235, 163), 'UID ' + f'{uid}', text_color, genshin_font(14))

    text_draw.text((690, 82), raw_data['max_floor'], text_color, genshin_font(26))
    text_draw.text((690, 127), str(raw_data['total_battle_times']), text_color, genshin_font(26))
    text_draw.text((690, 172), str(raw_data['total_star']), text_color, genshin_font(26))

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    # bg_img.save(result_buffer, format='PNG')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    # resultmes = f'[CQ:image,file={imgmes}]'
    resultmes = imgmes
    return resultmes


async def draw_abyss_pic(uid: str, nickname: str, floor_num: int, image: Optional[Match] = None, mode: int = 2,
                         date: str = '1'):
    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid, mode, date)
    if not retcode:
        return retcode
    raw_char_data = data_def.raw_data
    raw_data = data_def.raw_abyss_data
    uid = data_def.uid
    nickname = data_def.nickname if data_def.nickname else nickname

    # 获取数据
    raw_data = raw_data['data']
    raw_char_data = raw_char_data['data']['avatars']
    floors_data = raw_data['floors']
    based_data = {}
    for i in floors_data:
        if str(i['index']) == floor_num:
            based_data = i
    levels_num = len(based_data['levels'])

    # 获取背景图片各项参数
    based_w = 900
    based_h = 440 + levels_num * 340
    image_def = CustomizeImage(image, based_w, based_h)
    bg_img = image_def.bg_img
    bg_color = image_def.bg_color
    text_color = image_def.text_color
    # highlight_color = image_def.highlight_color

    # 打开图片
    abyss1_path = os.path.join(TEXT_PATH, 'abyss_1.png')
    abyss3_path = os.path.join(TEXT_PATH, 'abyss_3.png')
    abyss_star0_path = os.path.join(TEXT_PATH, 'abyss_star0.png')
    abyss_star1_path = os.path.join(TEXT_PATH, 'abyss_star1.png')
    abyss1 = Image.open(abyss1_path)
    abyss3 = Image.open(abyss3_path)
    abyss_star0 = Image.open(abyss_star0_path)
    abyss_star1 = Image.open(abyss_star1_path)
    avatar_bg_path = os.path.join(TEXT_PATH, 'avatar_bg.png')
    avatar_fg_path = os.path.join(TEXT_PATH, 'avatar_fg.png')

    all_mask_path = os.path.join(TEXT_PATH, 'All_Mask.png')

    # 转换遮罩的颜色、大小匹配，并paste上去
    all_mask = Image.open(all_mask_path).resize(bg_img.size, Image.ANTIALIAS)
    all_mask_img = Image.new('RGBA', (based_w, based_h), bg_color)
    bg_img.paste(all_mask_img, (0, 0), all_mask)

    # 开启图片
    avatar_bg = Image.open(avatar_bg_path)
    avatar_fg = Image.open(avatar_fg_path)

    # 确定主体框架
    avatar_bg_color = Image.new('RGBA', (316, 100), bg_color)
    bg_img.paste(avatar_bg_color, (113, 145), avatar_bg)
    bg_img.paste(avatar_fg, (114, 142), avatar_fg)

    """
    for i in range(0,len(based_data['levels'])):
        x, y = 65, 220 + 340*i 
        radius = 10
        cropped_img = bg_img.crop((x, y, 836, 517+340*i))
        blurred_img = cropped_img.filter(ImageFilter.GaussianBlur(5),).convert('RGBA')
        bg_img.paste(blurred_img, (x, y), create_rounded_rectangle_mask(cropped_img,radius))
    """

    abyss1_bg_color = Image.new('RGBA', (900, 400), bg_color)
    bg_img.paste(abyss1_bg_color, (0, 0), abyss1)

    for j in range(0, len(based_data['levels'])):
        abyss2 = Image.new('RGBA', (900, 340), (0, 0, 0, 0))
        num_1 = 0
        # avatars = based_data['levels'][j]['battles'][0]['avatars'] + based_data['levels'][j]['battles'][1]['avatars']
        for i in based_data['levels'][j]['battles'][0]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')):
                get_char_done_pic(i['id'], i['icon'], i['rarity'])
            char = os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40, 108), f'Lv.{str(k["level"])}', (21, 21, 21), genshin_font(18))
                    char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                    if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                        char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                    else:
                        char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
            char_crop = (70 + 125 * (num_1 % 4), 46)
            abyss2.paste(char_img, char_crop, char_img)
            num_1 = num_1 + 1
        num_2 = 0
        for i in based_data['levels'][j]['battles'][1]['avatars']:
            if not os.path.exists(os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')):
                get_char_done_pic(i['id'], i['icon'], i['rarity'])
            char = os.path.join(CHAR_DONE_PATH, str(i['id']) + '.png')
            char_img = Image.open(char)
            char_draw = ImageDraw.Draw(char_img)
            for k in raw_char_data:
                if k['id'] == i['id']:
                    char_draw.text((40, 108), f'Lv.{str(k["level"])}', (21, 21, 21), genshin_font(18))
                    char_draw.text((95.3, 19), f'{str(k["actived_constellation_num"])}', 'white', genshin_font(18))
                    if str(k['fetter']) == '10' or str(k['name']) == '旅行者':
                        char_draw.text((93, 41.5), '♥', (21, 21, 21), genshin_font(15))
                    else:
                        char_draw.text((95.3, 40.5), f'{str(k["fetter"])}', (21, 21, 21), genshin_font(18))
            char_crop = (70 + 125 * (num_2 % 4), 180)
            abyss2.paste(char_img, char_crop, char_img)
            num_2 = num_2 + 1
        star_num = based_data['levels'][j]['star']
        if star_num == 1:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star0, (685, 155), abyss_star0)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        elif star_num == 0:
            abyss2.paste(abyss_star0, (640, 155), abyss_star0)
            abyss2.paste(abyss_star0, (685, 155), abyss_star0)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        elif star_num == 2:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star1, (685, 155), abyss_star1)
            abyss2.paste(abyss_star0, (730, 155), abyss_star0)
        else:
            abyss2.paste(abyss_star1, (640, 155), abyss_star1)
            abyss2.paste(abyss_star1, (685, 155), abyss_star1)
            abyss2.paste(abyss_star1, (730, 155), abyss_star1)
        abyss2_text_draw = ImageDraw.Draw(abyss2)
        abyss2_text_draw.text((87, 30), f'第{j + 1}间', text_color, genshin_font(21))
        timestamp1 = int(based_data['levels'][j]['battles'][0]['timestamp'])
        timestamp2 = int(based_data['levels'][j]['battles'][1]['timestamp'])
        time_array1 = time.localtime(timestamp1)
        time_array2 = time.localtime(timestamp2)
        other_style_time1 = time.strftime('%Y--%m--%d %H:%M:%S', time_array1)
        other_style_time2 = time.strftime('%Y--%m--%d %H:%M:%S', time_array2)
        abyss2_text_draw.text((167, 33), f'{other_style_time1}/{other_style_time2}', text_color, genshin_font(19))
        bg_img.paste(abyss2, (0, 350 + j * 340), abyss2)

    bg_img.paste(abyss3, (0, len(based_data['levels']) * 340 + 400), abyss3)

    text_draw = ImageDraw.Draw(bg_img)

    text_draw.text((220, 163), f'{nickname}', text_color, genshin_font(32))
    text_draw.text((235, 203), 'UID ' + f'{uid}', text_color, genshin_font(14))
    text_draw.text((710, 190), f'{floor_num}', text_color, genshin_font(50), anchor='mm')

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    # bg_img.save(result_buffer, format='PNG')
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    # resultmes = f'[CQ:image,file={imgmes}]'
    resultmes = imgmes
    return resultmes


async def get_all_calculate_info(client: ClientSession, uid: str, char_id: List[str], ck: str, name: list):
    tasks = []
    for id_, name_ in zip(char_id, name):
        tasks.append(get_calculate_info(client, uid, id_, ck, name_))
    data = []
    repos = await asyncio.wait(tasks)
    for i in repos[0]:
        data.append(i.result())
    return data


async def draw_char_pic(img: Image, char_data: dict, index: int, bg_color: Tuple[int, int, int],
                        text_color: Tuple[int, int, int], bg_detail_color: Tuple[int, int, int],
                        char_high_color: Tuple[int, int, int], char_talent_data: dict):
    char_mingzuo = 0
    for k in char_data['constellations']:
        if k['is_actived']:
            char_mingzuo += 1
    if char_data['rarity'] == 5:
        char_0 = Image.new('RGBA', (180, 90), char_high_color)
    else:
        char_0 = Image.new('RGBA', (180, 90), bg_color)
    char_0_raw = Image.open(os.path.join(TEXT_PATH, 'char_0.png'))
    alpha = char_0_raw.getchannel('A')
    char_0.putalpha(alpha)

    char_2 = Image.new('RGBA', (180, 90), bg_detail_color)
    char_2_raw = Image.open(os.path.join(TEXT_PATH, 'char_2.png'))
    alpha = char_2_raw.getchannel('A')
    char_2.putalpha(alpha)

    """
    char_3 = Image.new('RGBA', (180, 90), bg_detail_color)
    char_3_raw = Image.open(os.path.join(TEXT_PATH, 'char_3.png'))
    alpha = char_3_raw.getchannel('A')
    char_3.putalpha(alpha) 
    """
    char_1_mask = Image.open(os.path.join(TEXT_PATH, 'char_1_mask.png'))
    STATUS.append(char_data['name'])
    if not os.path.exists(os.path.join(WEAPON_PATH, str(char_data['weapon']['icon'].split('/')[-1]))):
        get_weapon_pic(char_data['weapon']['icon'])
    if not os.path.exists(os.path.join(CHAR_PATH, str(char_data['id']) + '.png')):
        get_char_pic(char_data['id'], char_data['icon'])

    char_img = Image.open(os.path.join(CHAR_PATH, str(char_data['id']) + '.png')).resize((81, 81),
                                                                                         Image.ANTIALIAS)
    weapon_img = Image.open(
        os.path.join(WEAPON_PATH, str(char_data['weapon']['icon'].split('/')[-1]))).resize((40, 40),
                                                                                           Image.ANTIALIAS)
    weapon_1_mask = char_1_mask.resize((40, 40), Image.ANTIALIAS)
    char_0_temp = Image.new('RGBA', (180, 90))
    char_0_temp.paste(char_img, (8, 5), char_1_mask)
    char_0_temp.paste(weapon_img, (70, 45), weapon_1_mask)
    char_0.paste(char_0_temp, (0, 0), char_0_temp)
    char_0.paste(char_2, (0, 0), char_2)
    # char_0.paste(char_3, (0, 0), char_3)
    draw_text = ImageDraw.Draw(char_0)
    for i in range(0, 2):
        draw_text.text((106 + 23 * i, 17),
                       f'{str(char_talent_data["data"]["skill_list"][i]["level_current"])}', text_color,
                       genshin_font(15), anchor='mm')

    if len(char_talent_data['data']['skill_list']) == 7 and char_data['name'] != '珊瑚宫心海':
        draw_text.text((106 + 23 * 2, 17),
                       f'{str(char_talent_data["data"]["skill_list"][3]["level_current"])}', text_color,
                       genshin_font(15), anchor='mm')
    else:
        draw_text.text((106 + 23 * 2, 17),
                       f'{str(char_talent_data["data"]["skill_list"][2]["level_current"])}', text_color,
                       genshin_font(15), anchor='mm')

    draw_text.text((42, 77), 'Lv.{}'.format(str(char_data['level'])), text_color, genshin_font(16),
                   anchor='mm')
    draw_text.text((162, 38), '{}命'.format(char_mingzuo), text_color, genshin_font(18), anchor='rm')
    draw_text.text((115, 57), 'Lv.{}'.format(str(char_data['weapon']['level'])), text_color,
                   genshin_font(18), anchor='lm')
    draw_text.text((115, 75), '{}精'.format(str(char_data['weapon']['affix_level'])), text_color,
                   genshin_font(16), anchor='lm')

    if str(char_data['fetter']) == '10' or str(char_data['name']) == '旅行者':
        draw_text.text((74, 19), '♥', text_color, genshin_font(14), anchor='mm')
    else:
        draw_text.text((73, 18), '{}'.format(str(char_data['fetter'])), text_color, genshin_font(16),
                       anchor='mm')

    char_crop = (75 + 190 * (index % 4), 900 + 100 * (index // 4))
    STATUS.remove(char_data['name'])
    img.paste(char_0, char_crop, char_0)


async def draw_pic(uid: str, nickname: str, image: Optional[Match] = None, mode: int = 2,
                   role_level: Optional[int] = None):
    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid, mode)
    if not retcode:
        return retcode
    use_cookies = data_def.useable_cookies
    raw_data = data_def.raw_data
    uid = data_def.uid
    nickname = data_def.nickname if data_def.nickname else nickname

    # 记录数据
    raw_data = raw_data['data']
    char_data = raw_data['avatars']

    char_ids = []
    char_names = []

    for i in char_data:
        char_ids.append(i['id'])
        char_names.append(i['name'])

    char_rawdata = get_character(uid, char_ids, use_cookies)
    char_datas = char_rawdata['data']['avatars']

    # 确定角色占用行数
    char_num = len(char_datas)
    char_hang = 1 + (char_num - 1) // 4 if char_num > 8 else char_num

    # 获取背景图片各项参数
    based_w = 900
    based_h = 970 + char_hang * 100 if char_num > 8 else 990 + char_hang * 110
    image_def = CustomizeImage(image, based_w, based_h)
    bg_img = image_def.bg_img
    bg_color = image_def.bg_color
    text_color = image_def.text_color
    # highlight_color = image_def.highlight_color
    char_color = image_def.char_color
    bg_detail_color = image_def.bg_detail_color
    char_high_color = image_def.char_high_color

    # 确定texture2D路径
    panle1_path = os.path.join(TEXT_PATH, 'panle_1.png')
    panle3_path = os.path.join(TEXT_PATH, 'panle_3.png')

    avatar_bg_path = os.path.join(TEXT_PATH, 'avatar_bg.png')
    avatar_fg_path = os.path.join(TEXT_PATH, 'avatar_fg.png')

    all_mask_path = os.path.join(TEXT_PATH, 'All_Mask.png')

    # 转换遮罩的颜色、大小匹配，并paste上去
    all_mask = Image.open(all_mask_path).resize(bg_img.size, Image.ANTIALIAS)
    all_mask_img = Image.new('RGBA', (based_w, based_h), bg_color)
    bg_img.paste(all_mask_img, (0, 0), all_mask)

    # 操作图片
    panle1 = Image.open(panle1_path)
    panle3 = Image.open(panle3_path)
    avatar_bg = Image.open(avatar_bg_path)
    avatar_fg = Image.open(avatar_fg_path)

    # 确定主体框架
    avatar_bg_color = Image.new('RGBA', (316, 100), bg_color)
    panle1_color = Image.new('RGBA', (900, 900), text_color)
    bg_img.paste(panle1_color, (0, 0), panle1)
    bg_img.paste(panle3, (0, char_hang * 100 + 880) if char_num > 8 else (0, char_hang * 110 + 900), panle3)
    bg_img.paste(avatar_bg_color, (113, 98), avatar_bg)
    bg_img.paste(avatar_fg, (114, 95), avatar_fg)

    # 绘制基础信息文字
    text_draw = ImageDraw.Draw(bg_img)

    if role_level:
        text_draw.text((140, 200), '冒险等级：' + f'{role_level}', text_color, genshin_font(20))

    text_draw.text((220, 123), f'{nickname}', text_color, genshin_font(32))
    text_draw.text((235, 163), 'UID ' + f'{uid}', text_color, genshin_font(14))

    # 活跃天数/成就数量/深渊信息
    text_draw.text((640, 94.8), str(raw_data['stats']['active_day_number']), text_color, genshin_font(26))
    text_draw.text((640, 139.3), str(raw_data['stats']['achievement_number']), text_color, genshin_font(26))
    text_draw.text((640, 183.9), raw_data['stats']['spiral_abyss'], text_color, genshin_font(26))

    # 奇馈宝箱
    text_draw.text((505, 375), str(raw_data['stats']['magic_chest_number']), text_color, genshin_font(24))

    # 开启锚点和秘境数量
    text_draw.text((505, 426), str(raw_data['stats']['way_point_number']), text_color, genshin_font(24))
    text_draw.text((505, 477), str(raw_data['stats']['domain_number']), text_color, genshin_font(24))

    # 已获角色
    text_draw.text((505, 528), str(raw_data['stats']['avatar_number']), text_color, genshin_font(24))

    # 宝箱
    text_draw.text((245, 375), str(raw_data['stats']['common_chest_number']), text_color, genshin_font(24))
    text_draw.text((245, 426), str(raw_data['stats']['exquisite_chest_number']), text_color, genshin_font(24))
    text_draw.text((245, 477), str(raw_data['stats']['precious_chest_number']), text_color, genshin_font(24))
    text_draw.text((245, 528), str(raw_data['stats']['luxurious_chest_number']), text_color, genshin_font(24))

    mondstadt = liyue = dragonspine = inazuma = offering = chasms_maw = under_chasms_maw = dict()
    for i in raw_data['world_explorations']:
        if i['name'] == '蒙德':
            mondstadt = i
        elif i['name'] == '璃月':
            liyue = i
        elif i['name'] == '龙脊雪山':
            dragonspine = i
        elif i['name'] == '稻妻':
            inazuma = i
        elif i['name'] == '渊下宫':
            offering = i
        elif i['name'] == '璃月层岩巨渊':
            chasms_maw = i
        elif i['name'] == '璃月层岩巨渊·地下矿区':
            under_chasms_maw = i

    # 层岩巨渊
    text_draw.text((477, 727), str(chasms_maw['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))
    text_draw.text((523, 753), str(under_chasms_maw['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))
    text_draw.text((500, 782), 'lv.' + str(under_chasms_maw['offerings'][0]['level']), text_color, genshin_font(22))

    # 蒙德
    text_draw.text((235, 600), str(mondstadt['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))
    text_draw.text((235, 630), 'lv.' + str(mondstadt['level']), text_color, genshin_font(22))
    text_draw.text((258, 660), str(raw_data['stats']['anemoculus_number']), text_color, genshin_font(22))

    # 璃月
    text_draw.text((480, 597), str(liyue['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))
    text_draw.text((480, 627), 'lv.' + str(liyue['level']), text_color, genshin_font(22))
    text_draw.text((503, 657), str(raw_data['stats']['geoculus_number']), text_color, genshin_font(22))

    # 雪山
    text_draw.text((238, 733), str(dragonspine['exploration_percentage'] / 10) + '%',
                   text_color,
                   genshin_font(22))
    text_draw.text((238, 764), 'lv.' + str(dragonspine['level']), text_color, genshin_font(22))

    # 稻妻
    text_draw.text((750, 588), str(inazuma['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))
    text_draw.text((750, 616), 'lv.' + str(inazuma['level']), text_color, genshin_font(22))
    text_draw.text((750, 644), 'lv.' + str(inazuma['offerings'][0]['level']), text_color,
                   genshin_font(22))
    text_draw.text((773, 672), str(raw_data['stats']['electroculus_number']), text_color, genshin_font(22))

    # 渊下宫
    text_draw.text((750, 750), str(offering['exploration_percentage'] / 10) + '%', text_color,
                   genshin_font(22))

    # 家园
    if len(raw_data['homes']):
        text_draw.text((720, 375), 'lv.' + str(raw_data['homes'][0]['level']), text_color, genshin_font(24))
        text_draw.text((720, 426), str(raw_data['homes'][0]['visit_num']), text_color, genshin_font(24))
        text_draw.text((720, 477), str(raw_data['homes'][0]['item_num']), text_color, genshin_font(24))
        text_draw.text((720, 528), str(raw_data['homes'][0]['comfort_num']), text_color, genshin_font(24))
    else:
        text_draw.text((720, 375), '未开', text_color, genshin_font(24))
        text_draw.text((720, 426), '未开', text_color, genshin_font(24))
        text_draw.text((720, 477), '未开', text_color, genshin_font(24))
        text_draw.text((720, 528), '未开', text_color, genshin_font(24))

    # 确定texture2D路径
    charpic_mask_path = os.path.join(TEXT_PATH, 'charpic_mask.png')
    weaponpic_mask_path = os.path.join(TEXT_PATH, 'weaponpic_mask.png')

    def get_text(star, step):
        return os.path.join(TEXT_PATH, '{}s_{}.png'.format(str(star), str(step)))

    charpic_mask = Image.open(charpic_mask_path)
    weaponpic_mask = Image.open(weaponpic_mask_path)
    """
    s5s1 = Image.open(get_text(5, 1))
    s5s2 = Image.open(get_text(5, 2))
    s5s3 = Image.open(get_text(5, 3))
    s5s4 = Image.open(get_text(5, 4))
    s4s1 = Image.open(get_text(4, 1))
    s4s2 = Image.open(get_text(4, 2))
    s4s3 = Image.open(get_text(4, 3))
    s4s4 = Image.open(get_text(4, 4))
    s3s3 = Image.open(get_text(3, 3))
    s2s3 = Image.open(get_text(2, 3))
    s1s3 = Image.open(get_text(1, 3))
    """
    char_bg_path = os.path.join(TEXT_PATH, 'char_bg.png')
    char_fg_path = os.path.join(TEXT_PATH, 'char_fg.png')

    char_bg = Image.open(char_bg_path)
    char_fg = Image.open(char_fg_path)

    num = 0
    for index, i in enumerate(char_datas):
        if i['rarity'] > 5:
            char_datas[index]['rarity'] = 3
    char_datas.sort(key=lambda x: (-x['rarity'], -x['level'], -x['fetter']))

    if char_num > 8:
        client = ClientSession()
        talent_data = await get_all_calculate_info(client, uid, char_ids,
                                                   use_cookies, char_names)
        await client.close()

        tasks = []
        for index, i in enumerate(char_datas):
            for j in talent_data:
                if j['name'] == i['name']:
                    tasks.append(
                        draw_char_pic(
                            bg_img,
                            i,
                            index,
                            char_color,
                            text_color,
                            bg_detail_color,
                            char_high_color,
                            j
                        )
                    )
        await asyncio.wait(tasks)
        """
            char_mingzuo = 0
            for k in i['constellations']:
                if k['is_actived']:
                    char_mingzuo += 1

            char_name = i['name']
            char_id = i['id']
            char_level = i['level']
            char_fetter = i['fetter']
            char_rarity = i['rarity']

            char_weapon_star = i['weapon']['rarity']
            char_weapon_jinglian = i['weapon']['affix_level']
            char_weapon_icon = i['weapon']['icon']

            if not os.path.exists(os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))):
                get_weapon_pic(char_weapon_icon)
            if not os.path.exists(os.path.join(CHAR_PATH, str(i['id']) + '.png')):
                get_char_pic(i['id'], i['icon'])

            char = os.path.join(CHAR_PATH, str(char_id) + '.png')
            weapon = os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))

            char_img = Image.open(char)
            char_img = char_img.resize((100, 100), Image.ANTIALIAS)
            weapon_img = Image.open(weapon)
            weapon_img = weapon_img.resize((47, 47), Image.ANTIALIAS)

            charpic = Image.new('RGBA', (125, 140))

            if char_rarity == 5:
                charpic.paste(s5s1, (0, 0), s5s1)
                baseda = Image.new('RGBA', (100, 100))
                cc = Image.composite(char_img, baseda, charpic_mask)
                charpic.paste(cc, (6, 15), cc)
                charpic.paste(s5s2, (0, 0), s5s2)
                if char_weapon_star == 5:
                    charpic.paste(s5s3, (0, 0), s5s3)
                elif char_weapon_star == 4:
                    charpic.paste(s4s3, (0, 0), s4s3)
                elif char_weapon_star == 3:
                    charpic.paste(s3s3, (0, 0), s3s3)
                elif char_weapon_star == 2:
                    charpic.paste(s2s3, (0, 0), s2s3)
                elif char_weapon_star == 1:
                    charpic.paste(s1s3, (0, 0), s1s3)
                basedb = Image.new('RGBA', (47, 47))
                dd = Image.composite(weapon_img, basedb, weaponpic_mask)
                charpic.paste(dd, (69, 62), dd)
                charpic.paste(s5s4, (0, 0), s5s4)

            else:
                charpic.paste(s4s1, (0, 0), s4s1)
                baseda = Image.new('RGBA', (100, 100))
                cc = Image.composite(char_img, baseda, charpic_mask)
                charpic.paste(cc, (6, 15), cc)
                charpic.paste(s4s2, (0, 0), s4s2)
                if char_weapon_star == 5:
                    charpic.paste(s5s3, (0, 0), s5s3)
                elif char_weapon_star == 4:
                    charpic.paste(s4s3, (0, 0), s4s3)
                elif char_weapon_star == 3:
                    charpic.paste(s3s3, (0, 0), s3s3)
                elif char_weapon_star == 2:
                    charpic.paste(s2s3, (0, 0), s2s3)
                elif char_weapon_star == 1:
                    charpic.paste(s1s3, (0, 0), s1s3)
                basedb = Image.new('RGBA', (47, 47))
                dd = Image.composite(weapon_img, basedb, weaponpic_mask)
                charpic.paste(dd, (69, 62), dd)
                charpic.paste(s4s4, (0, 0), s4s4)

            char_draw = ImageDraw.Draw(charpic)
            char_draw.text((38, 106), f'Lv.{str(char_level)}', (21, 21, 21), genshin_font(18))
            char_draw.text((104.5, 91.5), f'{str(char_weapon_jinglian)}', 'white', genshin_font(10))
            char_draw.text((99, 19.5), f'{str(char_mingzuo)}', 'white', genshin_font(18))
            if str(i['fetter']) == '10' or str(char_name) == '旅行者':
                char_draw.text((98, 42), '♥', (21, 21, 21), genshin_font(14))
            else:
                char_draw.text((100, 41), f'{str(char_fetter)}', (21, 21, 21), genshin_font(16))

            char_crop = (68 + 129 * (num % 6), 800 + 130 * (num // 6))
            bg_img.paste(charpic, char_crop, charpic)
            num = num + 1
        """
    else:
        charset_mask = Image.new('RGBA', (900, 130), char_color)
        for i in char_datas:
            char_mingzuo = 0
            for k in i['constellations']:
                if k['is_actived']:
                    char_mingzuo += 1

            char_name = i['name']
            char_id = i['id']
            char_level = i['level']
            char_img_icon = i['image']

            char_weapon_star = i['weapon']['rarity']
            char_weapon_level = i['weapon']['level']
            char_weapon_jinglian = i['weapon']['affix_level']
            char_weapon_icon = i['weapon']['icon']

            if not os.path.exists(os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))):
                get_weapon_pic(char_weapon_icon)
            if not os.path.exists(os.path.join(CHAR_IMG_PATH, str(char_img_icon.split('/')[-1]))):
                get_char_img_pic(char_img_icon)
            if not os.path.exists(os.path.join(CHAR_PATH, str(i['id']) + '.png')):
                get_char_pic(i['id'], i['icon'])

            char = os.path.join(CHAR_PATH, str(char_id) + '.png')
            weapon = os.path.join(WEAPON_PATH, str(char_weapon_icon.split('/')[-1]))
            char_stand_img = os.path.join(CHAR_IMG_PATH, str(char_img_icon.split('/')[-1]))
            char_stand_mask = Image.open(os.path.join(TEXT_PATH, 'stand_mask.png'))

            # char_namecard_img = Image.open(os.path.join(CHAR_NAMECARD_PATH,str(i['icon'].split('_')[-1])))
            # char_namecard_img = char_namecard_img.resize((591,81), Image.ANTIALIAS)
            # char_namecard_img.putalpha(char_namecard_img.getchannel('A').point(lambda i: i*0.8 if i>0 else 0))
            char_stand = Image.open(char_stand_img)
            char_img = Image.open(char)
            char_img = char_img.resize((100, 100), Image.ANTIALIAS)
            weapon_img = Image.open(weapon)
            weapon_img = weapon_img.resize((47, 47), Image.ANTIALIAS)

            charpic = Image.new('RGBA', (900, 130))
            charpic_temp = Image.new('RGBA', (900, 130))

            charpic.paste(charset_mask, (0, 0), char_bg)

            weapon_bg = Image.open(get_text(char_weapon_star, 3))
            charpic_temp.paste(char_stand, (395, -99), char_stand_mask)
            # charpic_temp.paste(char_namecard_img, (247, 24), char_namecard_img)
            charpic.paste(weapon_bg, (72, 10), weapon_bg)
            charpic_temp.paste(char_img, (81, 13), charpic_mask)
            charpic_temp.paste(char_fg, (0, 0), char_fg)
            charpic_temp.paste(weapon_img, (141, 72), weaponpic_mask)
            # temp = Image.composite(weapon_img, basedb, weaponpic_mask)
            charpic.paste(charpic_temp, (0, 0), charpic_temp)

            for _, k in enumerate(i['reliquaries']):
                if not os.path.exists(os.path.join(REL_PATH, str(k['icon'].split('/')[-1]))):
                    get_rel_pic(k['icon'])
                rel = os.path.join(REL_PATH, str(k['icon'].split('/')[-1]))
                rel_img = Image.open(rel).resize((43, 43), Image.ANTIALIAS)
                rel_bg = Image.open(get_text(k['rarity'], 3))

                if k['pos_name'] == '生之花':
                    charpic.paste(rel_bg, (287 + 55 * 0, -14), rel_bg)
                    charpic.paste(rel_img, (360 + 55 * 0, 49), rel_img)
                elif k['pos_name'] == '死之羽':
                    charpic.paste(rel_bg, (287 + 55 * 1, -14), rel_bg)
                    charpic.paste(rel_img, (360 + 55 * 1, 49), rel_img)
                elif k['pos_name'] == '时之沙':
                    charpic.paste(rel_bg, (287 + 55 * 2, -14), rel_bg)
                    charpic.paste(rel_img, (360 + 55 * 2, 49), rel_img)
                elif k['pos_name'] == '空之杯':
                    charpic.paste(rel_bg, (287 + 55 * 3, -14), rel_bg)
                    charpic.paste(rel_img, (360 + 55 * 3, 49), rel_img)
                elif k['pos_name'] == '理之冠':
                    charpic.paste(rel_bg, (287 + 55 * 4, -14), rel_bg)
                    charpic.paste(rel_img, (360 + 55 * 4, 49), rel_img)

            char_draw = ImageDraw.Draw(charpic)

            char_draw.text((188, 30), i['name'] + ' ' + f'Lv.{str(char_level)}', text_color, genshin_font(22))
            char_draw.text((222, 87), f'{str(i["fetter"])}' if str(char_name) != '旅行者' else '10', text_color,
                           genshin_font(15), anchor='mm')
            char_draw.text((255, 87), f'{str(char_mingzuo)}', text_color, genshin_font(15), anchor='mm')
            char_draw.text((218, 67), f'{str(char_weapon_level)}级{str(char_weapon_jinglian)}精', text_color,
                           genshin_font(15),
                           anchor='lm')
            char_crop = (0, 900 + 110 * num)
            num += 1
            bg_img.paste(charpic, char_crop, charpic)

    # 转换之后发送
    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = imgmes
    return resultmes


async def draw_info_pic(uid: str, image: Optional[Match] = None) -> str:
    def seconds2hours(seconds: int) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return '%02d:%02d:%02d' % (h, m, s)

    # 获取Cookies
    data_def = GetCookies()
    retcode = await data_def.get_useable_cookies(uid)
    if not retcode:
        return retcode
    raw_data = data_def.raw_data
    char_data = raw_data['data']['avatars']
    # 获取数据
    award_data = await get_award(uid)
    daily_data = await get_daily_data(uid)
    daily_data = daily_data['data']
    nickname = award_data['data']['nickname']

    # 获取背景图片各项参数
    based_w = 900
    based_h = 1480
    image_def = CustomizeImage(image, based_w, based_h)
    bg_img = image_def.bg_img
    bg_color = image_def.bg_color
    text_color = image_def.text_color
    highlight_color = image_def.highlight_color
    char_color = image_def.char_color

    # 确定texture2D路径
    info1_path = os.path.join(TEXT_PATH, 'info_1.png')
    info2_path = os.path.join(TEXT_PATH, 'info_2.png')
    info3_path = os.path.join(TEXT_PATH, 'info_3.png')

    avatar_bg_path = os.path.join(TEXT_PATH, 'avatar_bg.png')
    avatar_fg_path = os.path.join(TEXT_PATH, 'avatar_fg.png')

    all_mask_path = os.path.join(TEXT_PATH, 'All_Mask.png')

    # 转换遮罩的颜色、大小匹配，并paste上去
    all_mask = Image.open(all_mask_path).resize(bg_img.size, Image.ANTIALIAS)
    all_mask_img = Image.new('RGBA', (based_w, based_h), bg_color)
    bg_img.paste(all_mask_img, (0, 0), all_mask)

    # 操作图片
    info1 = Image.open(info1_path)
    info2 = Image.open(info2_path)
    info3 = Image.open(info3_path)
    avatar_bg = Image.open(avatar_bg_path)
    avatar_fg = Image.open(avatar_fg_path)

    avatar_bg_color = Image.new('RGBA', (316, 100), bg_color)
    bg_img.paste(avatar_bg_color, (113, 98), avatar_bg)
    bg_img.paste(avatar_fg, (114, 95), avatar_fg)

    info1_color = Image.new('RGBA', (900, 1400), bg_color)
    bg_img.paste(info1_color, (0, 0), info1)

    info2_color = Image.new('RGBA', (900, 1400), text_color)
    bg_img.paste(info2_color, (0, 0), info2)

    bg_img.paste(info3, (0, 0), info3)

    text_draw = ImageDraw.Draw(bg_img)

    # 用户信息
    text_draw.text((220, 137), f'{nickname}', text_color, genshin_font(32), anchor='lm')
    text_draw.text((235, 170), 'UID ' + f'{uid}', text_color, genshin_font(14), anchor='lm')

    # 本日原石/摩拉
    text_draw.text((675, 148),
                   f'{award_data["data"]["day_data"]["current_primogems"]}/'
                   f'{award_data["data"]["day_data"]["last_primogems"]}',
                   text_color, genshin_font(28), anchor='lm')
    text_draw.text((675, 212),
                   f'{award_data["data"]["day_data"]["current_mora"]}\n{award_data["data"]["day_data"]["last_mora"]}',
                   text_color, genshin_font(28), anchor='lm')

    # 本月/上月原石
    text_draw.text((722, 287), f'{award_data["data"]["month_data"]["current_primogems"]}', text_color, genshin_font(21),
                   anchor='lm')
    text_draw.text((722, 323), f'{award_data["data"]["month_data"]["last_primogems"]}', text_color, genshin_font(21),
                   anchor='lm')

    # 本月/上月摩拉
    text_draw.text((722, 359), f'{award_data["data"]["month_data"]["current_mora"]}', text_color, genshin_font(21),
                   anchor='lm')
    text_draw.text((722, 395), f'{award_data["data"]["month_data"]["last_mora"]}', text_color, genshin_font(21),
                   anchor='lm')

    # 收入比例
    group_by = award_data['data']['month_data']['group_by']
    group_by.sort(key=lambda x: (-x['action_id']))
    for index, i in enumerate(group_by):
        text_draw.text((681, 447 + index * 42), f'{str(i["num"])}({str(i["percent"])}%)', text_color, genshin_font(21),
                       anchor='lm')

    # 基本四项
    text_draw.text((390, 314), f'{daily_data["current_resin"]}/{daily_data["max_resin"]}', text_color, genshin_font(26),
                   anchor='lm')
    text_draw.text((390, 408), f'{daily_data["current_home_coin"]}/{daily_data["max_home_coin"]}', text_color,
                   genshin_font(26), anchor='lm')
    text_draw.text((390, 503), f'{daily_data["finished_task_num"]}/{daily_data["total_task_num"]}', text_color,
                   genshin_font(26), anchor='lm')
    text_draw.text((390, 597),
                   f'{str(daily_data["resin_discount_num_limit"] - daily_data["remain_resin_discount_num"])}/'
                   f'{daily_data["resin_discount_num_limit"]}',
                   text_color, genshin_font(26), anchor='lm')

    # 参量质变仪
    if daily_data['transformer']['recovery_time']['reached']:
        transformer_status = '已处于可用状态'
        text_draw.text((170, 707), f'{transformer_status}', highlight_color, genshin_font(18), anchor='lm')
    else:
        transformer_time = daily_data['transformer']['recovery_time']
        transformer_status = '还剩{}天{}小时{}分钟可用'.format(transformer_time['Day'], transformer_time['Hour'],
                                                      transformer_time['Minute'])
        text_draw.text((170, 707), f'{transformer_status}', text_color, genshin_font(18), anchor='lm')

    # 树脂恢复时间计算
    if int(daily_data['resin_recovery_time']) <= 0:
        text_draw.text((170, 331), f'已全部恢复', text_color, genshin_font(18), anchor='lm')
    else:
        resin_recovery_time = seconds2hours(
            daily_data['resin_recovery_time'])
        next_resin_rec_time = seconds2hours(
            8 * 60 - ((daily_data['max_resin'] - daily_data['current_resin']) * 8 * 60 - int(
                daily_data['resin_recovery_time'])))
        text_draw.text((268, 305), f' {next_resin_rec_time}', text_color, genshin_font(18), anchor='lm')

        text_draw.text((170, 331), f'预计                后全部恢复', text_color, genshin_font(18), anchor='lm')
        text_draw.text((208, 331), f'{resin_recovery_time}', highlight_color, genshin_font(18), anchor='lm')

    # 洞天宝钱时间计算
    coin_rec_time = seconds2hours(int(daily_data['home_coin_recovery_time']))

    if int(daily_data['home_coin_recovery_time']) <= 0:
        text_draw.text((170, 425), f'已达到上限', text_color, genshin_font(18), anchor='lm')
    else:
        coin_add_speed = math.ceil((daily_data['max_home_coin'] - daily_data['current_home_coin']) / (
                int(daily_data['home_coin_recovery_time']) / 60 / 60))
        text_draw.text((270, 399), f'约{coin_add_speed}/h', text_color, genshin_font(18), anchor='lm')
        text_draw.text((170, 425), f'预计                 后达到上限', text_color, genshin_font(18), anchor='lm')
        text_draw.text((208, 425), f'{coin_rec_time}', highlight_color, genshin_font(18), anchor='lm')

    if daily_data['is_extra_task_reward_received']:
        daily_task_status = '「每日委托」奖励已领取'
    else:
        daily_task_status = '「每日委托」奖励未领取'

    # 详细信息
    text_draw.text((170, 518), f'{daily_task_status}', text_color, genshin_font(18), anchor='lm')
    text_draw.text((170, 614), f'本周剩余消耗减半次数', text_color, genshin_font(18), anchor='lm')

    # 派遣图片准备
    char_bg_path = os.path.join(TEXT_PATH, 'char_bg.png')

    char_bg = Image.open(char_bg_path)
    charset_mask = Image.new('RGBA', (900, 130), char_color)

    # 派遣
    for index, i in enumerate(daily_data['expeditions']):
        name = ''
        for j in char_data:
            if i['avatar_side_icon'].split('_')[-1] == j['image'].split('_')[-1]:
                name = j['name']
        if not os.path.exists(
                os.path.join(CHAR_IMG_PATH, f'UI_AvatarIcon_{i["avatar_side_icon"].split("_")[-1][:-4]}@2x.png')):
            get_char_img_pic(
                f'https://upload-bbs.mihoyo.com/game_record/genshin/character_image'
                f'/UI_AvatarIcon_{i["avatar_side_icon"].split("_")[-1][:-4]}@2x.png')
        # char_stand_img = os.path.join(CHAR_IMG_PATH, f'UI_AvatarIcon_{i['avatar_side_icon'].split('_')[-1][
        # :-4]}@2x.png') char_stand = Image.open(char_stand_img) char_stand_mask = Image.open(os.path.join(TEXT_PATH,
        # 'stand_mask.png'))

        # charpic_temp = Image.new('RGBA', (900, 130))
        # charpic_temp.paste(char_stand, (395, -99), char_stand_mask)
        charpic = Image.new('RGBA', (900, 130))
        char_icon = Image.open(BytesIO(get(i['avatar_side_icon']).content))

        char_namecard_img = Image.open(os.path.join(CHAR_NAMECARD_PATH, str(name + '.png')))
        char_namecard_img = char_namecard_img.resize((591, 81), Image.ANTIALIAS)
        char_namecard_img.putalpha(char_namecard_img.getchannel('A').point(lambda x: round(x * 0.8) if x > 0 else 0))

        char_icon_scale = char_icon.resize((140, 140), Image.ANTIALIAS)
        charpic.paste(charset_mask, (0, 0), char_bg)
        charpic.paste(char_icon_scale, (63, -26), char_icon_scale)
        charpic.paste(char_namecard_img, (247, 24), char_namecard_img)

        charpic_draw = ImageDraw.Draw(charpic)

        if i['status'] == 'Finished':
            charpic_draw.text((200, 65), f'探索完成', text_color, genshin_font(24), anchor='lm')
        else:
            remained_timed: str = seconds2hours(i['remained_time'])
            charpic_draw.text((200, 65), f'剩余时间 {remained_timed}', text_color, genshin_font(24), anchor='lm')

        bg_img.paste(charpic, (-15, 848 + 115 * index), charpic)

    end_pic = Image.open(os.path.join(TEXT_PATH, 'abyss_3.png'))
    bg_img.paste(end_pic, (0, 1440), end_pic)

    bg_img = bg_img.convert('RGB')
    result_buffer = BytesIO()
    bg_img.save(result_buffer, format='JPEG', subsampling=0, quality=90)
    imgmes = 'base64://' + b64encode(result_buffer.getvalue()).decode()
    resultmes = imgmes
    return resultmes


async def draw_event_pic() -> None:
    raw_data = await get_genshin_events('List')
    raw_time_data = await get_genshin_events('Content')

    data = raw_data['data']['list'][1]['list']

    event_data = {'gacha_event': [], 'normal_event': [], 'other_event': []}
    for k in data:
        for i in raw_time_data['data']['list']:
            if k['title'] in i['title']:
                content_bs = BeautifulSoup(i['content'], 'lxml')
                for index, value in enumerate(content_bs.find_all('p')):
                    if value.text == '〓任务开放时间〓':
                        time_data = content_bs.find_all('p')[index + 1].text
                        if '<t class=' in time_data:
                            time_data = findall('<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>', time_data)[0]
                        k['time_data'] = time_data
                    elif value.text == '〓活动时间〓':
                        time_data = content_bs.find_all('p')[index + 1].text
                        if '<t class=' in time_data:
                            time_datas = []
                            for s in time_data.split(' ~ '):
                                if '<t class=' in s:
                                    time_datas.append(findall('<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>', s)[0])
                                else:
                                    time_datas.append(s)
                            k['time_data'] = '——'.join(time_datas)
                        else:
                            k['time_data'] = time_data
                    elif value.text == '〓祈愿介绍〓':
                        start_time = content_bs.find_all('tr')[1].td.find_all('p')[0].text
                        if '<t class=' in start_time:
                            start_time = findall('<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>', start_time)[0]
                        end_time = findall('<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                           content_bs.find_all('tr')[1].td.find_all('p')[2].text)[0]
                        if '<t class=' in end_time:
                            end_time = findall('<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>', end_time)[0]
                        time_data = start_time + '——' + end_time
                        k['time_data'] = time_data

        if '冒险助力礼包' in k['title'] or '纪行' in k['title']:
            continue
        # if '角色试用' in k['title'] or '传说任务' in k['title']:
        #    event_data['other_event'].append(k)
        elif k['tag_label'] == '扭蛋':
            event_data['gacha_event'].append(k)
        elif k['tag_label'] == '活动':
            event_data['normal_event'].append(k)

    # base_h = 900 + ((1 + (len(event_data['normal_event'])+len(event_data['other_event'])))//2)*390 + ((1 + len(
    # event_data['gacha_event']))//2)*533
    base_h = 600 + len(event_data['normal_event']) * (390 + 90) + len(event_data['gacha_event']) * (533 + 90)
    base_img = Image.new(mode='RGB', size=(1080, base_h), color=(237, 217, 195))

    event1_path = os.path.join(TEXT_PATH, 'event_1.png')
    event2_path = os.path.join(TEXT_PATH, 'event_2.png')
    # event3_path = os.path.join(TEXT_PATH,'event_3.png')
    event1 = Image.open(event1_path)
    event2 = Image.open(event2_path)
    # event3 = Image.open(event3_path)

    base_img.paste(event1, (0, 0), event1)
    # base_img.paste(event2,(0,300+((1+len(event_data['normal_event']))//2)*390),event2)
    base_img.paste(event2, (0, len(event_data['normal_event']) * (390 + 90) + 300), event2)
    # base_img.paste(event3,(0,600+((1+len(event_data['normal_event']))//2)*390 + ((1 + len(event_data[
    # 'gacha_event']))//2)*533),event3)

    time_img1 = Image.new(mode='RGB', size=(1080, len(event_data['normal_event']) * (390 + 90)), color=(237, 130, 116))
    time_img2 = Image.new(mode='RGB', size=(1080, len(event_data['gacha_event']) * (533 + 90)), color=(237, 130, 116))
    base_img.paste(time_img1, (0, 300))
    base_img.paste(time_img2, (0, 600 + len(event_data['normal_event']) * (390 + 90)))
    base_draw = ImageDraw.Draw(base_img)
    for index, value in enumerate(event_data['normal_event']):
        img = Image.open(BytesIO(get(value['banner']).content))
        base_draw.text((540, 300 + 45 + 390 + (390 + 90) * index + 1),
                       value['time_data'], (255, 255, 255), genshin_font(42),
                       anchor='mm')
        # base_img.paste(img,((index%2)*1080,300 + 390*(index//2)))
        base_img.paste(img, (0, 300 + (390 + 90) * index))

    for index, value in enumerate(event_data['gacha_event']):
        img = Image.open(BytesIO(get(value['banner']).content))
        base_draw.text((540, 600 + 45 + (390 + 90) * len(event_data['normal_event']) + 533 + index * (533 + 90)),
                       value['time_data'], (255, 255, 255), genshin_font(42),
                       anchor='mm')
        # base_img.paste(img,((index%2)*1080,600 + ((1 + len(event_data['normal_event']))//2)*390 + 533*(index//2)))
        base_img.paste(img, (0, 600 + (390 + 90) * len(event_data['normal_event']) + index * (533 + 90)))
    # for index,value in enumerate(event_data['other_event']): img = Image.open(BytesIO(requests.get(value[
    # 'banner']).content)) base_img.paste(img,((index%2)*1080,900 + ((1 + len(event_data['normal_event']))//2)*390 +
    # ((1 + len(event_data['gacha_event']))//2)*533 + 390*(index//2)))

    base_img = base_img.convert('RGB')
    base_img.save(os.path.join(FILE2_PATH, 'event.jpg'), format='JPEG', subsampling=0, quality=90)

    return
