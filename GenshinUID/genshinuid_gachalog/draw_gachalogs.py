import json
import random
import asyncio
import datetime
from pathlib import Path
from typing import List, Tuple, Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger

from ..utils.image.convert import convert_img
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, PLAYER_PATH, WEAPON_PATH
from ..utils.image.image_tools import (
    get_color_bg,
    get_qq_avatar,
    draw_pic_with_ring,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_28,
    gs_font_36,
    gs_font_40,
    gs_font_62,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'

up_tag = Image.open(TEXT_PATH / 'up.png')

first_color = (29, 29, 29)
brown_color = (41, 25, 0)
red_color = (255, 66, 66)
green_color = (74, 189, 119)

CHANGE_MAP = {'常驻祈愿': 'normal', '角色祈愿': 'char', '武器祈愿': 'weapon'}
HOMO_TAG = ['非到极致', '运气不好', '平稳保底', '小欧一把', '欧狗在此']
NORMAL_LIST = [
    '莫娜',
    '迪卢克',
    '七七',
    '琴',
    '阿莫斯之弓',
    '天空之翼',
    '四风原典',
    '天空之卷',
    '和璞鸢',
    '天空之脊',
    '狼的末路',
    '天空之傲',
    '风鹰剑',
    '天空之刃',
]

UP_LIST = {
    '刻晴': [(2022, 8, 24, 11, 0, 0), (2022, 9, 9, 17, 59, 59)],
    '提纳里': [(2022, 8, 24, 11, 0, 0), (2022, 9, 9, 17, 59, 59)],
    '迪希雅': [(2023, 3, 1, 11, 0, 0), (2023, 3, 21, 17, 59, 59)],
}


async def _draw_card(
    img: Image.Image,
    xy_point: Tuple[int, int],
    type: str,
    name: str,
    gacha_num: int,
    is_up: bool,
):
    card_img = Image.open(TEXT_PATH / 'item_bg.png')
    card_img_draw = ImageDraw.Draw(card_img)
    point = (1, 0)
    text_point = (55, 124)
    if type == '角色':
        _id = await name_to_avatar_id(name)
        item_pic = (
            Image.open(CHAR_PATH / f'{_id}.png')
            .convert('RGBA')
            .resize((108, 108))
        )
    else:
        item_pic = (
            Image.open(WEAPON_PATH / f'{name}.png')
            .convert('RGBA')
            .resize((108, 108))
        )
    card_img.paste(item_pic, point, item_pic)
    if gacha_num >= 81:
        text_color = red_color
    elif gacha_num <= 55:
        text_color = green_color
    else:
        text_color = brown_color
    card_img_draw.text(
        text_point, f'{gacha_num}抽', text_color, gs_font_24, 'mm'
    )
    if is_up:
        card_img.paste(up_tag, (47, -2), up_tag)
    img.paste(card_img, xy_point, card_img)


async def random_emo_pic(level: int) -> Image.Image:
    emo_fold = TEXT_PATH / str(level)
    return Image.open(random.choice(list(emo_fold.iterdir())))


async def get_level_from_list(ast: int, lst: List) -> int:
    if ast == 0:
        return 3

    for num_index, num in enumerate(lst):
        if ast <= num:
            level = 5 - num_index
            break
    else:
        level = 1
    return level


def check_up(name: str, _time: str) -> bool:
    for char in UP_LIST:
        if char == name:
            time = UP_LIST[char]
            s_time = datetime.datetime(*time[0])
            e_time = datetime.datetime(*time[1])
            gacha_time = datetime.datetime.strptime(_time, '%Y-%m-%d %H:%M:%S')
            if gacha_time < s_time or gacha_time > e_time:
                return False
            else:
                return True
    else:
        return False


async def draw_gachalogs_img(uid: str, user_id: str) -> Union[bytes, str]:
    path = PLAYER_PATH / str(uid) / 'gacha_logs.json'
    if not path.exists():
        return '你还没有祈愿数据噢~\n请添加Stoken后使用命令`刷新抽卡记录`更新祈愿数据~'
    with open(path, 'r', encoding='UTF-8') as f:
        gacha_data = json.load(f)

    # 数据初始化
    total_data = {}
    for i in ['常驻祈愿', '角色祈愿', '武器祈愿']:
        total_data[i] = {
            'total': 0,  # 五星总数
            'avg': 0,  # 抽卡平均数
            'avg_up': 0,  # up平均数
            'remain': 0,  # 已xx抽未出金
            'r_num': [],  # 不包含首位的抽卡数量
            'e_num': [],  # 包含首位的up抽卡数量
            'up_list': [],  # 抽到的UP列表(不包含首位)
            'normal_list': [],  # 抽到的五星列表(不包含首位)
            'list': [],  # 抽到的五星列表
            'time_range': '',  # 抽卡时间
            'all_time': 0,  # 抽卡总计秒数
            'type': '一般型',  # 抽卡类型: 随缘型, 氪金型, 规划型, 仓鼠型, 佛系型
            'short_gacha_data': {'time': 0, 'num': 0},
            'long_gacha_data': {'time': 0, 'num': 0},
        }
        # 拿到数据列表
        data_list = gacha_data['data'][i]
        # 初始化开关
        is_not_first = False
        # 开始初始化抽卡数
        num = 1
        # 从后面开始循环
        temp_time = datetime.datetime(2020, 9, 15, 18, 0, 0)
        for index, data in enumerate(data_list[::-1]):
            # 计算抽卡时间跨度
            if index == 0:
                total_data[i]['time_range'] = data['time']
            if index == len(data_list) - 1:
                total_data[i]['all_time'] = (
                    datetime.datetime.strptime(
                        data['time'], '%Y-%m-%d %H:%M:%S'
                    )
                    - datetime.datetime.strptime(
                        total_data[i]['time_range'], '%Y-%m-%d %H:%M:%S'
                    )
                ).total_seconds()
                total_data[i]['time_range'] += '~' + data['time']

            # 计算时间间隔
            if index != 0:
                now_time = datetime.datetime.strptime(
                    data['time'], '%Y-%m-%d %H:%M:%S'
                )
                dis = (now_time - temp_time).total_seconds()
                temp_time = now_time
                if dis <= 5000:
                    total_data[i]['short_gacha_data']['num'] += 1
                    total_data[i]['short_gacha_data']['time'] += dis
                elif dis >= 86400:
                    total_data[i]['long_gacha_data']['num'] += 1
                    total_data[i]['long_gacha_data']['time'] += dis
            else:
                temp_time = datetime.datetime.strptime(
                    data['time'], '%Y-%m-%d %H:%M:%S'
                )

            # 如果这是个五星
            if data['rank_type'] == '5':
                # 抽到这个五星花了多少抽
                data['gacha_num'] = num

                # 判断是否是UP
                if data['name'] in NORMAL_LIST:
                    data['is_up'] = False
                elif data['name'] in UP_LIST:
                    data['is_up'] = check_up(data['name'], data['time'])
                else:
                    data['is_up'] = True

                # 往里加东西
                if is_not_first:
                    total_data[i]['r_num'].append(num)
                    total_data[i]['normal_list'].append(data)
                    if data['is_up']:
                        total_data[i]['up_list'].append(data)

                # 把这个数据扔到抽到的五星列表内
                total_data[i]['list'].append(data)

                # 判断经过了第一个
                if total_data[i]['list']:
                    is_not_first = True

                num = 1
                # 五星总数增加1
                total_data[i]['total'] += 1
            else:
                num += 1

        # 计算已多少抽
        total_data[i]['remain'] = num - 1

        # 计算平均抽卡数
        if len(total_data[i]['normal_list']) == 0:
            total_data[i]['avg'] = 0
        else:
            total_data[i]['avg'] = float(
                '{:.2f}'.format(
                    sum(total_data[i]['r_num']) / len(total_data[i]['r_num'])
                )
            )
        # 计算平均up数量
        if len(total_data[i]['up_list']) == 0:
            total_data[i]['avg_up'] = 0
        else:
            total_data[i]['avg_up'] = float(
                '{:.2f}'.format(
                    sum(total_data[i]['r_num']) / len(total_data[i]['up_list'])
                )
            )

        # 计算抽卡类型
        # 如果抽卡总数小于40
        if gacha_data[f'{CHANGE_MAP[i]}_gacha_num'] <= 40:
            total_data[i]['type'] = '佛系型'
        # 如果长时抽卡总数占据了总抽卡数的70%
        elif (
            total_data[i]['long_gacha_data']['num']
            / gacha_data[f'{CHANGE_MAP[i]}_gacha_num']
            >= 0.7
        ):
            total_data[i]['type'] = '随缘型'
        # 如果短时抽卡总数占据了总抽卡数的70%
        elif (
            total_data[i]['short_gacha_data']['num']
            / gacha_data[f'{CHANGE_MAP[i]}_gacha_num']
            >= 0.7
        ):
            total_data[i]['type'] = '规划型'
        # 如果抽卡数量远远大于标称抽卡数量
        elif (
            total_data[i]['all_time'] / 30000
            <= gacha_data[f'{CHANGE_MAP[i]}_gacha_num']
        ):
            # 如果长时抽卡数量大于短时抽卡数量
            if (
                total_data[i]['long_gacha_data']['num']
                >= total_data[i]['short_gacha_data']['num']
            ):
                total_data[i]['type'] = '规划型'
            else:
                total_data[i]['type'] = '氪金型'
        # 如果抽卡数量远远小于标称抽卡数量
        elif (
            total_data[i]['all_time'] / 32000
            >= gacha_data[f'{CHANGE_MAP[i]}_gacha_num'] * 2
        ):
            total_data[i]['type'] = '仓鼠型'

    # 常量偏移数据
    single_y = 150

    # 计算图片尺寸
    normal_y = (1 + ((total_data['常驻祈愿']['total'] - 1) // 6)) * single_y
    char_y = (1 + ((total_data['角色祈愿']['total'] - 1) // 6)) * single_y
    weapon_y = (1 + ((total_data['武器祈愿']['total'] - 1) // 6)) * single_y

    # 获取背景图片各项参数
    _id = str(user_id)
    if _id.startswith('http'):
        char_pic = await get_qq_avatar(avatar_url=_id)
    else:
        char_pic = await get_qq_avatar(qid=user_id)
    char_pic = await draw_pic_with_ring(char_pic, 320)

    avatar_title = Image.open(TEXT_PATH / 'avatar_title.png')
    img = await get_color_bg(950, 530 + 900 + normal_y + char_y + weapon_y)
    img.paste(avatar_title, (0, 0), avatar_title)
    img.paste(char_pic, (318, 83), char_pic)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((475, 454), f'UID {uid}', first_color, gs_font_36, 'mm')

    # 处理title
    # {'total': 0, 'avg': 0, 'remain': 0, 'list': []}
    type_list = ['常驻祈愿', '角色祈愿', '武器祈愿']
    y_extend = 0
    level = 3
    for index, i in enumerate(type_list):
        title = Image.open(TEXT_PATH / 'gahca_title.png')
        if i == '常驻祈愿':
            level = await get_level_from_list(
                total_data[i]['avg'], [54, 61, 67, 73, 80]
            )
        else:
            if i == '武器祈愿':
                level = await get_level_from_list(
                    total_data[i]['avg_up'], [62, 75, 88, 99, 111]
                )
            else:
                level = await get_level_from_list(
                    total_data[i]['avg_up'], [74, 87, 99, 105, 120]
                )

        emo_pic = await random_emo_pic(level)
        emo_pic = emo_pic.resize((154, 154))
        title.paste(emo_pic, (703, 28), emo_pic)
        title_draw = ImageDraw.Draw(title)
        # 欧非描述
        title_draw.text(
            (778, 207), HOMO_TAG[level - 1], first_color, gs_font_36, 'mm'
        )
        # 卡池
        title_draw.text((69, 72), i, first_color, gs_font_62, 'lm')
        # 抽卡时间
        if total_data[i]['time_range']:
            time_range = total_data[i]['time_range']
        else:
            time_range = '暂未抽过卡!'
        title_draw.text((68, 122), time_range, brown_color, gs_font_28, 'lm')
        # 平均抽卡数量
        title_draw.text(
            (123, 176),
            str(total_data[i]['avg']),
            first_color,
            gs_font_40,
            'mm',
        )
        # 平均up
        title_draw.text(
            (272, 176),
            str(total_data[i]['avg_up']),
            first_color,
            gs_font_40,
            'mm',
        )
        # 抽卡总数
        title_draw.text(
            (424, 176),
            str(gacha_data[f'{CHANGE_MAP[i]}_gacha_num']),
            first_color,
            gs_font_40,
            'mm',
        )
        # 抽卡类型
        title_draw.text(
            (585, 176),
            str(total_data[i]['type']),
            first_color,
            gs_font_40,
            'mm',
        )
        # 已抽数
        title_draw.text(
            (383, 85),
            str(total_data[i]['remain']),
            red_color,
            gs_font_28,
            'mm',
        )
        y_extend += (
            (1 + ((total_data[type_list[index - 1]]['total'] - 1) // 6)) * 150
            if index != 0
            else 0
        )
        y = 540 + index * 300 + y_extend
        img.paste(title, (0, y), title)
        tasks = []
        for item_index, item in enumerate(total_data[i]['list']):
            item_x = (item_index % 6) * 138 + 60
            item_y = (item_index // 6) * 150 + y + 275
            xy_point = (item_x, item_y)
            tasks.append(
                _draw_card(
                    img,
                    xy_point,
                    item['item_type'],
                    item['name'],
                    item['gacha_num'],
                    item['is_up'],
                )
            )
        await asyncio.gather(*tasks)
        tasks.clear()

    # 发送图片
    res = await convert_img(img)
    logger.info('[查询抽卡]绘图已完成,等待发送!')
    return res
