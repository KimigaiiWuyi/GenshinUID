from pathlib import Path
from typing import Union

from nonebot.log import logger
from PIL import Image, ImageDraw

from ..utils.mhy_api.get_mhy_data import get_award
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import get_color_bg
from ..utils.genshin_fonts.genshin_fonts import genshin_font_origin

TEXT_PATH = Path(__file__).parent / 'texture2d'

note_pic = Image.open(TEXT_PATH / 'note.png')
oops_pic = Image.open(TEXT_PATH / 'oops.png')
ok_pic = Image.open(TEXT_PATH / 'ok.png')

first_color = (29, 29, 29)
second_color = (67, 61, 56)

gs_font_26 = genshin_font_origin(26)
gs_font_38 = genshin_font_origin(38)
gs_font_58 = genshin_font_origin(58)

COLOR_MAP = {
    '邮件奖励': (127, 115, 173),
    '每日活跃': (190, 158, 97),
    '活动奖励': (89, 126, 162),
    '深境螺旋': (113, 152, 113),
    '冒险奖励': (220, 99, 96),
    '任务奖励': (107, 182, 181),
    '其他': (118, 168, 196),
    'Mail': (127, 115, 173),
    'Daily Activity': (190, 158, 97),
    'Events': (89, 126, 162),
    'Spiral Abyss': (113, 152, 113),
    'Adventure': (220, 99, 96),
    'Quests': (107, 182, 181),
    'Other': (118, 168, 196),
}


async def draw_note_img(uid: str) -> Union[bytes, str]:
    # 获取数据
    data = await get_award(uid)
    nickname = data['data']['nickname']
    day_stone = data['data']['day_data']['current_primogems']
    day_mora = data['data']['day_data']['current_mora']
    lastday_stone = 0
    lastday_mora = 0
    if int(uid[0]) < 6:
        lastday_stone = data['data']['day_data']['last_primogems']
        lastday_mora = data['data']['day_data']['last_mora']
    month_stone = data['data']['month_data']['current_primogems']
    month_mora = data['data']['month_data']['current_mora']
    lastmonth_stone = data['data']['month_data']['last_primogems']
    lastmonth_mora = data['data']['month_data']['last_mora']

    day_stone_str = await int_carry(day_stone)
    day_mora_str = await int_carry(day_mora)
    month_stone_str = await int_carry(month_stone)
    month_mora_str = await int_carry(month_mora)
    lastday_stone_str = f'昨日原石:{await int_carry(lastday_stone)}'
    lastday_mora_str = f'昨日摩拉:{await int_carry(lastday_mora)}'
    lastmonth_stone_str = f'上月原石:{await int_carry(lastmonth_stone)}'
    lastmonth_mora_str = f'上月摩拉:{await int_carry(lastmonth_mora)}'

    # 处理数据
    # 今日比昨日 原石
    day_stone_percent = day_stone / lastday_stone if lastday_stone != 0 else 1
    day_stone_percent = day_stone_percent if day_stone_percent <= 1 else 1
    # 今日比昨日 摩拉
    day_mora_percent = day_mora / lastday_mora if lastday_mora != 0 else 1
    day_mora_percent = day_mora_percent if day_mora_percent <= 1 else 1
    # 本月比上月 原石
    month_stone_percent = (
        month_stone / lastmonth_stone if lastmonth_stone != 0 else 1
    )
    month_stone_percent = (
        month_stone_percent if month_stone_percent <= 1 else 1
    )
    # 本月比上月 摩拉
    month_mora_percent = (
        month_mora / lastmonth_mora if lastmonth_mora != 0 else 1
    )
    month_mora_percent = month_mora_percent if month_mora_percent <= 1 else 1

    # 获取背景图片各项参数
    based_w = 850
    based_h = 1900

    img = await get_color_bg(based_w, based_h)
    img.paste(note_pic, (0, 0), note_pic)

    ring_pic = Image.open(TEXT_PATH / 'ring.apng')
    ring_list = []
    ring_list.append([int(day_stone_percent * 49 + 0.5), (-5, 475)])
    ring_list.append([int(day_mora_percent * 49 + 0.5), (371, 475)])
    ring_list.append([int(month_stone_percent * 49 + 0.5), (-5, 948)])
    ring_list.append([int(month_mora_percent * 49 + 0.5), (371, 948)])
    ring_list.sort(key=lambda x: -x[0], reverse=True)
    for i in ring_list:
        ring_pic.seek(i[0])
        img.paste(ring_pic, i[1], ring_pic)

    img_draw = ImageDraw.Draw(img)
    # UID
    img_draw.text((430, 464), f'UID {uid}', second_color, gs_font_38, 'mm')

    # 具体数据
    img_draw.text((243, 718), day_stone_str, first_color, gs_font_58, 'mm')
    img_draw.text((625, 718), day_mora_str, first_color, gs_font_58, 'mm')
    img_draw.text((245, 1192), month_stone_str, first_color, gs_font_58, 'mm')
    img_draw.text((621, 1192), month_mora_str, first_color, gs_font_58, 'mm')

    img_draw.text(
        (245, 923), lastday_stone_str, second_color, gs_font_26, 'mm'
    )
    img_draw.text((621, 923), lastday_mora_str, second_color, gs_font_26, 'mm')
    img_draw.text(
        (245, 1396), lastmonth_stone_str, second_color, gs_font_26, 'mm'
    )
    img_draw.text(
        (621, 1396), lastmonth_mora_str, second_color, gs_font_26, 'mm'
    )

    if data['data']['month_data']['group_by'] == []:
        for index, action in enumerate(COLOR_MAP):
            if action == '其他':
                continue
            img_draw.text(
                (614, 1535 + index * 52),
                f'{action}:无',
                second_color,
                gs_font_26,
                'mm',
            )
        img.paste(oops_pic, (106, 1513), oops_pic)
    else:
        xy = ((94, 1515), (384, 1805))
        temp = -90
        for index, i in enumerate(data['data']['month_data']['group_by']):
            img_draw.pieslice(
                xy,
                temp,
                temp + (i['percent'] / 100) * 360,
                COLOR_MAP[i['action']],
            )
            temp = temp + (i['percent'] / 100) * 360
            if i['action'] == '其他':
                continue
            img_draw.rectangle(
                ((407, 1523 + index * 52), (453, 1548 + index * 52)),
                fill=COLOR_MAP[i['action']],
            )
            img_draw.text(
                (614, 1535 + index * 52),
                f'{i["action"]}:{i["num"]}',
                second_color,
                gs_font_26,
                'mm',
            )
        img.paste(ok_pic, (115, 1535), ok_pic)

    img = await convert_img(img)
    logger.info('[原石札记] 图片绘制完成!等待发送...')
    return img


async def int_carry(i: int) -> str:
    if i >= 100000:
        i_str = '{:.1f}W'.format(i / 10000)
    else:
        i_str = str(i)
    return i_str
