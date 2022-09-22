from typing import List
from pathlib import Path

from nonebot.log import logger
from PIL import Image, ImageDraw

from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_simple_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin
from ..utils.db_operation.db_operation import (
    select_db,
    get_push_data,
    get_user_bind_data,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'

status_s_on = Image.open(TEXT_PATH / 'status_s_on.png')
status_s_off = Image.open(TEXT_PATH / 'status_s_off.png')
status_l_off = Image.open(TEXT_PATH / 'status_l_off.png')
status_l_on = Image.open(TEXT_PATH / 'status_l_on.png')
uid_hint = Image.open(TEXT_PATH / 'uid_hint.png')

EN_MAP = {'Coin': '宝钱', 'Resin': '体力', 'Go': '派遣', 'Transform': '质变仪'}

white_color = (254, 243, 231)
gs_font_20 = genshin_font_origin(20)
gs_font_15 = genshin_font_origin(15)
gs_font_26 = genshin_font_origin(26)


async def get_user_card(qid: str) -> bytes:
    uid_list: List = await select_db(qid, 'list')  # type: ignore
    w, h = 500, len(uid_list) * 210 + 330
    img = await get_simple_bg(w, h)
    white_overlay = Image.new('RGBA', (w, h), (244, 244, 244, 200))
    img.paste(white_overlay, (0, 0), white_overlay)
    uid_title = Image.open(TEXT_PATH / 'uid_title.png')
    uid_title_draw = ImageDraw.Draw(uid_title)
    uid_title_draw.text(
        (47, 70), f'频道ID {str(qid)}', (106, 100, 89), font=gs_font_26
    )
    img.paste(uid_title, (0, 50), uid_title)
    img.paste(uid_hint, (0, 145 + len(uid_list) * 210), uid_hint)
    for uid_index, uid in enumerate(uid_list):
        user_push_data = await get_push_data(uid)
        user_bind_data = await get_user_bind_data(uid)
        if not user_bind_data:
            user_bind_data = {
                'QID': qid,
                'UID': uid,
                'Stoken': None,
                'Cookies': None,
                'StatusA': 'off',
                'StatusB': 'off',
                'StatusC': 'off',
            }
        uid_img = Image.open(TEXT_PATH / 'uid_part.png')
        uid_img_draw = ImageDraw.Draw(uid_img)
        uid_img_draw.text(
            (112, 45),
            f'UID{uid}',
            white_color,
            font=gs_font_20,
            anchor='mm',
        )
        uid_img_draw.text(
            (390, 17),
            f'QID{user_bind_data["QID"]}',
            white_color,
            font=gs_font_20,
            anchor='mm',
        )
        if user_bind_data['Cookies']:
            uid_img.paste(status_s_on, (292, 41), status_s_on)
        else:
            uid_img.paste(status_s_off, (292, 41), status_s_off)

        if user_bind_data['Stoken']:
            uid_img.paste(status_s_on, (428, 41), status_s_on)
        else:
            uid_img.paste(status_s_off, (428, 41), status_s_off)

        if user_bind_data['StatusA'] != 'off':
            uid_img.paste(status_s_on, (135, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (135, 76), status_s_off)

        if user_bind_data['StatusB'] != 'off':
            uid_img.paste(status_s_on, (270, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (270, 76), status_s_off)

        if user_bind_data['StatusC'] != 'off':
            uid_img.paste(status_s_on, (428, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (428, 76), status_s_off)

        for index, mode in enumerate(['Coin', 'Resin', 'Go', 'Transform']):
            if user_push_data[f'{mode}Push'] != 'off':
                uid_img.paste(
                    status_l_on, (25 + index * 115, 112), status_l_on
                )

            else:
                uid_img.paste(
                    status_l_off, (25 + index * 115, 112), status_l_off
                )
            uid_img_draw.text(
                (78 + index * 115, 141),
                f'{EN_MAP[mode]}推送',
                white_color,
                font=gs_font_20,
                anchor='mm',
            )
            uid_img_draw.text(
                (78 + index * 115, 164),
                f'阈值:{user_push_data[f"{mode}Value"]}',
                white_color,
                font=gs_font_15,
                anchor='mm',
            )
        img.paste(uid_img, (0, 150 + uid_index * 210), uid_img)

    res: bytes = await convert_img(img)  # type: ignore
    logger.info('[查询绑定状态]绘图已完成,等待发送!')
    return res
