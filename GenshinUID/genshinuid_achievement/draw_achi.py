from pathlib import Path

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.convert import convert_img

from ..utils.mys_api import mys_api, get_base_data
from ..utils.resource.download_url import download
from ..utils.resource.RESOURCE_PATH import ACHI_ICON_PATH
from ..utils.fonts.genshin_fonts import gs_font_30, gs_font_36
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_v4_title,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'


async def draw_achi_img(ev: Event, uid: str):
    data = await mys_api.get_achievement_info(uid)
    if isinstance(data, int):
        return get_error(data)

    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

    w, h = 1950, title_img.size[1] + (((len(data) - 1) // 3) + 1) * 170 + 240
    img = get_v4_bg(w, h)

    img.paste(title_img, (137, 0), title_img)
    bar = Image.open(TEXT_PATH / 'bar.png')
    img.paste(bar, (0, title_img.size[1] + 20), bar)

    for index, achi in enumerate(data):
        icon_url = achi['icon']
        icon_id = achi['id']
        icon_name = f'{icon_id}.png'
        icon_path = ACHI_ICON_PATH / icon_name
        if not icon_path.exists():
            await download(icon_url, 15, icon_name)

        icon = Image.open(icon_path)
        icon = icon.resize((128, 128))

        percent = achi['percentage']
        finish_num = achi['finish_num']
        if percent == 0:
            all_num = '?'
        else:
            all_num = int((finish_num / percent) * 100)
        if percent >= 95:
            level = 5
            color = (249, 53, 53)
        elif percent >= 80:
            level = 4
            color = (255, 173, 0)
        elif percent >= 60:
            level = 3
            color = (243, 53, 249)
        elif percent >= 30:
            level = 2
            color = (53, 157, 249)
        else:
            level = 1
            color = (96, 220, 52)

        bg = Image.open(TEXT_PATH / f'bg{level}.png')
        bg.paste(icon, (28, 21), icon)
        bg_draw = ImageDraw.Draw(bg)

        name = achi['name'][:10]
        bg_draw.text(
            (160, 50),
            name,
            (255, 173, 0),
            gs_font_36,
            'lm',
        )

        bg_draw.text(
            (160, 93),
            f'{finish_num} / ~{all_num}',
            color,
            gs_font_30,
            'lm',
        )

        bg_draw.text(
            (543, 93),
            f'{percent}%',
            color,
            gs_font_30,
            'rm',
        )

        add_x = int((544 - 163) * percent / 100)

        bg_draw.rounded_rectangle((160, 117, 547, 137), 0, (0, 0, 0, 150))

        bg_draw.rounded_rectangle((163, 120, 163 + add_x, 134), 0, color)

        x = (index % 3) * 600 + 71
        y = (index // 3) * 170 + 837
        img.paste(bg, (x, y), bg)

    img = add_footer(img)
    return await convert_img(img)
