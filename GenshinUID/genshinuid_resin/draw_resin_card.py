import json
import asyncio
from typing import List
from pathlib import Path

from PIL import Image, ImageDraw
from gsuid_core.logger import logger
from gsuid_core.utils.api.mys.models import Expedition

from ..utils.mys_api import mys_api
from ..utils.database import get_sqla
from ..utils.image.convert import convert_img
from ..genshinuid_enka.to_data import get_enka_info
from ..utils.image.image_tools import get_simple_bg
from ..utils.map.name_covert import enName_to_avatarId
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH, CHAR_SIDE_PATH
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_26,
    gs_font_32,
    gs_font_60,
)

TEXT_PATH = Path(__file__).parent / 'texture2D'

resin_fg_pic = Image.open(TEXT_PATH / 'resin_fg.png')
yes_pic = Image.open(TEXT_PATH / 'yes.png')
no_pic = Image.open(TEXT_PATH / 'no.png')
warn_pic = Image.open(TEXT_PATH / 'warn.png')

based_w = 500
based_h = 900
white_overlay = Image.new('RGBA', (based_w, based_h), (255, 251, 242, 225))

first_color = (29, 29, 29)
second_color = (98, 98, 98)
green_color = (15, 196, 35)
orange_color = (237, 115, 61)
red_color = (235, 61, 75)


async def _draw_task_img(
    img: Image.Image,
    img_draw: ImageDraw.ImageDraw,
    index: int,
    char: Expedition,
):
    char_en_name = char['avatar_side_icon'].split('_')[-1].split('.')[0]
    avatar_id = await enName_to_avatarId(char_en_name)
    char_pic = (
        Image.open(CHAR_SIDE_PATH / f'{avatar_id}.png')
        .convert('RGBA')
        .resize((80, 80), Image.Resampling.LANCZOS)  # type: ignore
    )
    img.paste(char_pic, (22 + index * 90, 770), char_pic)
    if char['status'] == 'Finished':
        status_mark = '待收取'
        status_color = red_color
    else:
        status_mark = '已派遣'
        status_color = green_color
    img_draw.text(
        (65 + index * 90, 870),
        status_mark,
        font=gs_font_20,
        fill=status_color,
        anchor='mm',
    )


async def get_resin_img(bot_id: str, user_id: str):
    try:
        sqla = get_sqla(bot_id)
        uid_list: List = await sqla.get_bind_uid_list(user_id)
        logger.info('[每日信息]UID: {}'.format(uid_list))
        # 进行校验UID是否绑定CK
        useable_uid_list = []
        for uid in uid_list:
            status = await sqla.get_user_cookie(uid)
            if status is not None:
                useable_uid_list.append(uid)
        logger.info('[每日信息]可用UID: {}'.format(useable_uid_list))
        if len(useable_uid_list) == 0:
            return '请先绑定一个可用CK & UID再来查询哦~'
        # 开始绘图任务
        task = []
        img = Image.new(
            'RGBA', (based_w * len(useable_uid_list), based_h), (0, 0, 0, 0)
        )
        for uid_index, uid in enumerate(useable_uid_list):
            task.append(_draw_all_resin_img(img, uid, uid_index))
        await asyncio.gather(*task)
        res = await convert_img(img)
        logger.info('[查询每日信息]绘图已完成,等待发送!')
    except TypeError:
        logger.exception('[查询每日信息]绘图失败!')
        res = '你绑定过的UID中可能存在过期CK~请重新绑定一下噢~'

    return res


async def _draw_all_resin_img(img: Image.Image, uid: str, index: int):
    resin_img = await draw_resin_img(uid)
    img.paste(resin_img, (500 * index, 0), resin_img)


async def seconds2hours(seconds: int) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return '%02d小时%02d分' % (h, m)


