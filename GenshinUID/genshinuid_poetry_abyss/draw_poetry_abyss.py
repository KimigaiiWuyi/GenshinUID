from pathlib import Path
from datetime import datetime
from typing import List, Union

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.image_tools import get_avatar_with_ring

from ..utils.mys_api import mys_api
from ..utils.colors import first_color
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import add_footer
from ..utils.resource.download_url import download_file
from ..utils.resource.RESOURCE_PATH import ICON_PATH, CHAR_CARD_PATH
from ..utils.resource.generate_char_card import create_single_char_card
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_28,
    gs_font_36,
    gs_font_40,
    gs_font_50,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'
DIFFICULTY_MAP = {
    1: '简单模式',
    2: '普通模式',
    3: '困难模式',
}


def timestamp_to_str(timestamp: float):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime('%Y.%m.%d %H:%M:%S')


async def draw_buff(
    data: List,
    startb: int,
    stage: Image.Image,
    stage_draw: ImageDraw.ImageDraw,
    _type: str,
):
    if _type == '神秘收获':
        y = 206
    else:
        y = 253

    for index_choice, choice in enumerate(data):
        name = f'{choice["name"]}.png'
        path = ICON_PATH / name
        if not path.exists():
            await download_file(choice['icon'], 8, name)
        icon = Image.open(path).resize((45, 45)).convert('RGBA')
        buff = Image.open(TEXT_PATH / 'buff.png')
        buff.paste(icon, (-3, -4), icon)
        stage.paste(buff, (startb + index_choice * 44, y), buff)

    if not data:
        stage_draw.text(
            (startb, y + 21), f'暂无{_type}', (68, 59, 45), gs_font_20, 'lm'
        )


async def draw_poetry_abyss_img(uid: str, ev: Event) -> Union[str, bytes]:
    data = await mys_api.get_poetry_abyss_data(uid)
    if isinstance(data, int):
        return get_error(data)

    if not data['is_unlock'] or not data['data']:
        return '[幻想真境剧诗] 你还没有解锁该模式！'

    data = data['data'][0]
    round_data = data['detail']['rounds_data']
    stat_data = data['stat']

    start_time = timestamp_to_str(float(data['schedule']['start_time']))
    end_time = timestamp_to_str(float(data['schedule']['end_time']))

    w, h = 1000, 1040 + 50 + (len(round_data) // 2) * 330

    img = Image.new('RGBA', (w, h), (22, 18, 20))

    title = Image.open(TEXT_PATH / 'title.png').convert('RGBA')
    status = Image.open(TEXT_PATH / 'status.png').convert('RGBA')
    title_draw = ImageDraw.Draw(title)
    status_draw = ImageDraw.Draw(status)

    avatar = await get_avatar_with_ring(ev, 278)
    title.paste(avatar, (361, 115), avatar)
    title_draw.text((500, 473), f'UID {uid}', 'white', gs_font_36, 'mm')

    difficulty = DIFFICULTY_MAP.get(stat_data['difficulty_id'], '困难模式')
    max_round_id = stat_data['max_round_id']
    is_gold = (
        True
        if stat_data['difficulty_id'] == 3 and max_round_id == 8
        else False
    )
    time = f'{start_time} ~ {end_time}'
    avatar_bonus = stat_data['avatar_bonus_num']
    rent_cnt = stat_data['rent_cnt']
    coin_num = stat_data['coin_num']

    if is_gold:
        status_icon = Image.open(TEXT_PATH / 'yes.png')
    else:
        status_icon = Image.open(TEXT_PATH / 'no.png')

    status_icon = status_icon.convert('RGBA')
    status.paste(status_icon, (560, 111), status_icon)
    status_draw.text((462, 132), difficulty, (236, 233, 229), gs_font_36, 'mm')
    status_draw.text((500, 189), time, (139, 137, 133), gs_font_20, 'mm')

    status_draw.text(
        (220, 398), f'第{max_round_id}幕', (68, 59, 45), gs_font_50, 'mm'
    )
    status_draw.text(
        (416, 398), f'{avatar_bonus}', (68, 59, 45), gs_font_50, 'mm'
    )
    status_draw.text((604, 398), f'{rent_cnt}', (68, 59, 45), gs_font_50, 'mm')
    status_draw.text((793, 398), f'{coin_num}', (68, 59, 45), gs_font_50, 'mm')

    flower_yes = Image.open(TEXT_PATH / 'flower_yes.png').convert('RGBA')
    flower_no = Image.open(TEXT_PATH / 'flower_no.png').convert('RGBA')
    medals = stat_data['get_medal_round_list']

    while len(medals) < 8:
        medals.append(0)

    for index, medal in enumerate(medals):
        flower = flower_yes if medal else flower_no
        status.paste(flower, (449 + 42 * index, 270), flower)

    img.paste(title, (0, 0), title)
    img.paste(status, (0, 474), status)

    for i, r in enumerate(round_data):
        is_get_medal = r['is_get_medal']
        round_id = r['round_id']
        _medal = flower_yes if is_get_medal else flower_no

        if i % 2 == 0:
            stage = Image.open(TEXT_PATH / 'stage.png')
            stage_draw = ImageDraw.Draw(stage)
            stage_draw.text(
                (160, 54), f'第{round_id}幕', (68, 59, 45), gs_font_28, 'lm'
            )
            stage.paste(_medal, (97, 32), _medal)
            startx = 92
            startb = 116
        else:
            stage_draw.text(
                (830, 54), f'第{round_id}幕', (68, 59, 45), gs_font_28, 'rm'
            )
            stage.paste(_medal, (866, 32), _medal)
            startx = 520
            startb = 552

        for index_char, char in enumerate(r['avatars']):
            char_id = char['avatar_id']
            char_type = char['avatar_type']
            char_pic_path = CHAR_CARD_PATH / f'{char_id}.png'
            # 不存在自动下载
            if not char_pic_path.exists():
                await create_single_char_card(char_id)
            char_card = Image.open(char_pic_path).convert('RGBA')
            char_card_draw = ImageDraw.Draw(char_card)
            char_card_draw.text(
                (128, 280),
                f'Lv.{char["level"]}',
                font=gs_font_40,
                fill=first_color,
                anchor='mm',
            )
            char_card = char_card.resize((89, 108), Image.Resampling.LANCZOS)
            stage.paste(
                char_card,
                (startx + 97 * index_char, 88),
                char_card,
            )
            if char_type != 1:
                char_tag = Image.open(TEXT_PATH / f'{char_type}.png')
                stage.paste(
                    char_tag,
                    (startx + 16 + 97 * index_char, 75),
                    char_tag,
                )

        await draw_buff(
            r['choice_cards'],
            startb,
            stage,
            stage_draw,
            '神秘收获',
        )
        await draw_buff(
            r['buffs'],
            startb,
            stage,
            stage_draw,
            '奇妙助益',
        )

        if i % 2 == 1:
            img.paste(stage, (0, 1040 + 330 * (i // 2)), stage)

    img = add_footer(img, 1000)

    res = await convert_img(img)
    return res
