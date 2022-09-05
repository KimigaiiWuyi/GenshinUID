import asyncio
from pathlib import Path
from typing import Union

from nonebot.log import logger
from PIL import Image, ImageDraw

from .set_config import SWITCH_MAP
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import CustomizeImage
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from ..utils.db_operation.db_operation import (
    get_all_uid,
    config_check,
    get_all_cookie,
    get_all_stoken,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'
config_title = Image.open(TEXT_PATH / 'config_title.png')
config_on = Image.open(TEXT_PATH / 'config_on.png')
config_off = Image.open(TEXT_PATH / 'config_off.png')

gs_font_36 = genshin_font_origin(36)
gs_font_40 = genshin_font_origin(40)
gs_font_24 = genshin_font_origin(24)

first_color = (20, 20, 20)
second_color = (57, 57, 57)

DETAIL_MAP = {
    '米游币推送': '开启后会私聊每个用户当前米游币任务完成情况',
    '简洁签到报告': '开启后可以大大减少每日签到报告字数 ',
    '私聊报告': '关闭后将不再给主人推送当天米游币任务完成情况',
    '随机图': '开启后[查询心海]等命令展示图将替换为随机图片',
    '定时签到': '开启后每晚00:30将开始自动签到任务',
    '定时米游币': '开启后每晚01:16将开始自动米游币任务',
    '催命模式': '开启后当达到推送阈值将会一直推送',
}


async def draw_config_img() -> Union[bytes, str]:
    # 获取背景图片各项参数
    based_w = 850
    based_h = 850 + 155 * (len(SWITCH_MAP) - 3)

    CI_img = CustomizeImage('', based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    color_mask = Image.new('RGBA', (based_w, based_h), color)
    config_mask = Image.open(TEXT_PATH / 'config_mask.png').resize(
        (based_w, based_h)
    )
    img.paste(color_mask, (0, 0), config_mask)
    img.paste(config_title, (0, 0), config_title)
    img_draw = ImageDraw.Draw(img)

    # 获取数据
    uid_list = await get_all_uid()
    cookie_list = await get_all_cookie()
    stoken_list = await get_all_stoken()

    uid_num = len(uid_list)
    cookie_num = len(cookie_list)
    stoken_num = len(stoken_list)
    img_draw.text((210, 600), str(uid_num), first_color, gs_font_40, 'mm')
    img_draw.text((431, 600), str(cookie_num), first_color, gs_font_40, 'mm')
    img_draw.text((651, 600), str(stoken_num), first_color, gs_font_40, 'mm')

    tasks = []
    for index, name in enumerate(DETAIL_MAP):
        tasks.append(_draw_config_line(img, name, index))
    await asyncio.gather(*tasks)

    res = await convert_img(img)
    logger.info('[查询配置信息]绘图已完成,等待发送!')
    return res


async def _draw_config_line(img: Image.Image, name: str, index: int):
    detail = DETAIL_MAP[name]
    switch_name = SWITCH_MAP[name]
    config_line = Image.open(TEXT_PATH / 'config_line.png')
    config_line_draw = ImageDraw.Draw(config_line)
    if name.startswith('定时'):
        name += '(全部)'
    config_line_draw.text((52, 46), name, first_color, gs_font_36, 'lm')
    config_line_draw.text((52, 80), detail, second_color, gs_font_24, 'lm')
    if await config_check(switch_name):
        config_line.paste(config_on, (613, 21), config_on)
    else:
        config_line.paste(config_off, (613, 21), config_off)
    img.paste(config_line, (26, 850 + index * 155), config_line)
