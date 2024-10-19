import time
import asyncio
from pathlib import Path
from typing import Union, Optional

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.api.mys.models import AbyssBattleAvatar

from ..utils.mys_api import mys_api
from ..utils.image.convert import convert_img
from ..utils.resource.download_url import download_file
from ..utils.resource.generate_char_card import create_single_char_card
from ..utils.resource.RESOURCE_PATH import CHAR_CARD_PATH, CHAR_SIDE_PATH
from ..utils.image.image_tools import (
    get_avatar,
    get_color_bg,
    get_talent_pic,
    draw_pic_with_ring,
)
from ..utils.colors import (
    red_color,
    sec_color,
    blue_color,
    gray_color,
    first_color,
    white_color,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_22,
    gs_font_26,
    gs_font_32,
    gs_font_36,
    gs_font_40,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'


async def get_abyss_star_pic(star: int) -> Image.Image:
    star_pic = Image.open(TEXT_PATH / f'star{star}.png')
    return star_pic


async def _draw_abyss_card(
    char: AbyssBattleAvatar,
    talent_num: str,
    floor_pic: Image.Image,
    index_char: int,
    index_part: int,
):
    char_id = char['id']
    # 确认角色头像路径
    char_pic_path = CHAR_CARD_PATH / f'{char_id}.png'
    # 不存在自动下载
    if not char_pic_path.exists():
        await create_single_char_card(char_id)
    char_card = Image.open(char_pic_path).convert('RGBA')
    talent_pic = await get_talent_pic(int(talent_num))
    talent_pic = talent_pic.resize((90, 45))
    char_card.paste(talent_pic, (137, 260), talent_pic)
    char_card_draw = ImageDraw.Draw(char_card)
    char_card_draw.text(
        (77, 280),
        f'Lv.{char["level"]}',
        font=gs_font_40,
        fill=first_color,
        anchor='mm',
    )
    char_card = char_card.resize((128, 160), Image.Resampling.LANCZOS)
    floor_pic.paste(
        char_card,
        (70 + 147 * index_char, 39 + index_part * 170),
        char_card,
    )


async def _draw_floor_card(
    level_star: int,
    floor_pic: Image.Image,
    img: Image.Image,
    time_str: str,
    index_floor: int,
    floor_num: int,
):
    star_pic = await get_abyss_star_pic(level_star)
    floor_pic.paste(star_pic, (690, 170), star_pic)
    floor_pic_draw = ImageDraw.Draw(floor_pic)
    time_list = time_str.split(' ')
    floor_pic_draw.text(
        (652, 71),
        f'第{floor_num}层第{index_floor+1}间',
        font=gs_font_32,
        fill=first_color,
        anchor='lm',
    )
    for index, _time in enumerate(time_list):
        floor_pic_draw.text(
            (655, 102 + index * 22),
            _time,
            font=gs_font_22,
            fill=first_color,
            anchor='lm',
        )
    img.paste(floor_pic, (0, 818 + index_floor * 391), floor_pic)


async def draw_abyss_img(
    ev: Event,
    uid: str,
    floor: Optional[int] = None,
    schedule_type: str = '1',
) -> Union[bytes, str]:
    raw_abyss_data = await mys_api.get_spiral_abyss_info(uid, schedule_type)
    raw_data = await mys_api.get_info(uid)

    # 获取数据
    if isinstance(raw_abyss_data, int):
        return await get_error_img(raw_abyss_data)
    if isinstance(raw_data, int):
        return await get_error_img(raw_data)

    if raw_data:
        char_data = raw_data['avatars']
    else:
        return '没有获取到角色数据'
    char_temp = {}

    # 获取查询者数据
    if floor:
        if floor < 9:
            return '楼层不能小于9层!'
        for _floor_data in raw_abyss_data['floors']:
            if floor == _floor_data['index']:
                floors_data = _floor_data
                break
        else:
            if (
                raw_abyss_data['floors']
                and floor < raw_abyss_data['floors'][0]['index']
            ):
                return '你本期已跳过该层深渊!'
            else:
                return '你还没有挑战过该层深渊!'
    else:
        if len(raw_abyss_data['floors']) == 0:
            return '你还没有挑战本期深渊!\n可以使用[上期深渊]命令查询上期~'
        floors_data = raw_abyss_data['floors'][-1]

    if floors_data['levels'][-1]['battles']:
        is_unfull = False
    else:
        is_unfull = True

    # 获取背景图片各项参数
    based_w = 950
    based_h = 900 if is_unfull else 2000
    img = await get_color_bg(based_w, based_h, '_abyss')
    abyss_title = Image.open(TEXT_PATH / 'abyss_title.png')
    img.paste(abyss_title, (0, 0), abyss_title)

    # 获取头像
    char_pic = await get_avatar(ev, 320)
    char_pic = await draw_pic_with_ring(char_pic, 320)

    img.paste(char_pic, (320, 50), char_pic)

    # 解析数据
    damage_rank = raw_abyss_data['damage_rank']
    defeat_rank = raw_abyss_data['defeat_rank']
    take_damage_rank = raw_abyss_data['take_damage_rank']
    # normal_skill_rank = raw_abyss_data['normal_skill_rank']
    energy_skill_rank = raw_abyss_data['energy_skill_rank']
    # 挑战次数 raw_abyss_data['total_battle_times']

    # 绘制抬头
    img_draw = ImageDraw.Draw(img)
    img_draw.text((475, 469), f'UID {uid}', first_color, gs_font_36, 'mm')
    img_draw.text(
        (475, 413),
        f'挑战次数 - {raw_abyss_data["total_battle_times"]}',
        first_color,
        gs_font_26,
        'mm',
    )
    title_data = {
        '最强一击!': damage_rank[0],
        '最多击破!': defeat_rank[0],
        '承受伤害': take_damage_rank[0],
        '元素爆发': energy_skill_rank[0],
    }
    for _index, _name in enumerate(title_data):
        _char = title_data[_name]
        _char_id = _char['avatar_id']
        char_side_path = CHAR_SIDE_PATH / f'{_char_id}.png'
        if not char_side_path.exists():
            await download_file(_char['avatar_icon'], 3, f'{_char_id}.png')
        char_side = Image.open(char_side_path)
        char_side = char_side.resize((75, 75))
        intent = _index * 224
        title_xy = (115 + intent, 523)
        val_xy = (115 + intent, 545)
        _val = str(_char['value'])
        img.paste(char_side, (43 + intent, 484), char_side)
        img_draw.text(title_xy, _name, first_color, gs_font_20, 'lm')
        img_draw.text(val_xy, _val, first_color, gs_font_26, 'lm')

    # 过滤数据
    raw_abyss_data['floors'] = [
        i for i in raw_abyss_data['floors'] if i['index'] >= 9
    ]

    if raw_abyss_data['floors'] and raw_abyss_data['floors'][0]:
        base = raw_abyss_data['floors'][0]['index']

    for _i in range(base - 9):
        raw_abyss_data['floors'].insert(
            0,
            {
                'index': _i + 9,
                'levels': [],
                'is_unlock': True,
                'star': 9,
                'max_star': 9,
                'settle_time': '0000-00-00 00:00:00',
                'icon': '',
            },
        )

    # 绘制缩略信息
    for num in range(4):
        omit_bg = Image.open(TEXT_PATH / 'abyss_omit.png')
        omit_draw = ImageDraw.Draw(omit_bg)
        omit_draw.text((56, 34), f'第{num+9}层', first_color, gs_font_32, 'lm')
        omit_draw.rounded_rectangle((165, 19, 225, 49), 20, red_color)
        if len(raw_abyss_data['floors']) - 1 >= num:
            _floor = raw_abyss_data['floors'][num]
            if _floor['settle_time'] == '0000-00-00 00:00:00':
                _color = red_color
                _text = '已跳过'
            elif _floor['star'] == _floor['max_star']:
                _color = red_color
                _text = '全满星'
            else:
                _gap = _floor['max_star'] - _floor['star']
                _color = blue_color
                _text = f'差{_gap}颗'

            if _floor['settle_time'] == '0000-00-00 00:00:00':
                _time_str = '跳过楼层不存在时间顺序!'
            elif not is_unfull:
                _timestamp = int(
                    _floor['levels'][-1]['battles'][-1]['timestamp']
                )
                _time_array = time.localtime(_timestamp)
                _time_str = time.strftime('%Y-%m-%d %H:%M:%S', _time_array)
            else:
                _time_str = '请挑战后查看时间数据!'
        else:
            _color = gray_color
            _text = '未解锁'
            _time_str = '请挑战后查看时间数据!'
        omit_draw.rounded_rectangle((165, 19, 255, 49), 20, _color)
        omit_draw.text((210, 34), _text, white_color, gs_font_26, 'mm')
        omit_draw.text((54, 65), _time_str, sec_color, gs_font_22, 'lm')
        pos = (20 + 459 * (num % 2), 613 + 106 * (num // 2))
        img.paste(omit_bg, pos, omit_bg)

    if is_unfull:
        hint = Image.open(TEXT_PATH / 'hint.png')
        img.paste(hint, (0, 830), hint)
    else:
        task = []
        floor_num = floors_data['index']
        for index_floor, level in enumerate(floors_data['levels']):
            floor_pic = Image.open(TEXT_PATH / 'abyss_floor.png')
            level_star = level['star']
            timestamp = int(level['battles'][0]['timestamp'])
            time_array = time.localtime(timestamp)
            time_str = time.strftime('%Y-%m-%d %H:%M:%S', time_array)
            for index_part, battle in enumerate(level['battles']):
                for index_char, char in enumerate(battle['avatars']):
                    # 获取命座
                    if char["id"] in char_temp:
                        talent_num = char_temp[char["id"]]
                    else:
                        for i in char_data:
                            if i["id"] == char["id"]:
                                talent_num = str(
                                    i["actived_constellation_num"]
                                )
                                char_temp[char["id"]] = talent_num
                                break
                    task.append(
                        _draw_abyss_card(
                            char,
                            talent_num,  # type: ignore
                            floor_pic,
                            index_char,
                            index_part,
                        )
                    )
            await asyncio.gather(*task)
            task.clear()
            task.append(
                _draw_floor_card(
                    level_star,
                    floor_pic,
                    img,
                    time_str,
                    index_floor,
                    floor_num,
                )
            )
        await asyncio.gather(*task)

    res = await convert_img(img)
    logger.info('[查询深渊信息]绘图已完成,等待发送!')
    return res
