import json
import asyncio
from pathlib import Path
from typing import List, Tuple

from nonebot.log import logger
from PIL import Image, ImageDraw

from ..utils.mhy_api.get_mhy_data import get_daily_data
from ..utils.enka_api.get_enka_data import get_enka_info
from ..utils.message.error_reply import *  # noqa: F403,F401
from ..utils.alias.enName_to_avatarId import enName_to_avatarId
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_simple_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from ..utils.db_operation.db_operation import select_db, owner_cookies

TEXT_PATH = Path(__file__).parent / 'texture2D'
CHAR_SIDE_PATH = Path(__file__).parents[1] / 'resource' / 'char_side'

resin_fg_pic = Image.open(TEXT_PATH / 'resin_fg.png')
yes_pic = Image.open(TEXT_PATH / 'yes.png')
no_pic = Image.open(TEXT_PATH / 'no.png')

based_w = 500
based_h = 900
white_overlay = Image.new('RGBA', (based_w, based_h), (228, 222, 210, 222))

first_color = (29, 29, 29)
second_color = (98, 98, 98)
green_color = (15, 196, 35)
orange_color = (237, 115, 61)
red_color = (235, 61, 75)

gs_font_20 = genshin_font_origin(20)
gs_font_26 = genshin_font_origin(26)
gs_font_32 = genshin_font_origin(32)
gs_font_60 = genshin_font_origin(60)


async def _draw_task_img(
    img: Image.Image, img_draw: ImageDraw.ImageDraw, index: int, char: dict
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


async def get_resin_img(qid: int):
    try:
        uid_list: List = await select_db(qid, mode='list')  # type: ignore
        logger.info('[每日信息]UID: {}'.format(uid_list))
        # 进行校验UID是否绑定CK
        useable_uid_list = []
        for uid in uid_list:
            status = await owner_cookies(uid)
            if status != '该用户没有绑定过Cookies噢~':
                useable_uid_list.append(uid)
        logger.info('[每日信息]可用UID: {}'.format(uid_list))
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
        res = '查询不到该QQ号的UID信息,请联系管理员检查后台输出!'

    return res


async def _draw_all_resin_img(img: Image.Image, uid: str, index: int):
    resin_img = await draw_resin_img(uid)
    img.paste(resin_img, (500 * index, 0), resin_img)


async def draw_resin_img(uid: str) -> Image.Image:
    # 获取数据
    daily_data = await get_daily_data(uid)
    daily_data = daily_data['data']
    enta_data_path = (
        Path(__file__).parents[1] / 'player' / uid / 'rawData.json'
    )
    if enta_data_path.exists:
        with open(enta_data_path, 'r', encoding='utf-8') as f:
            player_data = json.load(f)
    else:
        player_data = await get_enka_info(uid)

    # 处理数据
    if player_data:
        if 'signature' in player_data['playerInfo']:
            signature = player_data['playerInfo']['signature']
        else:
            signature = '该旅行者还没有签名噢~'
        world_level = player_data['playerInfo']['level']
        world_level_str = f'探索等级{str(world_level)}'
    else:
        signature = '暂无获取数据'
        world_level_str = f'暂无数据'

    # 获取背景图片各项参数
    img = await get_simple_bg(based_w, based_h)
    img.paste(white_overlay, (0, 0), white_overlay)

    img.paste(resin_fg_pic, (0, 0), resin_fg_pic)

    # 树脂
    resin = daily_data['current_resin']
    max_resin = daily_data['max_resin']
    resin_str = f'{resin}/{max_resin}'
    resin_percent = resin / max_resin

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
    ring_pic.seek(round(resin_percent * 49))
    img.paste(ring_pic, (0, 0), ring_pic)

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
