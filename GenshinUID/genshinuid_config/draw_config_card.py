import asyncio
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger

from .gs_config import gsconfig
from ..utils.database import get_sqla
from ..utils.image.convert import convert_img
from ..utils.resource.RESOURCE_PATH import TEXT2D_PATH
from ..utils.fonts.genshin_fonts import gs_font_24, gs_font_36, gs_font_40

TEXT_PATH = Path(__file__).parent / 'texture2d'
config_title = Image.open(TEXT_PATH / 'config_title.png')
config_on = Image.open(TEXT_PATH / 'config_on.png')
config_off = Image.open(TEXT_PATH / 'config_off.png')

first_color = (20, 20, 20)
second_color = (57, 57, 57)


async def draw_config_img(bot_id: str) -> Union[bytes, str]:
    from ..utils.image.image_tools import CustomizeImage

    sqla = get_sqla(bot_id)
    # 获取背景图片各项参数
    based_w = 850
    based_h = 850 + 155 * (len(gsconfig) - 8)

    CI_img = CustomizeImage('', based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    color_mask = Image.new('RGBA', (based_w, based_h), color)
    config_mask = Image.open(TEXT2D_PATH / 'mask.png').resize(
        (based_w, based_h)
    )
    img.paste(color_mask, (0, 0), config_mask)
    img.paste(config_title, (0, 0), config_title)
    img_draw = ImageDraw.Draw(img)

    # 获取数据
    uid_list = await sqla.get_all_uid_list()
    cookie_list = await sqla.get_all_cookie()
    stoken_list = await sqla.get_all_stoken()

    uid_num = len(uid_list)
    cookie_num = len(cookie_list)
    stoken_num = len(stoken_list)
    img_draw.text((210, 600), str(uid_num), first_color, gs_font_40, 'mm')
    img_draw.text((431, 600), str(cookie_num), first_color, gs_font_40, 'mm')
    img_draw.text((651, 600), str(stoken_num), first_color, gs_font_40, 'mm')

    tasks = []
    index = 0
    for name in gsconfig:
        if isinstance(gsconfig[name].data, bool):
            tasks.append(_draw_config_line(img, name, index))
            index += 1
    await asyncio.gather(*tasks)

    res = await convert_img(img)
    logger.info('[查询配置信息]绘图已完成,等待发送!')
    return res


async def _draw_config_line(img: Image.Image, name: str, index: int):
    detail = gsconfig[name].desc
    config_line = Image.open(TEXT_PATH / 'config_line.png')
    config_line_draw = ImageDraw.Draw(config_line)
    if name.startswith('定时'):
        name += '(全部)'
    title = gsconfig[name].title
    config_line_draw.text((52, 46), title, first_color, gs_font_36, 'lm')
    config_line_draw.text((52, 80), detail, second_color, gs_font_24, 'lm')
    if gsconfig[name].data:
        config_line.paste(config_on, (613, 21), config_on)
    else:
        config_line.paste(config_off, (613, 21), config_off)
    img.paste(config_line, (26, 850 + index * 155), config_line)
