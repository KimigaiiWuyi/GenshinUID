import re
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image, ImageOps, ImageDraw

from .main import ann
from .util import filter_list
from ..utils.image.convert import convert_img
from ..genshinuid_config.gs_config import gsconfig
from ..utils.fonts.genshin_fonts import gs_font_18, gs_font_26
from ..utils.image.image_tools import (
    get_pic,
    easy_paste,
    draw_text_by_line,
    easy_alpha_composite,
)

assets_dir = Path(__file__).parent / 'assets'

list_head = Image.open(assets_dir / 'list.png')
list_item = (
    Image.open(assets_dir / 'item.png').resize((384, 96)).convert('RGBA')
)


async def ann_list_card() -> bytes:
    ann_list = await ann().get_ann_list()
    if not ann_list:
        raise Exception('获取游戏公告失败,请检查接口是否正常')

    height_len = max(len(ann_list[0]['list']), len(ann_list[1]['list']))

    bg = Image.new(
        'RGBA',
        (
            list_head.width,
            list_head.height + list_item.height * height_len + 20 + 30,
        ),
        '#f9f6f2',
    )
    easy_paste(bg, list_head, (0, 0))

    for data in ann_list:
        x = 45
        if data['type_id'] == 1:
            x = 472

        for index, ann_info in enumerate(data['list']):
            new_item = list_item.copy()
            subtitle = ann_info['subtitle']
            draw_text_by_line(
                new_item,
                (0, 30 - (len(subtitle) > 10 and 10 or 0)),
                subtitle,
                gs_font_26,
                '#3b4354',
                250,
                True,
            )

            draw_text_by_line(
                new_item,
                (new_item.width - 80, 10),
                str(ann_info['ann_id']),
                gs_font_18,
                '#3b4354',
                100,
            )

            bg = easy_alpha_composite(
                bg, new_item, (x, list_head.height + (index * new_item.height))
            )

    tip = '*可以使用 原神公告#0000(右上角ID) 来查看详细内容, 例子: 原神公告#2434'
    draw_text_by_line(
        bg, (0, bg.height - 35), tip, gs_font_18, '#767779', 1000, True
    )

    return await convert_img(bg)


async def ann_detail_card(ann_id):
    ann_list = await ann().get_ann_content()
    if not ann_list:
        raise Exception('获取游戏公告失败,请检查接口是否正常')
    content = filter_list(ann_list, lambda x: x['ann_id'] == ann_id)
    if not content:
        raise Exception('没有找到对应的公告ID :%s' % ann_id)
    soup = BeautifulSoup(content[0]['content'], 'lxml')
    banner = content[0]['banner']
    ann_img = banner if banner else ''
    for a in soup.find_all('a'):
        a.string = ''

    msg_list = [ann_img]
    for img in soup.find_all('img'):
        msg_list.append(img.get('src'))
        # img.string = img.get('src')

    msg_list.extend(
        [
            BeautifulSoup(x.get_text('').replace('<<', ''), 'lxml').get_text()
            + '\n'
            for x in soup.find_all('p')
        ]
    )

    drow_height = 0
    for msg in msg_list:
        if msg.strip().endswith(('jpg', 'png')):
            _msg = re.search(r'(https://.*[png|jpg])', msg)
            if _msg:
                msg = _msg.group(0)
            img = await get_pic(msg.strip())
            img_height = img.size[1]
            if img.width > 1080:
                img_height = int(img.height * 0.6)
            drow_height += img_height + 40
        else:
            (
                x_drow_duanluo,
                x_drow_note_height,
                x_drow_line_height,
                x_drow_height,
            ) = split_text(msg)
            drow_height += x_drow_height

    im = Image.new('RGB', (1080, drow_height), '#f9f6f2')
    draw = ImageDraw.Draw(im)
    # 左上角开始
    x, y = 0, 0
    for msg in msg_list:
        if msg.strip().endswith(('jpg', 'png')):
            _msg = re.search(r'(https://.*[png|jpg])', msg)
            if _msg:
                msg = _msg.group(0)
            img = await get_pic(msg.strip())
            if img.width > im.width:
                img = img.resize((int(img.width * 0.6), int(img.height * 0.6)))
            easy_paste(im, img, (0, y))
            y += img.size[1] + 40
        else:
            (
                drow_duanluo,
                drow_note_height,
                drow_line_height,
                drow_height,
            ) = split_text(msg)
            for duanluo, line_count in drow_duanluo:
                draw.text((x, y), duanluo, fill=(0, 0, 0), font=gs_font_26)
                y += drow_line_height * line_count

    if hasattr(gs_font_26, 'getsize'):
        _x, _y = gs_font_26.getsize('囗')  # type: ignore
    else:
        bbox = gs_font_26.getbbox('囗')
        _x, _y = bbox[2] - bbox[0], bbox[3] - bbox[1]

    padding = (_x, _y, _x, _y)
    im = ImageOps.expand(im, padding, '#f9f6f2')

    return await convert_img(im)


def split_text(content: str):
    # 按规定宽度分组
    max_line_height, total_lines = 0, 0
    allText = []
    for text in content.split('\n'):
        duanluo, line_height, line_count = get_duanluo(text)
        max_line_height = max(line_height, max_line_height)
        total_lines += line_count
        allText.append((duanluo, line_count))
    line_height = max_line_height
    total_height = total_lines * line_height
    drow_height = total_lines * line_height
    return allText, total_height, line_height, drow_height


def get_duanluo(text: str):
    txt = Image.new('RGBA', (600, 800), (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    # 所有文字的段落
    duanluo = ''
    max_width = 1080
    # 宽度总和
    sum_width = 0
    # 几行
    line_count = 1
    # 行高
    line_height = 0
    for char in text:
        left, top, right, bottom = draw.textbbox((0, 0), char, gs_font_26)
        width, height = (right - left, bottom - top)
        sum_width += width
        if sum_width > max_width:  # 超过预设宽度就修改段落 以及当前行数
            line_count += 1
            sum_width = 0
            duanluo += '\n'
        duanluo += char
        line_height = max(height, line_height)
    if not duanluo.endswith('\n'):
        duanluo += '\n'
    return duanluo, line_height, line_count


def sub_ann(bot_id: str, group: str):
    groups = gsconfig.get_config('Ann_Groups').data
    if bot_id not in groups:
        groups[bot_id] = []
    if group in groups[bot_id]:
        return '已经订阅了'
    else:
        groups[bot_id].append(group)
        gsconfig.set_config('Ann_Groups', groups)
    return '成功订阅原神公告'


def unsub_ann(bot_id: str, group: str):
    groups = gsconfig.get_config('Ann_Groups').data
    if bot_id not in groups:
        groups[bot_id] = []
    if group in groups[bot_id]:
        groups[bot_id].remove(group)
        gsconfig.set_config('Ann_Groups', groups)
        return '成功取消订阅原神公告'
    else:
        return '已经不在订阅中了'