async def draw_resin_img(uid: str) -> Image.Image:
    # 获取数据
    daily_data = await mys_api.get_daily_data(uid)

    # 获取背景图片各项参数
    img = await get_simple_bg(based_w, based_h)
    img.paste(white_overlay, (0, 0), white_overlay)

    if isinstance(daily_data, int):
        img_draw = ImageDraw.Draw(img)
        img.paste(warn_pic, (0, 0), warn_pic)
        # 写UID
        img_draw.text(
            (250, 553),
            f'UID{uid}',
            font=gs_font_26,
            fill=first_color,
            anchor='mm',
        )
        img_draw.text(
            (250, 518),
            f'错误码 {daily_data}',
            font=gs_font_26,
            fill=red_color,
            anchor='mm',
        )
        return img

    enta_data_path = PLAYER_PATH / uid / 'rawData.json'
    if enta_data_path.exists():
        with open(enta_data_path, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
    else:
        try:
            player_data = await get_enka_info(uid)
        except Exception:
            player_data = {}

    # 处理数据
    if player_data and 'playerInfo' in player_data:
        if 'signature' in player_data['playerInfo']:
            signature = player_data['playerInfo']['signature']
        else:
            signature = '该旅行者还没有签名噢~'
        world_level = player_data['playerInfo']['level']
        world_level_str = f'探索等级{str(world_level)}'
    else:
        signature = '暂无获取数据'
        world_level_str = '暂无数据'

    img.paste(resin_fg_pic, (0, 0), resin_fg_pic)

    # 树脂
    resin = daily_data['current_resin']
    max_resin = daily_data['max_resin']
    resin_str = f'{resin}/{max_resin}'
    resin_percent = resin / max_resin
    if resin_percent > 0.8:
        resin_color = red_color
    else:
        resin_color = second_color
    resin_recovery_time = await seconds2hours(
        daily_data['resin_recovery_time']
    )

    delay = 53
    # 洞天宝钱
    home_coin = daily_data['current_home_coin']
    max_home_coin = daily_data['max_home_coin']
    home_coin_str = f'{home_coin}/{max_home_coin}'
    if max_home_coin - home_coin < 200:
        home_coin_mark = '可收取'
        home_coin_color = red_color
        img.paste(no_pic, (35, 559), no_pic)
    else:
        home_coin_mark = '已收取'
        home_coin_color = green_color
        img.paste(yes_pic, (35, 559), yes_pic)
    # 完成委托
    finish_task = daily_data['finished_task_num']
    total_task = daily_data['total_task_num']
    is_task_reward = daily_data['is_extra_task_reward_received']
    task_str = f'{finish_task}/{total_task}'
    if is_task_reward:
        task_mark = '已领取'
        task_color = green_color
        img.paste(yes_pic, (35, 559 + delay), yes_pic)
    else:
        task_mark = '未领取'
        task_color = red_color
        img.paste(no_pic, (35, 559 + delay), no_pic)
    # 周本减半
    weekly_half = daily_data['remain_resin_discount_num']
    max_weekly_half = daily_data['resin_discount_num_limit']
    weekly_half_str = f'{weekly_half}/{max_weekly_half}'
    if weekly_half == 0:
        weekly_half_mark = '已使用'
        weekly_half_color = green_color
        img.paste(yes_pic, (35, 559 + delay * 2), yes_pic)
    else:
        weekly_half_mark = '未用完'
        weekly_half_color = red_color
        img.paste(no_pic, (35, 559 + delay * 2), no_pic)
    # 参量质变仪
    transformer = daily_data['transformer']['recovery_time']['reached']
    transformer_day = daily_data['transformer']['recovery_time']['Day']
    transformer_hour = daily_data['transformer']['recovery_time']['Hour']
    transformer_str = f'还剩{transformer_day}天{transformer_hour}小时'
    if transformer:
        transformer_mark = '可使用'
        transformer_color = red_color
        img.paste(no_pic, (35, 559 + delay * 3), no_pic)
    else:
        transformer_mark = '已使用'
        transformer_color = green_color
        img.paste(yes_pic, (35, 559 + delay * 3), yes_pic)

    img_draw = ImageDraw.Draw(img)

    # 派遣
    task_task = []
    for index, char in enumerate(daily_data['expeditions']):
        task_task.append(_draw_task_img(img, img_draw, index, char))
    await asyncio.gather(*task_task)

    # 绘制树脂圆环
    ring_pic = Image.open(TEXT_PATH / 'ring.apng')
    percent = (
        round(resin_percent * 49) if round(resin_percent * 49) <= 49 else 49
    )
    ring_pic.seek(percent)
    img.paste(ring_pic, (0, 0), ring_pic)

    # 写树脂剩余时间
    img_draw.text(
        (250, 370),
        f'还剩{resin_recovery_time}',
        font=gs_font_20,
        fill=resin_color,
        anchor='mm',
    )
    # 写签名
    img_draw.text(
        (48, 137), signature, font=gs_font_26, fill=second_color, anchor='lm'
    )
    # 写UID
    img_draw.text(
        (250, 518), f'UID{uid}', font=gs_font_26, fill=first_color, anchor='mm'
    )
    # 写探索等级
    img_draw.text(
        (250, 281),
        world_level_str,
        font=gs_font_26,
        fill=second_color,
        anchor='mm',
    )
    # 写树脂
    img_draw.text(
        (250, 327),
        resin_str,
        font=gs_font_60,
        fill=first_color,
        anchor='mm',
    )
    # 写洞天宝钱
    img_draw.text(
        (335, 588),
        home_coin_str,
        font=gs_font_20,
        fill=first_color,
        anchor='lm',
    )
    img_draw.text(
        (225, 584),
        home_coin_mark,
        font=gs_font_32,
        fill=home_coin_color,
        anchor='lm',
    )
    # 写完成委托
    img_draw.text(
        (335, 588 + delay),
        task_str,
        font=gs_font_20,
        fill=first_color,
        anchor='lm',
    )
    img_draw.text(
        (225, 584 + delay),
        task_mark,
        font=gs_font_32,
        fill=task_color,
        anchor='lm',
    )
    # 写周本减半
    img_draw.text(
        (335, 588 + delay * 2),
        weekly_half_str,
        font=gs_font_20,
        fill=first_color,
        anchor='lm',
    )
    img_draw.text(
        (225, 584 + delay * 2),
        weekly_half_mark,
        font=gs_font_32,
        fill=weekly_half_color,
        anchor='lm',
    )
    # 写参量质变仪
    img_draw.text(
        (335, 588 + delay * 3),
        transformer_str,
        font=gs_font_20,
        fill=first_color,
        anchor='lm',
    )
    img_draw.text(
        (225, 584 + delay * 3),
        transformer_mark,
        font=gs_font_32,
        fill=transformer_color,
        anchor='lm',
    )

    return img
