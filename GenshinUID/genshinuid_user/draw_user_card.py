from typing import List
from pathlib import Path

from PIL import Image, ImageDraw

from ..utils.database import active_sqla
from ..utils.image.convert import convert_img
from ..gsuid_utils.database.models import GsUser
from ..utils.image.image_tools import get_simple_bg
from ..utils.fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'

status_s_on = Image.open(TEXT_PATH / 'status_s_on.png')
status_s_off = Image.open(TEXT_PATH / 'status_s_off.png')
status_l_off = Image.open(TEXT_PATH / 'status_l_off.png')
status_l_on = Image.open(TEXT_PATH / 'status_l_on.png')
uid_hint = Image.open(TEXT_PATH / 'uid_hint.png')

EN_MAP = {'coin': '宝钱', 'resin': '体力', 'go': '派遣', 'transform': '质变仪'}

white_color = (254, 243, 231)
gs_font_20 = genshin_font_origin(20)
gs_font_15 = genshin_font_origin(15)
gs_font_26 = genshin_font_origin(26)


async def get_user_card(bot_id: str, user_id: str) -> bytes:
    sqla = active_sqla[bot_id]
    uid_list: List = await sqla.get_bind_uid_list(user_id)
    w, h = 500, len(uid_list) * 210 + 330
    img = await get_simple_bg(w, h)
    white_overlay = Image.new('RGBA', (w, h), (244, 244, 244, 200))
    img.paste(white_overlay, (0, 0), white_overlay)
    uid_title = Image.open(TEXT_PATH / 'uid_title.png')
    uid_title_draw = ImageDraw.Draw(uid_title)
    uid_title_draw.text(
        (47, 70), f'QQ号{str(user_id)}', (106, 100, 89), font=gs_font_26
    )
    img.paste(uid_title, (0, 50), uid_title)
    img.paste(uid_hint, (0, 145 + len(uid_list) * 210), uid_hint)
    for uid_index, uid in enumerate(uid_list):
        user_push_data = await sqla.select_push_data(uid)
        user_data = await sqla.select_user_data(uid)
        if user_data is None:
            user_data = GsUser(
                bot_id=bot_id,
                user_id=user_id,
                uid=uid,
                stoken=None,
                cookie=None,
                sign_switch='off',
                bbs_switch='off',
                push_switch='off',
            )
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
            f'user_id{user_data.user_id}',
            white_color,
            font=gs_font_20,
            anchor='mm',
        )
        if user_data.cookie:
            uid_img.paste(status_s_on, (292, 41), status_s_on)
        else:
            uid_img.paste(status_s_off, (292, 41), status_s_off)

        if user_data.stoken:
            uid_img.paste(status_s_on, (428, 41), status_s_on)
        else:
            uid_img.paste(status_s_off, (428, 41), status_s_off)

        if user_data.push_switch != 'off':
            uid_img.paste(status_s_on, (135, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (135, 76), status_s_off)

        if user_data.sign_switch != 'off':
            uid_img.paste(status_s_on, (270, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (270, 76), status_s_off)

        if user_data.bbs_switch != 'off':
            uid_img.paste(status_s_on, (428, 76), status_s_on)
        else:
            uid_img.paste(status_s_off, (428, 76), status_s_off)

        for index, mode in enumerate(['coin', 'resin', 'go', 'transform']):
            if getattr(user_push_data, f'{mode}_push') != 'off':
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
                f'阈值:{getattr(user_push_data, f"{mode}_value")}',
                white_color,
                font=gs_font_15,
                anchor='mm',
            )
        img.paste(uid_img, (0, 150 + uid_index * 210), uid_img)

    return await convert_img(img)
