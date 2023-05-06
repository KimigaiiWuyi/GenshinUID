from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import get_error

from ..utils.mys_api import mys_api
from ..utils.image.convert import convert_img
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import CARD_PATH
from ..utils.colors import sec_color, first_color, light_color
from ..utils.fonts.genshin_fonts import gs_font_20, gs_font_36
from ..utils.image.image_tools import (
    get_color_bg,
    get_qq_avatar,
    draw_pic_with_ring,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'


async def draw_deck_img(
    user_id: str, uid: str, deck_id: int
) -> Union[str, bytes]:
    # 获取数据
    raw_data = await mys_api.get_gcg_deck(uid)
    if isinstance(raw_data, int):
        return get_error(raw_data)
    if len(raw_data['deck_list']) < deck_id:
        return f'你没有第{deck_id}套卡组！'
    raw_data = raw_data['deck_list'][deck_id - 1]
    deck_name = raw_data['name']
    # 获取背景图片各项参数
    _id = str(user_id)
    if _id.startswith('http'):
        char_pic = await get_qq_avatar(avatar_url=_id)
    else:
        char_pic = await get_qq_avatar(qid=user_id)
    char_pic = await draw_pic_with_ring(char_pic, 320)

    # 初始化图片
    img = await get_color_bg(950, 2300)

    char_mask = Image.open(TEXT_PATH / 'char_mask.png')
    for index, avatar in enumerate(raw_data['avatar_cards']):
        path = CARD_PATH / f'{avatar["id"]}.png'
        if not path.exists():
            await download(avatar['image'], 9, f'{avatar["id"]}.png')
        EMPTY_IMG = Image.new('RGBA', (320, 320))
        CHAR_IMG = Image.new('RGBA', (320, 320))
        char_img = Image.open(path).resize((420, 720))
        EMPTY_IMG.paste(char_img, (-29, 5), char_img)
        CHAR_IMG.paste(EMPTY_IMG, (0, 0), char_mask)
        img.paste(CHAR_IMG, (18 + index * 296, 518), CHAR_IMG)

    avatar_title = Image.open(TEXT_PATH / 'desk_title.png')
    img.paste(avatar_title, (0, 0), avatar_title)
    img.paste(char_pic, (318, 45), char_pic)
    img_draw = ImageDraw.Draw(img)
    img_draw.text((475, 410), f'UID {uid}', first_color, gs_font_36, 'mm')
    img_draw.text((475, 466), deck_name, first_color, gs_font_36, 'mm')

    action_card = raw_data['action_cards']

    action_cards = []
    for action in action_card:
        for _ in range(action['num']):
            action_cards.append(action)

    same = Image.open(TEXT_PATH / 'same.png')
    void = Image.open(TEXT_PATH / 'void.png')
    step = 137
    for cut in range(5):
        _c = cut * 6
        _cc = _c + 6
        bg = Image.open(TEXT_PATH / 'bar.png')
        bg_draw = ImageDraw.Draw(bg)
        for index, action in enumerate(action_cards[_c:_cc]):
            path = CARD_PATH / f'{action["id"]}.png'
            if not path.exists():
                await download(action['image'], 9, f'{action["id"]}.png')
            card = Image.open(path).resize((109, 187))
            bg.paste(card, (82 + index * step, 39), card)
            value = str(action['action_cost'][0]['cost_value'])
            if action['action_cost'][0]['cost_type'] == 'CostTypeSame':
                t_color = sec_color
                bg.paste(same, (148 + index * step, 43), same)
            else:
                t_color = light_color
                bg.paste(void, (148 + index * step, 43), void)
            bg_draw.text(
                (168 + index * step, 63),
                value,
                t_color,
                gs_font_20,
                'mm',
            )
            bg_draw.text(
                (137 + index * step, 249),
                action['name'],
                first_color,
                gs_font_20,
                'mm',
            )
        img.paste(bg, (0, 827 + cut * 285), bg)
    img = await convert_img(img)
    logger.info('[七圣召唤]绘图已结束，等待发送...')
    return img
