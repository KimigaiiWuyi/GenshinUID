from io import BytesIO
from re import findall
from pathlib import Path
from typing import List, Literal

from httpx import get
from PIL import Image, ImageDraw
from gsuid_core.utils.api.ambr.request import get_ambr_event_info

from ..version import Genshin_version
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import get_color_bg
from ..utils.fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'
EVENT_IMG_PATH = Path(__file__).parent / 'event.jpg'
GACHA_IMG_PATH = Path(__file__).parent / 'gacha.jpg'

PATTERN = r'<[a-zA-Z]+.*?>([\s\S]*?)</[a-zA-Z]*?>'

text_color = (60, 59, 64)


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


class DrawEventList:
    def __init__(self):
        self.gacha_event: List = []
        self.normal_event: List = []
        self.other_event: List = []

    async def get_event_data(self):
        event_list = await get_ambr_event_info()
        assert event_list is not None
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

            event_data['full_name'] = event_list[event]['nameFull']['CHS']
            event_data['start_time'] = await get_month_and_time(start_time)
            event_data['end_time'] = await get_month_and_time(end_time)
            if '祈愿' in name_full or '扭蛋' in name_full:
                self.gacha_event.append(event_data)
            else:
                self.normal_event.append(event_data)

    async def get_and_save_event_img(self):
        base_h = 100 + len(self.normal_event) * 380
        base_img = await get_color_bg(950, base_h)

        font_l = genshin_font_origin(62)
        # font_m = genshin_font_origin(34)
        font_s = genshin_font_origin(26)

        # now_time = datetime.now().strftime('%Y/%m/%d')
        event_cover = Image.open(TEXT_PATH / 'normal_event_cover.png')

        for index, value in enumerate(self.normal_event):
            event_img = Image.open(TEXT_PATH / 'normal_event_bg.png')
            banner_img = Image.open(BytesIO(get(value['banner']).content))
            banner_img = banner_img.resize(
                (576, 208), Image.Resampling.LANCZOS
            )
            event_img.paste(banner_img, (315, 118))
            event_img_draw = ImageDraw.Draw(event_img)

            # 写标题
            event_img_draw.text(
                (475, 47), value['full_name'], text_color, font_s, 'mm'
            )
            # 纠错
            if isinstance(value['start_time'], str):
                value['start_time'] = await get_month_and_time(
                    value['start_time']
                )
            if isinstance(value['end_time'], str):
                value['end_time'] = await get_month_and_time(value['end_time'])

            # 画三角
            event_img_draw.polygon(
                [(98, 211), (98, 237), (121, 224)], fill=(243, 110, 110)
            )

            # 写字
            event_img_draw.text(
                (74, 149),
                value['start_time'][0],
                text_color,
                font_l,
                anchor='lm',
            )
            event_img_draw.text(
                (74, 191),
                value['start_time'][1],
                text_color,
                font_s,
                anchor='lm',
            )
            event_img_draw.text(
                (115, 275),
                value['end_time'][0],
                text_color,
                font_l,
                anchor='lm',
            )
            event_img_draw.text(
                (115, 318),
                value['end_time'][1],
                text_color,
                font_s,
                anchor='lm',
            )
            event_img.paste(event_cover, (0, 0), event_cover)
            base_img.paste(event_img, (0, 50 + 380 * index), event_img)

        base_img = base_img.convert('RGB')
        base_img.save(EVENT_IMG_PATH, format='JPEG', subsampling=0, quality=90)
        base_img = await convert_img(base_img)
        if isinstance(base_img, bytes):
            return base_img
        else:
            return bytes(base_img, 'utf8')

    async def get_and_save_gacha_img(self):
        base_h = 100 + len(self.gacha_event) * 480
        base_img = await get_color_bg(950, base_h)

        font_l = genshin_font_origin(62)
        # font_m = genshin_font_origin(34)
        font_s = genshin_font_origin(26)

        # now_time = datetime.now().strftime('%Y/%m/%d')
        gacha_cover = Image.open(TEXT_PATH / 'gacha_event_cover.png')

        for index, value in enumerate(self.gacha_event):
            gacha_img = Image.open(TEXT_PATH / 'gacha_event_bg.png')
            banner_img = Image.open(BytesIO(get(value['banner']).content))
            banner_img = banner_img.resize(
                (576, 284), Image.Resampling.LANCZOS
            )
            gacha_img.paste(banner_img, (315, 130))
            gacha_img_draw = ImageDraw.Draw(gacha_img)

            # 写标题
            gacha_img_draw.text(
                (475, 47), value['full_name'], text_color, font_s, 'mm'
            )
            # 纠错
            if isinstance(value['start_time'], str):
                value['start_time'] = await get_month_and_time(
                    value['start_time']
                )
            if isinstance(value['end_time'], str):
                value['end_time'] = await get_month_and_time(value['end_time'])

            # 画三角
            gacha_img_draw.polygon(
                [(98, 261), (98, 287), (121, 274)], fill=(243, 110, 110)
            )

            # 写字
            gacha_img_draw.text(
                (74, 199),
                value['start_time'][0],
                text_color,
                font_l,
                anchor='lm',
            )
            gacha_img_draw.text(
                (74, 241),
                value['start_time'][1],
                text_color,
                font_s,
                anchor='lm',
            )
            gacha_img_draw.text(
                (115, 325),
                value['end_time'][0],
                text_color,
                font_l,
                anchor='lm',
            )
            gacha_img_draw.text(
                (115, 368),
                value['end_time'][1],
                text_color,
                font_s,
                anchor='lm',
            )
            gacha_img.paste(gacha_cover, (0, 0), gacha_cover)
            base_img.paste(gacha_img, (0, 50 + 480 * index), gacha_img)

        base_img = base_img.convert('RGB')
        base_img.save(GACHA_IMG_PATH, format='JPEG', subsampling=0, quality=90)
        base_img = await convert_img(base_img)
        if isinstance(base_img, bytes):
            return base_img
        else:
            return bytes(base_img, 'utf8')


async def get_all_event_img():
    event_list = DrawEventList()
    await event_list.get_event_data()
    await event_list.get_and_save_event_img()
    await event_list.get_and_save_gacha_img()


async def get_event_img(event_type: Literal['EVENT', 'GACHA']) -> bytes:
    if event_type == 'EVENT':
        if EVENT_IMG_PATH.exists():
            with open(EVENT_IMG_PATH, 'rb') as f:
                return f.read()
    else:
        if GACHA_IMG_PATH.exists():
            with open(GACHA_IMG_PATH, 'rb') as f:
                return f.read()

    event_list = DrawEventList()
    await event_list.get_event_data()
    if event_type == 'EVENT':
        return await event_list.get_and_save_event_img()
    else:
        return await event_list.get_and_save_gacha_img()
