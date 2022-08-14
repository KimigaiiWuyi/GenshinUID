from io import BytesIO
from re import findall
from pathlib import Path
from datetime import datetime
from typing import Any, List, Tuple, Union

from httpx import get
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .get_event_data import get_genshin_events
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'
IMG_PATH = Path(__file__).parent / 'event.jpg'


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
    if '更新后' in time_data:
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
      绘制原神活动列表图片，存放至同级目录``event.png``。
    """
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
                            time_data = findall(
                                r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                time_data,
                            )[0]
                        month_start, time_start = await get_month_and_time(
                            time_data
                        )
                        k['start_time'] = [month_start, time_start]
                        k['end_time'] = ['更新后', '永久开放']
                    elif value.text == '〓活动时间〓':
                        time_data = content_bs.find_all('p')[index + 1].text
                        if '<t class=' in time_data:
                            time_datas = []
                            for s in time_data.split(' ~ '):
                                if '<t class=' in s:
                                    time_datas.append(
                                        findall(
                                            r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                            s,
                                        )[0]
                                    )
                                else:
                                    time_datas.append(s)
                            if ' ' in time_datas[0]:
                                (
                                    month_start,
                                    time_start,
                                ) = await get_month_and_time(time_datas[0])
                            else:
                                month_start, time_start = '版本更新后', '更新后'

                            if ' ' in time_datas[1]:
                                month_end, time_end = await get_month_and_time(
                                    time_datas[1]
                                )
                            elif '版本结束' in time_datas[1]:
                                month_end, time_end = time_datas[1][:5], '结束后'
                            else:
                                month_end, time_end = '更新后', '永久开放'
                            k['start_time'] = [month_start, time_start]
                            k['end_time'] = [month_end, time_end]
                        elif '活动内容' in time_data:
                            for n in range(2, 10):
                                time_data = content_bs.find_all('p')[
                                    index + n
                                ].text
                                if '版本更新后' in time_data:
                                    time_data_end = content_bs.find_all('p')[
                                        index + n + 1
                                    ].text
                                    if '<t class=' in time_data_end:
                                        time_data_end = findall(
                                            r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                            time_data_end,
                                        )[0]
                                        (
                                            month_end,
                                            time_end,
                                        ) = await get_month_and_time(
                                            time_data_end
                                        )
                                        k['start_time'] = [
                                            time_data[:5],
                                            '更新后',
                                        ]
                                        k['end_time'] = [month_end, time_end]
                                    else:
                                        k['start_time'] = [time_data, '维护后']
                                        k['end_time'] = ['更新后', '永久开放']
                                    break
                                elif '<t class=' in time_data:
                                    time_data = findall(
                                        r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                        time_data,
                                    )[0]
                                    (
                                        month_start,
                                        time_start,
                                    ) = await get_month_and_time(time_data)
                                    k['start_time'] = [month_start, time_start]
                                    time_data_end = content_bs.find_all('p')[
                                        index + n + 1
                                    ].text
                                    if '<t class=' in time_data_end:
                                        time_data_end = findall(
                                            r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                            time_data_end,
                                        )[0]
                                        (
                                            month_end,
                                            time_end,
                                        ) = await get_month_and_time(
                                            time_data_end
                                        )
                                        k['end_time'] = [month_end, time_end]
                                    elif '版本结束' in time_data_end:
                                        k['end_time'] = [
                                            time_data_end[1:6],
                                            '结束',
                                        ]
                                    else:
                                        k['end_time'] = ['更新后', '永久开放']
                                    break
                        else:
                            month_start, time_start = await get_month_and_time(
                                time_data
                            )
                            k['start_time'] = [month_start, time_start]
                            k['end_time'] = ['更新后', '永久开放']
                    elif value.text == '〓祈愿介绍〓':
                        start_time = (
                            content_bs.find_all('tr')[1]
                            .td.find_all('p')[0]
                            .text
                        )
                        if '<t class=' in start_time:
                            start_time = findall(
                                r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                start_time,
                            )[0]
                        end_time = findall(
                            r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                            content_bs.find_all('tr')[1]
                            .td.find_all('p')[2]
                            .text,
                        )[0]
                        if '<t class=' in end_time:
                            end_time = findall(
                                r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>',
                                end_time,
                            )[0]

                        month_start, time_start = await get_month_and_time(
                            start_time
                        )
                        month_end, time_end = await get_month_and_time(
                            end_time
                        )

                        k['start_time'] = [month_start, time_start]
                        k['end_time'] = [month_end, time_end]

        if '冒险助力礼包' in k['title'] or '纪行' in k['title']:
            continue
        # if '角色试用' in k['title'] or '传说任务' in k['title']:
        #    event_data['other_event'].append(k)
        elif k['tag_label'] == '扭蛋':
            event_data['gacha_event'].append(k)
        elif k['tag_label'] == '活动':
            event_data['normal_event'].append(k)

    base_h = (
        450
        + len(event_data['normal_event']) * (270 + 10)
        + len(event_data['gacha_event']) * (370 + 10)
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

    for index, value in enumerate(event_data['normal_event']):
        event_img = Image.new(mode='RGBA', size=(950, 280))
        img = Image.open(BytesIO(get(value['banner']).content))
        img = img.resize((745, 270), Image.Resampling.LANCZOS)
        event_img.paste(img, (205, 10))
        event_img_draw = ImageDraw.Draw(event_img)

        if isinstance(value['start_time'], str):
            value['start_time'] = await get_month_and_time(value['start_time'])
        if isinstance(value['end_time'], str):
            value['end_time'] = await get_month_and_time(value['end_time'])
        event_img_draw.rectangle([(0, 0), (950, 10)], fill=event_color)
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

    for index, value in enumerate(event_data['gacha_event']):
        event_img = Image.new(mode='RGBA', size=(950, 380))
        img = Image.open(BytesIO(get(value['banner']).content))
        img = img.resize((745, 370), Image.Resampling.LANCZOS)
        event_img.paste(img, (205, 10))
        event_img_draw = ImageDraw.Draw(event_img)

        event_img_draw.rectangle([(0, 0), (950, 10)], fill=gacha_color)
        event_img_draw.rectangle([(8, 45), (58, 75)], fill=gacha_color)
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
            (0, 450 + len(event_data['normal_event']) * 280 + 380 * index),
            event_img,
        )

    base_img = base_img.convert('RGB')
    base_img.save(IMG_PATH, format='JPEG', subsampling=0, quality=90)
    return
