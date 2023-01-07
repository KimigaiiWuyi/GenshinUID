import json
from io import BytesIO
from pathlib import Path
from textwrap import fill

from httpx import AsyncClient, get
from PIL import Image, ImageDraw, ImageFont

from ..utils.download_resource.RESOURCE_PATH import RESOURCE_PATH
from ..utils.minigg_api.get_minigg_data import (
    get_char_info,
    get_misc_info,
    get_audio_info,
    get_weapon_info,
)

R_PATH = Path(__file__).parents[0]
TEXT_PATH = R_PATH / 'texture2D'
RELIC_PATH = R_PATH / 'relicIcon'
ITEM_PATH = R_PATH / 'itemIcon'

WIKI_PATH = RESOURCE_PATH / 'wiki'
WIKI_ARTIFACTS_PATH = WIKI_PATH / 'artifacts'
WIKI_WEAPON_PATH = WIKI_PATH / 'weapons'
WIKI_CHAR_PATH = WIKI_PATH / 'chars'


def genshin_font_origin(size: int):
    return ImageFont.truetype(
        str(TEXT_PATH / 'yuanshen_origin.ttf'), size=size
    )


async def strLenth(r: str, size: int, limit: int = 540) -> str:
    result = ''
    temp = 0
    for i in r:
        if temp >= limit:
            result += '\n' + i
            temp = 0
        else:
            result += i

        if i.isdigit():
            temp += round(size / 10 * 6)
        elif i == '/':
            temp += round(size / 10 * 2.2)
        elif i == '.':
            temp += round(size / 10 * 3)
        elif i == '%':
            temp += round(size / 10 * 9.4)
        else:
            temp += size
    return result


