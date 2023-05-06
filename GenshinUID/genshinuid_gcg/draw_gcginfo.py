from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error

from ..utils.mys_api import mys_api
from ..utils.image.convert import convert_img
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import CARD_PATH
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_26,
    gs_font_32,
    gs_font_50,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'

rank1 = Image.open(TEXT_PATH / '1.png').resize((400, 54))
rank2 = Image.open(TEXT_PATH / '2.png').resize((400, 54))
rank3 = Image.open(TEXT_PATH / '3.png').resize((400, 54))
rank4 = Image.open(TEXT_PATH / '4.png').resize((400, 54))

frist_color = (45, 45, 45)
second_color = (53, 53, 53)


async def draw_gcg_info(uid: str) -> Union[bytes, str]:
    # 获得数据
    raw_data = await mys_api.get_gcg_info(uid)
    if isinstance(raw_data, int):
        return get_error(raw_data)

    if raw_data['covers'] == []:
        return f'UID{uid}还没有开启七圣召唤玩法 或 未去米游社激活数据！'

    # 解析数据
    nickname: str = raw_data['nickname']
    level: int = raw_data['level']
    avatar_card_num_gained: int = raw_data['avatar_card_num_gained']
    avatar_card_num_total: int = raw_data['avatar_card_num_total']
    action_card_num_gained: int = raw_data['action_card_num_gained']
    action_card_num_total: int = raw_data['action_card_num_total']

    avatar_rate = avatar_card_num_gained / avatar_card_num_total
    action_rate = action_card_num_gained / action_card_num_total

    avatar = f'{avatar_card_num_gained} / {avatar_card_num_total}'
    action = f'{action_card_num_gained} / {action_card_num_total}'

    # 制作图片
    img = Image.open(TEXT_PATH / 'BG.png')
    avatar_bar = await get_bar(avatar_rate)
    action_bar = await get_bar(action_rate)
    img.paste(avatar_bar, (440, 36), avatar_bar)
    img.paste(action_bar, (440, 101), action_bar)

    img_draw = ImageDraw.Draw(img)
    # 右上区域
    img_draw.text((469, 63), '已解锁角色牌', frist_color, gs_font_26, 'lm')
    img_draw.text((469, 128), '已收集行动牌', frist_color, gs_font_26, 'lm')

    img_draw.text((805, 63), avatar, frist_color, gs_font_26, 'rm')
    img_draw.text((805, 128), action, frist_color, gs_font_26, 'rm')

    # 左上区域
    img_draw.text((165, 87), nickname, frist_color, gs_font_32, 'lm')
    img_draw.text((165, 120), f'UID{uid}', frist_color, gs_font_18, 'lm')
    img_draw.text((102, 97), str(level), 'white', gs_font_50, 'mm')

    for i, card in enumerate(raw_data['covers']):
        file_name = f'{card["id"]}.png'
        path = CARD_PATH / file_name
        if path.exists():
            card_img = Image.open(path).resize((160, 275))
        else:
            await download(card['image'], 9, file_name)
            card_img = Image.open(path).resize((160, 275))

        img.paste(card_img, (65 + i * 204, 198), card_img)

    img = await convert_img(img)
    logger.info('[七圣召唤]绘图已结束，等待发送...')
    return img


async def get_bar(rate: float) -> Image.Image:
    if rate <= 0.25:
        bar = rank1
    elif rate <= 0.58:
        bar = rank2
    elif rate <= 0.8:
        bar = rank3
    else:
        bar = rank4

    return bar
