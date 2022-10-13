from io import BytesIO
from re import findall
from typing import List
from pathlib import Path
from datetime import datetime

from httpx import get
from PIL import Image, ImageDraw

from ..version import Genshin_version
from ..utils.ambr_api.get_ambr_data import get_event_data
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'
IMG_PATH = Path(__file__).parent / 'event.jpg'

PATTERN = r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>'


async def get_month_and_time(time_data: str) -> List:
    """
    :说明:
      接收时间字符串`2022/02/09 18:59:59`
      转换为`['02/09', '18:59PM']`
    :参数:
      * time_data (str): 时间字符串。
    :返回:
      * [month, time] (list): ['02/09', '18:59PM']。
    """
    if '永久开放' in time_data:
        month = time_data[:5]
        time = '永久开放'
    if '更新后' in time_data or '版本' in time_data:
        month = time_data[:5]
        time = '更新后'
    else:
        time_data = time_data.split(' ')  # type: ignore
        time_data[0] = time_data[0].replace('-', '/')  # type: ignore
        month = time_data[0].split('/', 1)[1]
        time = ':'.join(time_data[1].split(':')[:-1])
        if int(time.split(':')[0]) <= 12:
            time = time + 'AM'
        else:
            time = time + 'PM'
    return [month, time]


async def save_draw_event_img() -> None:
    """
    :说明:
      绘制原神活动列表图片_，存放至同级目录``event.png``。
    """
    event_list = await get_event_data()

    event_data_list = {
        'gacha_event': [],
        'normal_event': [],
        'other_event': [],
    }
    for event in event_list:
        # 跳过一部分活动
        flag = False
        name_full = event_list[event]['nameFull']['CHS']
        for ban_word in ['首充', '深境螺旋', '传说任务', '纪行', '更新修复']:
            if ban_word in name_full:
                flag = True
                break

        if flag:
            continue

        event_data = {}

        # 确定结束时间
        start_time = f'{Genshin_version[:-2]}更新后'
        end_time = event_list[event]['endAt']  # 2022-11-01 14:59:59

        event_data['banner'] = event_list[event]['banner']['CHS']
        desc = event_list[event]['description']['CHS']
        desc_content = findall(
            r'(</span></strong></p>)?<p><span>(<t class=\"t_lc\">)?'
            r'(\d.\d[^<]+|\d{4}\d{2}\d{2} \d{2}:\d{2}:\d{2})'
            r'(</span></p><p><span>|</t>)',
            desc,
        )
        if desc_content:
            start_time = desc_content[0][2]

        event_data['start_time'] = await get_month_and_time(start_time)
        event_data['end_time'] = await get_month_and_time(end_time)
        if '祈愿' in name_full or '扭蛋' in name_full:
            event_data_list['gacha_event'].append(event_data)
        else:
            event_data_list['normal_event'].append(event_data)

    base_h = (
        450
        + len(event_data_list['normal_event']) * (270 + 10)
        + len(event_data_list['gacha_event']) * (370 + 10)
    )
    base_img = Image.new(
        mode='RGBA', size=(950, base_h), color=(255, 253, 248, 255)
    )

    text_color = (60, 59, 64)
    event_color = (250, 93, 93)
    gacha_color = (93, 198, 250)
    font_l = genshin_font_origin(52)
    font_m = genshin_font_origin(34)
    font_s = genshin_font_origin(28)

    now_time = datetime.now().strftime('%Y/%m/%d')
    event_title_path = TEXT_PATH / 'event_title.png'
    event_title = Image.open(event_title_path)
    event_title_draw = ImageDraw.Draw(event_title)
    event_title_draw.text(
        (7, 380), now_time, font=font_l, fill=text_color, anchor='lm'
    )
    base_img.paste(event_title, (0, 0), event_title)

    for index, value in enumerate(event_data_list['normal_event']):
        event_img = Image.new(mode='RGBA', size=(950, 280))
        img = Image.open(BytesIO(get(value['banner']).content))
        img = img.resize((745, 270), Image.Resampling.LANCZOS)
        event_img.paste(img, (205, 10))
        event_img_draw = ImageDraw.Draw(event_img)

        if isinstance(value['start_time'], str):
            value['start_time'] = await get_month_and_time(value['start_time'])
        if isinstance(value['end_time'], str):
            value['end_time'] = await get_month_and_time(value['end_time'])
        event_img_draw.rectangle(((0, 0), (950, 10)), fill=event_color)
        event_img_draw.polygon(
            [(32, 150), (32, 176), (55, 163)], fill=(243, 110, 110)
        )
        event_img_draw.text(
            (8, 83), value['start_time'][0], text_color, font_l, anchor='lm'
        )
        event_img_draw.text(
            (8, 129), value['start_time'][1], text_color, font_s, anchor='lm'
        )
        event_img_draw.text(
            (39, 213), value['end_time'][0], text_color, font_l, anchor='lm'
        )
        event_img_draw.text(
            (39, 256), value['end_time'][1], text_color, font_s, anchor='lm'
        )

        base_img.paste(event_img, (0, 450 + 280 * index), event_img)

    for index, value in enumerate(event_data_list['gacha_event']):
        event_img = Image.new(mode='RGBA', size=(950, 380))
        img = Image.open(BytesIO(get(value['banner']).content))
        img = img.resize((745, 370), Image.Resampling.LANCZOS)
        event_img.paste(img, (205, 10))
        event_img_draw = ImageDraw.Draw(event_img)

        event_img_draw.rectangle(((0, 0), (950, 10)), fill=gacha_color)
        event_img_draw.rectangle(((8, 45), (58, 75)), fill=gacha_color)
        event_img_draw.text((65, 60), '祈愿', text_color, font_m, anchor='lm')
        event_img_draw.polygon(
            [(32, 250), (32, 276), (55, 263)], fill=(243, 110, 110)
        )
        event_img_draw.text(
            (8, 183), value['start_time'][0], text_color, font_l, anchor='lm'
        )
        event_img_draw.text(
            (8, 229), value['start_time'][1], text_color, font_s, anchor='lm'
        )
        event_img_draw.text(
            (39, 313), value['end_time'][0], text_color, font_l, anchor='lm'
        )
        event_img_draw.text(
            (39, 356), value['end_time'][1], text_color, font_s, anchor='lm'
        )

        base_img.paste(
            event_img,
            (
                0,
                450 + len(event_data_list['normal_event']) * 280 + 380 * index,
            ),
            event_img,
        )

    base_img = base_img.convert('RGB')
    base_img.save(IMG_PATH, format='JPEG', subsampling=0, quality=90)
    return
