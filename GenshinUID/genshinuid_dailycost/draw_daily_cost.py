import time
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.ambr.request import get_ambr_icon

from .get_daily_data import generate_daily_data
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.image.image_tools import get_color_bg, get_weapon_pic
from ..utils.fonts.genshin_fonts import gs_font_26, gs_font_36, gs_font_44
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    ICON_PATH,
    TEMP_PATH,
    WEAPON_PATH,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'


async def draw_daily_cost_img(is_force: bool = False) -> Union[str, bytes]:
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    timestamp = time.time()
    timestamp -= 14400
    _t = time.localtime(timestamp)
    wk = time.strftime(weekdays[_t.tm_wday], _t)

    path = TEMP_PATH / f'daily_cost_{wk}.jpg'
    if not is_force and path.exists():
        return await convert_img(Image.open(path))

    if wk == '周日':
        return '今天是周日, 所有材料都能获得噢！'

    data = await generate_daily_data()
    if data is None:
        return '获取信息错误...'
    elif data == {}:
        return '今天是周日, 所有材料都能获得噢！'

    w, h = 950, 630
    for domain in data:
        h += 110 + ((len(data[domain]) - 2) // 8 + 1) * 110

    img = await get_color_bg(w, h)

    title = Image.open(TEXT_PATH / 'title.png')
    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (475, 474),
        f'今天是{wk}哦!',
        'black',
        gs_font_36,
        'mm',
    )
    title_draw.text((475, 531), '每日材料', 'black', gs_font_36, 'mm')

    img.paste(title, (0, 0), title)

    y = 600
    for domain in data:
        icon_id = data[domain][0]
        icon = await get_ambr_icon('UI', icon_id, ICON_PATH, 'ItemIcon')

        icon = icon.resize((77, 77))
        bar = Image.open(TEXT_PATH / 'bar.png')
        bar_draw = ImageDraw.Draw(bar)
        if icon.mode == 'RGBA':
            mask = icon.split()[3]  # 获取alpha通道作为遮罩
            bar.paste(icon, (43, 10), mask)
        else:
            bar.paste(icon, (43, 10))  # 如果没有alpha通道，不使用遮罩

        domain1, domain2 = domain.split('：')

        bar_draw.text((142, 50), domain2, 'black', gs_font_44, 'lm')
        bar_draw.text((900, 50), domain1, 'black', gs_font_26, 'rm')

        img.paste(bar, (0, y), bar)

        for index, item in enumerate(data[domain]):
            if isinstance(item, int):
                continue

            rank: int = item['rank']

            if '炼武' in domain:
                item_path = WEAPON_PATH / f'{item["name"]}.png'
                if not item_path.exists():
                    item = await get_ambr_icon(
                        'UI',
                        item['icon'].replace('UI_EquipIcon_', ''),
                        WEAPON_PATH,
                        'EquipIcon',
                        f'{item["name"]}.png',
                    )
                else:
                    item = Image.open(item_path)
            else:
                if 'name' in item:
                    avatar_id = await name_to_avatar_id(item['name'])
                    item_path = CHAR_PATH / f'{avatar_id}.png'
                elif 'Boy' in item['icon']:
                    avatar_id = 10000005
                else:
                    avatar_id = 10000007

                item_path = CHAR_PATH / f'{avatar_id}.png'

                if not item_path.exists():
                    item = await get_ambr_icon(
                        'UI',
                        item['icon'].replace('UI_AvatarIcon_', ''),
                        CHAR_PATH,
                        'AvatarIcon',
                        f'{avatar_id}.png',
                    )
                else:
                    item = Image.open(item_path)

            if ((index - 1) % 8) == 0 and index != 0:
                y += 110

            item = item.resize((100, 100))
            item_bg = await get_weapon_pic(rank)
            item_bg = item_bg.resize((100, 100))

            img.paste(
                item_bg,
                (36 + ((index - 1) % 8) * 110, y),
                item_bg,
            )

            temp = Image.new('RGBA', (100, 100))
            temp.paste(item, (0, 0), item_bg)

            img.paste(
                temp,
                (36 + ((index - 1) % 8) * 110, y),
                temp,
            )

        y += 110

    # 最后生成图片
    all_black = Image.new('RGBA', img.size, (255, 255, 255))
    img = Image.alpha_composite(all_black, img)

    img = img.convert('RGB')
    img.save(
        TEMP_PATH / 'daily_cost.jpg',
        'JPEG',
        quality=89,
        subsampling=0,
    )

    return await convert_img(img)