async def draw_artifacts_wiki_img(data: dict) -> Path:
    # 获取数据
    # data = await get_misc_info('artifacts', name)
    name = data['name']

    # 获取资源路径
    artifacts_bar_path = TEXT_PATH / 'artifacts_bar.png'
    slider_path = TEXT_PATH / 'slider.png'
    star_bar_path = TEXT_PATH / 'star_bar.png'

    artifacts_suitbar4_path = TEXT_PATH / 'wiki_artifacts_suitbar4.png'
    artifacts_suitbar2_path = TEXT_PATH / 'wiki_artifacts_suitbar2.png'
    artifacts_suitbar1_path = TEXT_PATH / 'wiki_artifacts_suitbar1.png'

    artifacts_bg1_path = TEXT_PATH / 'wiki_artifacts_bg1.png'
    artifacts_bg2_path = TEXT_PATH / 'wiki_artifacts_bg2.png'
    artifacts_bg3_path = TEXT_PATH / 'wiki_artifacts_bg3.png'

    img1 = Image.open(artifacts_bg1_path)
    img2 = Image.open(artifacts_bg2_path)
    img3 = Image.open(artifacts_bg3_path)

    # 转为全角字符
    """
    pc2 = ''
    pc4 = ''
    for uchar in data['2pc']:
        code = ord(uchar)
        if 32 <= code <= 126:
            code += 65248
            new_char = chr(code)
        else:
            new_char = uchar
        pc2 += new_char

    for uchar in data['4pc']:
        code = ord(uchar)
        if 32 <= code <= 126:
            code += 65248
            new_char = chr(code)
        else:
            new_char = uchar
        pc4 += new_char
    """

    if '1pc' in data:
        suitbar1 = Image.open(artifacts_suitbar1_path)
        pc1 = await strLenth('　　　　' + data['1pc'], 22, 455)

        # 计算长度
        img_draw = ImageDraw.Draw(img1)
        _, _, _, y1 = img_draw.textbbox((0, 0), pc1, genshin_font_origin(22))
        y2 = 0
    else:
        suitbar4 = Image.open(artifacts_suitbar4_path)
        suitbar2 = Image.open(artifacts_suitbar2_path)
        pc2 = await strLenth('　　　　' + data['2pc'], 22, 455)
        pc4 = await strLenth('　　　　' + data['4pc'], 22, 455)

        # 计算长度
        img_draw = ImageDraw.Draw(img1)
        _, _, _, y1 = img_draw.textbbox((0, 0), pc2, genshin_font_origin(22))
        _, _, _, y2 = img_draw.textbbox((0, 0), pc4, genshin_font_origin(22))

    img_h = 250 + y1 + y2 + 30 + 500 + 50
    wrap_middle = ((img_h - 760) // 50) + 1

    result_img = Image.new('RGBA', (590, img_h))
    result_img.paste(img1, (0, 0), img1)
    result_img.paste(img3, (0, img_h - 100), img3)
    for i in range(wrap_middle):
        result_img.paste(img2, (0, 660 + i * 50), img2)

    star_bar = Image.open(star_bar_path)
    result_img.paste(star_bar, (95, 215), star_bar)

    if '1pc' in data:
        result_img.paste(suitbar1, (63, 250 + 10), suitbar1)
    else:
        result_img.paste(suitbar2, (63, 250 + 10), suitbar2)
        result_img.paste(suitbar4, (63, 250 + y1 + 40), suitbar2)

        slider = Image.open(slider_path)
        result_img.paste(slider, (0, 270 + y1), slider)

    artifacts_bar = Image.open(artifacts_bar_path)
    artifacts_bar_draw = ImageDraw.Draw(artifacts_bar)
    artifacts_list = ['flower', 'plume', 'sands', 'goblet', 'circlet']

    for index, i in enumerate(artifacts_list):
        # for index, i in enumerate(data['images']):
        if '1pc' in data and i != 'circlet':
            # index = 4
            continue
        icon = data['images'][i].split('/')[-1]
        # print("icon:", icon)
        icon_url = data['images'][i]
        # print("icon_url:", icon_url)
        if '.png' not in icon_url:
            continue

        artifacts_part_img = (
            Image.open(BytesIO(get(icon_url).content))
            .convert('RGBA')
            .resize((80, 80), Image.Resampling.LANCZOS)
        )
        # artifacts_part_img = Image.open(
        # RELIC_PATH / icon).convert('RGBA').resize((80, 80), Image.Resampling.LANCZOS)
        artifacts_bar.paste(
            artifacts_part_img, (76, 32 + index * 90), artifacts_part_img
        )
        artifacts_bar_draw.text(
            (183, 58 + 90 * index),
            data[i]['name'],
            (154, 123, 51),
            genshin_font_origin(26),
            'lm',
        )
        artifacts_bar_draw.text(
            (183, 90 + 90 * index),
            fill(data[i]['description'], width=24),
            (182, 173, 165),
            genshin_font_origin(14),
            'lm',
        )

    result_img.paste(artifacts_bar, (0, 260 + y2 + y1 + 40), artifacts_bar)

    rarity = '稀有度：' + '/'.join(data['rarity'])

    text_draw = ImageDraw.Draw(result_img)
    text_draw.text(
        (295, 182), data['name'], (154, 123, 51), genshin_font_origin(40), 'mm'
    )
    text_draw.text(
        (295, 230), rarity, (175, 145, 75), genshin_font_origin(23), 'mm'
    )
    if '1pc' in data:
        text_draw.text(
            (63, 250 + 10 + 3), pc1, (111, 100, 80), genshin_font_origin(22)
        )
    else:
        text_draw.text(
            (63, 250 + 10 + 3), pc2, (111, 100, 80), genshin_font_origin(22)
        )
        text_draw.text(
            (63, 250 + y1 + 40 + 3),
            pc4,
            (111, 100, 80),
            genshin_font_origin(22),
        )

    logo = Image.open(TEXT_PATH / 'wuyi_dark.png')
    result_img.paste(logo, (370, img_h - 30), logo)

    result_img = result_img.convert('RGB')
    WIKI_ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
    result_img.save(
        WIKI_ARTIFACTS_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=100,
        subsampling=0,
    )

    IMG_PATH = WIKI_ARTIFACTS_PATH / '{}.jpg'.format(data['name'])

    return IMG_PATH


async def draw_weapons_wiki_img(data: dict) -> Path:
    # 获取数据
    # data = await get_weapon_info(name)
    name = data['name']
    level90_data = await get_weapon_info(name, '90')

    base_atk = str(data['baseatk'])
    sub_name = data['substat']
    if data['subvalue'] != '':
        base_sub_val = (
            (data['subvalue'] + '%')
            if sub_name != '元素精通'
            else data['subvalue']
        )
    else:
        base_sub_val = ''

    if sub_name != '':
        sub_val = (
            '%.1f%%' % (level90_data['specialized'] * 100)
            if sub_name != '元素精通'
            else str(round(level90_data['specialized']))
        )
    else:
        sub_val = ''

    # 满级90级/70级
    try:
        atk = str(round(level90_data['attack']))
    except:
        level70_data = await get_weapon_info(name, '70')
        atk = str(round(level70_data['attack']))
        # print(f"{name}最高70级")

    attr = '攻击力 {}/{}   {} {}/{}'.format(
        base_atk, atk, sub_name, base_sub_val, sub_val
    )

    # 效果名称
    if data['effectname'] != '':
        raw_effect = data['effect']
        rw_ef = []
        for i in range(len(data['r1'])):
            now = ''
            for j in range(1, 6):
                now = now + data['r{}'.format(j)][i] + '/'
            now = now[:-1]
            rw_ef.append(now)
        raw_effect = raw_effect.format(*rw_ef)
    else:
        raw_effect = ''

    # 获取资源路径
    slider_path = TEXT_PATH / 'slider.png'
    star_bar_path = TEXT_PATH / 'star_bar.png'
    attr_bar_path = TEXT_PATH / 'attr_bar.png'

    weapons_bg1_path = TEXT_PATH / 'wiki_weapons_bg1.png'
    weapons_bg2_path = TEXT_PATH / 'wiki_artifacts_bg2.png'
    weapons_bg3_path = TEXT_PATH / 'wiki_artifacts_bg3.png'

    cost_bg_path = TEXT_PATH / 'UI_Item_Bg.png'

    """
    # 转为全角字符
    effect = '・'
    for uchar in raw_effect:
        code = ord(uchar)
        if 32 <= code <= 126:
            code += 65248
            new_char = chr(code)
        else:
            new_char = uchar
        effect += new_char
    """

    effect = await strLenth('・' + raw_effect, 24, 485)

    # 计算长度
    img1 = Image.open(weapons_bg1_path)
    img2 = Image.open(weapons_bg2_path)
    img3 = Image.open(weapons_bg3_path)
    img_draw = ImageDraw.Draw(img1)
    _, _, _, y = img_draw.textbbox((0, 0), effect, genshin_font_origin(24))

    img_h = 660 + 100 + y + 100 + 190
    wrap_middle = ((img_h - 760) // 50) + 1

    result_img = Image.new('RGBA', (590, img_h))
    result_img.paste(img1, (0, 0), img1)
    result_img.paste(img3, (0, img_h - 100), img3)
    for i in range(wrap_middle):
        result_img.paste(img2, (0, 660 + i * 50), img2)

    # 贴图
    weapon_img = (
        Image.open(BytesIO(get(data['images']['icon']).content))
        .convert('RGBA')
        .resize((312, 312), Image.Resampling.LANCZOS)
    )
    result_img.paste(weapon_img, (139, 175), weapon_img)
    star_bar = Image.open(star_bar_path)
    result_img.paste(star_bar, (95, 617), star_bar)
    attr_bar = Image.open(attr_bar_path)
    result_img.paste(attr_bar, (0, 675), attr_bar)

    # 材料
    try:
        costs = data['costs']['ascend6'][1:]
    except:
        costs = data['costs']['ascend4'][1:]
    for index, cost in enumerate(costs):
        cost_data = json.loads(
            get('https://info.minigg.cn/materials?query=' + cost['name']).text
        )
        if index < 1:
            cost_info = cost_data['dropdomain'] + '({})'.format(
                ' & '.join(cost_data['daysofweek'][:-1])
            )
        cost_bg = Image.open(cost_bg_path)

        # 重定向
        cost_icon_url = cost_data['images']['redirect']
        # print(cost_icon_url)
        async with AsyncClient() as client:
            r = await client.get(
                url=cost_icon_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
                    "Content-Type": "application/json",
                },
                follow_redirects=True,
            )
        # print(r.url)
        cost_icon = (
            Image.open(BytesIO(r.content))
            .convert('RGBA')
            .resize((90, 90), Image.Resampling.LANCZOS)
        )
        # cost_icon = Image.open(ITEM_PATH / '{}.png'.format(
        #     cost_data['images']['nameicon'])).resize((90, 90), Image.Resampling.LANCZOS)
        cost_bg.paste(cost_icon, (15, 10), cost_icon)
        cost_draw = ImageDraw.Draw(cost_bg)
        cost_draw.text(
            (64, 115),
            cost_data['name'],
            (255, 255, 255),
            genshin_font_origin(13),
            'mm',
        )
        result_img.paste(
            cost_bg, (30 + index * 140, 660 + 100 + y + 110), cost_bg
        )

    # 写字
    text_draw = ImageDraw.Draw(result_img)
    text_draw.text(
        (295, 579), data['name'], (154, 123, 51), genshin_font_origin(40), 'mm'
    )
    text_draw.text(
        (295, 632),
        '稀有度：' + data['rarity'],
        (175, 145, 75),
        genshin_font_origin(23),
        'mm',
    )
    text_draw.text(
        (295, 695), attr, (255, 255, 255), genshin_font_origin(28), 'mm'
    )

    text_draw.text(
        (40, 660 + 50 + y + 120),
        cost_info,
        (175, 145, 75),
        genshin_font_origin(28),
        'lm',
    )

    if data['effectname']:
        text_draw.text(
            (295, 750),
            data['effectname'],
            (175, 145, 75),
            genshin_font_origin(24),
            'mm',
        )
        text_draw.text(
            (38, 660 + 120), effect, (87, 89, 101), genshin_font_origin(24)
        )

    logo = Image.open(TEXT_PATH / 'wuyi_dark.png')
    result_img.paste(logo, (370, img_h - 30), logo)

    result_img = result_img.convert('RGB')
    WIKI_WEAPON_PATH.mkdir(parents=True, exist_ok=True)
    result_img.save(
        WIKI_WEAPON_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=100,
        subsampling=0,
    )
    IMG_PATH = WIKI_WEAPON_PATH / '{}.jpg'.format(data['name'])

    return IMG_PATH


async def draw_chars_wiki_img(data: dict) -> Path:
    # 获取数据
    # data = await get_char_info(name, 'char', None)
    name = data['name']
    level90_data = await get_char_info(name, 'char', '90')
    skill_data = await get_char_info(name, 'talents')

    # 获取资源路径
    slider_path = TEXT_PATH / 'slider.png'
    star_bar_path = TEXT_PATH / 'star_bar.png'
    attr_bar_path = TEXT_PATH / 'attr_bar.png'
    wiki_char_attr4_path = TEXT_PATH / 'wiki_char_attr_bg.png'

    chars_bg1_path = TEXT_PATH / 'wiki_weapons_bg1.png'
    chars_mask_bg1_path = TEXT_PATH / 'wiki_char_maskbg1.png'
    chars_mask_bg2_path = TEXT_PATH / 'wiki_char_maskbg2.png'
    chars_mask_bg3_path = TEXT_PATH / 'wiki_char_maskbg3.png'

    cost_bg_path = TEXT_PATH / 'UI_Item_Bg.png'

    charimg = (
        Image.open(BytesIO(get(data['images']['cover1']).content))
        .convert('RGBA')
        .resize((862, 528), Image.Resampling.LANCZOS)
    )

    # 计算长度
    imgbg1 = Image.open(chars_bg1_path)
    img1 = Image.open(chars_mask_bg1_path)
    img2 = Image.open(chars_mask_bg2_path)
    img3 = Image.open(chars_mask_bg3_path)
    img_draw = ImageDraw.Draw(img1)

    y = []
    y_size = []
    for skill in skill_data:
        if skill.startswith('passive'):
            skill_info = skill_data[skill]['info']
            skill_name = skill_data[skill]['name']
            for i in range(1, 10):
                if i % 2 != 0:
                    skill_info = skill_info.replace('**', '「', 1)
                else:
                    skill_info = skill_info.replace('**', '」', 1)
            # skill_info = await strLenth(skill_info, 23, 490)
            _, _, _, y_temp = img_draw.textbbox(
                (0, 0), skill_name + '\n' + skill_info, genshin_font_origin(23)
            )
            skill_temp = {'name': skill_name, 'info': skill_info, 'y': y_temp}
            y.append(skill_temp)
            y_size.append(y_temp)

    y_length = sum(y_size) + 50 * (len(y_size) - 1)

    img_h = 360 + 580 + 100 + y_length + 275
    wrap_middle = ((img_h - 1040) // 100) + 1

    # 基本图生成
    result_img = Image.new('RGBA', (590, img_h))
    result_img.paste(imgbg1, (0, 0), imgbg1)
    result_img.paste(charimg, (-136, 33), charimg)
    result_img.paste(img1, (0, 360), img1)
    for i in range(wrap_middle):
        result_img.paste(img2, (0, 940 + i * 100), img2)
    result_img.paste(img3, (0, img_h - 100), img3)

    # 继续贴图
    star_bar = Image.open(star_bar_path)
    slider = Image.open(slider_path)
    attr_bar = Image.open(attr_bar_path)
    char_attr4 = Image.open(wiki_char_attr4_path)
    cost_bg = Image.open(cost_bg_path)

    result_img.paste(star_bar, (95, 621), star_bar)
    result_img.paste(slider, (0, 665), slider)
    result_img.paste(attr_bar, (0, 680), attr_bar)
    result_img.paste(char_attr4, (0, 725), char_attr4)

    # 材料
    char_costs = data['costs']['ascend6'][1:]
    skill_costs = [
        skill_data['costs']['lvl9'][1],
        skill_data['costs']['lvl9'][-1],
    ]
    costs = char_costs + skill_costs
    for index, cost in enumerate(costs):
        cost_data = json.loads(
            get('https://info.minigg.cn/materials?query=' + cost['name']).text
        )
        if index == 4:
            cost_info = cost_data['dropdomain'] + '({})'.format(
                ' & '.join(cost_data['daysofweek'][:-1])
            )
        cost_bg = Image.open(cost_bg_path)

        # 重定向
        cost_icon_url = cost_data['images']['redirect']
        # print(cost_icon_url)
        async with AsyncClient() as client:
            r = await client.get(
                url=cost_icon_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
                    "Content-Type": "application/json",
                },
                follow_redirects=True,
            )
        # print(r.url)
        cost_icon = (
            Image.open(BytesIO(r.content))
            .convert('RGBA')
            .resize((90, 90), Image.Resampling.LANCZOS)
        )
        # cost_icon = Image.open(ITEM_PATH / '{}.png'.format(
        #     cost_data['images']['nameicon'])).resize((90, 90), Image.Resampling.LANCZOS)
        cost_bg.paste(cost_icon, (15, 10), cost_icon)
        cost_draw = ImageDraw.Draw(cost_bg)
        cost_draw.text(
            (64, 115),
            cost_data['name'],
            (255, 255, 255),
            genshin_font_origin(13),
            'mm',
        )
        result_img.paste(
            cost_bg,
            (
                30 + (index % 3) * 140,
                360 + 580 + 55 + y_length + (index // 3 * 140),
            ),
            cost_bg,
        )

    # 写字
    text_draw = ImageDraw.Draw(result_img)
    y1 = 950
    for skill in y:
        text_draw.rounded_rectangle(
            (32, y1, 558, y1 + skill['y'] + 25),
            fill=(220, 211, 203),
            radius=15,
        )
        text_draw.text(
            (48, y1 + 25),
            skill['name'],
            (194, 155, 78),
            genshin_font_origin(23),
            'lm',
        )
        text_draw.text(
            (48, y1 + (skill['y'] + 10) / 2 + 20),
            skill['info'],
            (69, 69, 69),
            genshin_font_origin(23),
            'lm',
        )
        y1 += skill['y'] + 50

    text_draw.text(
        (295, 602), data['name'], (154, 123, 51), genshin_font_origin(40), 'mm'
    )
    text_draw.text(
        (295, 635),
        '稀有度：' + data['rarity'],
        (175, 145, 75),
        genshin_font_origin(23),
        'mm',
    )
    text_draw.text(
        (295, 912),
        await strLenth(data['description'], 23, 495),
        (69, 69, 69),
        genshin_font_origin(23),
        'mm',
    )
    # text_draw.text((295, 695), attr, (255, 255, 255), genshin_font_origin(28), 'mm')

    logo = Image.open(TEXT_PATH / 'wuyi_dark.png')
    result_img.paste(logo, (370, img_h - 30), logo)

    result_img = result_img.convert('RGB')
    WIKI_CHAR_PATH.mkdir(parents=True, exist_ok=True)
    result_img.save(
        WIKI_CHAR_PATH / '{}.jpg'.format(data['name']),
        format='JPEG',
        quality=100,
        subsampling=0,
    )
    IMG_PATH = WIKI_CHAR_PATH / '{}.jpg'.format(data['name'])

    return IMG_PATH
