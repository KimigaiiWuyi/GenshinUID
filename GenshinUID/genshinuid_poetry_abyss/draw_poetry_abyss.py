from pathlib import Path
from datetime import datetime
from typing import List, Union, Optional

from PIL import Image, ImageDraw
from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.image_tools import get_avatar_with_ring

from ..utils.mys_api import mys_api
from ..utils.colors import first_color
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import add_footer
from ..utils.resource.download_url import download, download_file
from ..utils.resource.generate_char_card import create_single_char_card
from ..utils.resource.RESOURCE_PATH import (
    ICON_PATH,
    CHAR_CARD_PATH,
    CHAR_SIDE_PATH,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_26,
    gs_font_28,
    gs_font_30,
    gs_font_38,
    gs_font_40,
)

TEXT_PATH = Path(__file__).parent / 'texture2d'
DIFFICULTY_MAP = {
    1: '简单模式',
    2: '普通模式',
    3: '困难模式',
    4: '卓越模式',
    5: '月喻模式',
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


async def draw_poetry_abyss_img(
    uid: str, ev: Event, active: Optional[int] = None
) -> Union[str, bytes]:
    data = await mys_api.get_poetry_abyss_data(uid, active)
    if isinstance(data, int):
        return get_error(data)

    if not data['is_unlock'] or not data['data']:
        return '[幻想真境剧诗] 你还没有解锁该模式！'

    if active:
        data = data['data'][-1]
    else:
        data = data['data'][0]

    round_data = data['detail']['rounds_data']
    fight_statisic = data['detail']['fight_statisic']
    stat_data = data['stat']

    start_time = timestamp_to_str(float(data['schedule']['start_time']))
    end_time = timestamp_to_str(float(data['schedule']['end_time']))

    difficulty = DIFFICULTY_MAP.get(stat_data['difficulty_id'], '困难模式')
    max_round = stat_data["max_round_id"]
    if stat_data['difficulty_id'] == 3:
        if stat_data['max_round_id'] == 8:
            icon_name = 'gold_yes.png'
        else:
            icon_name = 'gold_no.png'
    elif stat_data['difficulty_id'] == 4:
        if stat_data['max_round_id'] == 10:
            icon_name = 'super_yes.png'
        else:
            icon_name = 'super_no.png'
    elif stat_data['difficulty_id'] == 5:
        if (
            stat_data['max_round_id'] == 10
            and stat_data['tarot_finished_cnt'] == 2
        ):
            icon_name = 'moon_yes.png'
        else:
            icon_name = 'moon_no.png'
        max_round = 12
    else:
        icon_name = 'gold_no.png'
    icon = Image.open(TEXT_PATH / icon_name).convert('RGBA')

    w, h = 1200, 760 + 80 + (len(round_data) // 2) * 280

    img = Image.new('RGBA', (w, h), (22, 18, 20))

    title = Image.open(TEXT_PATH / 'title.png').convert('RGBA')
    title_fg = Image.open(TEXT_PATH / 'title_fg.png').convert('RGBA')
    avatar = await get_avatar_with_ring(ev, 180)
    title.paste(avatar, (119, 328), avatar)
    title.paste(title_fg, (0, 0), title_fg)

    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (362, 428),
        f'{ev.sender["nickname"] if "nickname" in ev.sender else "旅行者"}',
        'white',
        gs_font_40,
        'lm',
    )
    title_draw.text(
        (458, 478),
        f'UID {uid}',
        (207, 207, 207),
        gs_font_30,
        'mm',
    )
    title_draw.text(
        (875, 430),
        f'{difficulty}',
        'white',
        gs_font_30,
        'mm',
    )
    title_draw.text(
        (1072, 430),
        f'{stat_data["medal_num"]}/{max_round}',
        'white',
        gs_font_30,
        'mm',
    )
    title_draw.text(
        (1118, 482),
        f'{start_time} ~ {end_time}',
        (139, 137, 133),
        gs_font_20,
        'rm',
    )
    title.paste(icon, (726, 406), icon)

    best_hit = Image.open(TEXT_PATH / 'best_hit.png').convert('RGBA')
    max_damage_avatar = fight_statisic['max_damage_avatar']
    _char_id = max_damage_avatar['avatar_id']
    char_side_path = CHAR_SIDE_PATH / f'{_char_id}.png'
    if not char_side_path.exists():
        await download_file(
            max_damage_avatar['avatar_icon'], 3, f'{_char_id}.png'
        )
    char_side = Image.open(char_side_path)
    char_side = char_side.resize((75, 75))
    best_hit.paste(char_side, (27, 7), char_side)
    best_hit_draw = ImageDraw.Draw(best_hit)
    best_hit_draw.text(
        (189, 58),
        f'{max_damage_avatar["value"]}',
        (255, 255, 255),
        gs_font_26,
        'mm',
    )
    best_hit_draw.text(
        (68, 91),
        '最高伤害',
        (255, 255, 255),
        gs_font_20,
        'mm',
    )
    title.paste(best_hit, (860, 222), best_hit)
    img.paste(title, (0, 0), title)

    status = Image.open(TEXT_PATH / 'bar.png').convert('RGBA')
    status_draw = ImageDraw.Draw(status)

    max_round_id = stat_data['max_round_id']
    avatar_bonus = stat_data['avatar_bonus_num']
    rent_cnt = stat_data['rent_cnt']
    coin_num = stat_data['coin_num']
    tarot_cnt = stat_data['tarot_finished_cnt']
    total_time = fight_statisic['total_use_time']
    total_time_str = f'{total_time // 60}分{total_time % 60}秒'

    status_draw.text(
        (145, 41),
        f'第{max_round_id}幕',
        'white',
        gs_font_38,
        'mm',
    )
    status_draw.text(
        (327, 41),
        f'圣牌{tarot_cnt}',
        'white',
        gs_font_38,
        'mm',
    )
    status_draw.text(
        (508, 41),
        f'{coin_num}',
        'white',
        gs_font_38,
        'mm',
    )
    status_draw.text(
        (690, 41),
        f'{avatar_bonus}',
        'white',
        gs_font_38,
        'mm',
    )
    status_draw.text(
        (871, 41),
        f'{rent_cnt}',
        'white',
        gs_font_38,
        'mm',
    )
    status_draw.text(
        (1052, 41),
        f'{total_time_str}',
        'white',
        gs_font_38,
        'mm',
    )
    img.paste(status, (0, 577), status)

    flower_yes = Image.open(TEXT_PATH / 'flower_yes.png').convert('RGBA')
    flower_no = Image.open(TEXT_PATH / 'flower_no.png').convert('RGBA')
    for i, r in enumerate(round_data):
        is_get_medal = r['is_get_medal']
        round_id = r['round_id']
        _medal = flower_yes if is_get_medal else flower_no

        if r['is_tarot']:
            round_name = f'圣牌{r["tarot_serial_no"]}'
            stage_bg = 'stage_moon'
        else:
            round_name = f'第{round_id}幕'
            stage_bg = 'stage'

        stage = Image.open(TEXT_PATH / f'{stage_bg}.png')
        stage_draw = ImageDraw.Draw(stage)

        stage_draw.text((172, 63), round_name, 'white', gs_font_28, 'mm')
        stage.paste(_medal, (57, 38), _medal)

        for bindex, buff in enumerate(r['splendour_buff']['buffs']):
            buff_image = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
            buff_image_draw = ImageDraw.Draw(buff_image)
            buff_icon_url = buff['icon']
            buff_icon_path = ICON_PATH / f'{buff["name"]}.png'
            if not buff_icon_path.exists():
                await download(buff_icon_url, 8, f'{buff["name"]}.png')
            buff_icon = Image.open(buff_icon_path).convert('RGBA')
            buff_icon = buff_icon.resize((51, 51))
            buff_image.paste(buff_icon, (14, 5), buff_icon)
            buff_image_draw.text(
                (40, 62),
                f'Lv{buff["level"]}',
                'white',
                gs_font_20,
                'mm',
            )

            stage.paste(buff_image, (323 + 65 * bindex, 18), buff_image)

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
            char_card = char_card.resize((110, 133), Image.Resampling.LANCZOS)
            stage.paste(
                char_card,
                (45 + 123 * index_char, 109),
                char_card,
            )
            if char_type != 1:
                char_tag = Image.open(TEXT_PATH / f'{char_type}.png')
                stage.paste(
                    char_tag,
                    (45 + 29 + 123 * index_char, 99),
                    char_tag,
                )

        img.paste(stage, (30 + 570 * (i % 2), 760 + 280 * (i // 2)), stage)

    img = add_footer(img, 1000)
    res = await convert_img(img)
    return res
