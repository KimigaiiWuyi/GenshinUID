from pathlib import Path
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw

from ..utils.database import get_sqla
from ..utils.image.convert import convert_img
from ..gsuid_utils.database.models import GsUser
from ..utils.colors import sec_color, first_color
from ..utils.fonts.genshin_fonts import gs_font_15, gs_font_30, gs_font_36
from ..utils.image.image_tools import (
    get_color_bg,
    get_qq_avatar,
    draw_pic_with_ring,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'

status_off = Image.open(TEXT_PATH / 'status_off.png')
status_on = Image.open(TEXT_PATH / 'status_on.png')

EN_MAP = {'coin': '宝钱', 'resin': '体力', 'go': '派遣', 'transform': '质变仪'}


async def get_user_card(bot_id: str, user_id: str) -> bytes:
    sqla = get_sqla(bot_id)
    uid_list: List = await sqla.get_bind_uid_list(user_id)
    w, h = 750, len(uid_list) * 750 + 470

    # 获取背景图片各项参数
    _id = str(user_id)
    if _id.startswith('http'):
        char_pic = await get_qq_avatar(avatar_url=_id)
    else:
        char_pic = await get_qq_avatar(qid=_id)
    char_pic = await draw_pic_with_ring(char_pic, 290)

    img = await get_color_bg(w, h)
    title = Image.open(TEXT_PATH / 'user_title.png')
    title.paste(char_pic, (241, 40), char_pic)

    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (375, 444), f'{bot_id} - {user_id}', first_color, gs_font_30, 'mm'
    )
    img.paste(title, (0, 0), title)

    for index, uid in enumerate(uid_list):
        user_card = Image.open(TEXT_PATH / 'user_bg.png')
        user_draw = ImageDraw.Draw(user_card)
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

        user_draw.text(
            (375, 62),
            f'UID {uid}',
            first_color,
            font=gs_font_36,
            anchor='mm',
        )

        x, y = 331, 112
        paste_switch(user_card, user_data.cookie, (241, 128))
        paste_switch(user_card, user_data.stoken, (241 + x, 128))
        paste_switch(user_card, user_data.sign_switch, (241, 128 + y))
        paste_switch(user_card, user_data.bbs_switch, (241 + x, 128 + y))
        paste_switch(user_card, user_data.push_switch, (241, 128 + 2 * y))
        paste_switch(user_card, user_data.status, (241 + x, 128 + 2 * y), True)

        for _index, mode in enumerate(['coin', 'resin', 'go', 'transform']):
            paste_switch(
                user_card,
                getattr(user_push_data, f'{mode}_push'),
                (241 + _index % 2 * x, 128 + (_index // 2 + 3) * y),
            )
            if getattr(user_push_data, f'{mode}_push') != 'off':
                user_draw.text(
                    (268 + _index % 2 * x, 168 + (_index // 2 + 3) * y),
                    f'{getattr(user_push_data, f"{mode}_value")}',
                    sec_color,
                    font=gs_font_15,
                    anchor='lm',
                )
        img.paste(user_card, (0, 500 + index * 690), user_card)

    return await convert_img(img)


def paste_switch(
    card: Image.Image,
    status: Optional[str],
    pos: Tuple[int, int],
    is_status: bool = False,
):
    if is_status:
        pic = status_off if status else status_on
    else:
        pic = status_on if status != 'off' and status else status_off
    card.paste(pic, pos, pic)
