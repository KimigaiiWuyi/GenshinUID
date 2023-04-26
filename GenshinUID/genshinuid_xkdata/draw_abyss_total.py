from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw
from gsuid_core.utils.api.akashadata.request import get_akasha_abyss_info

from ..utils.image.image_tools import get_color_bg
from ..utils.resource.RESOURCE_PATH import CHAR_PATH
from ..utils.fonts.genshin_fonts import gs_font_24, gs_font_26, gs_font_30

TEXT_PATH = Path(__file__).parent / 'texture2d'
TOTAL_IMG = Path(__file__).parent / 'abyss_total.png'

black = (10, 10, 10)
grey = (40, 40, 40)

green = (205, 255, 168)
red = (255, 168, 168)


def _c(part: str) -> Tuple[int, int, int]:
    if part.startswith('-'):
        return red
    else:
        return green


async def draw_xk_abyss_img():
    raw_data = await get_akasha_abyss_info()
    last_time: str = raw_data['modify_time']  # 2022-11-23 00:06
    version_desc = raw_data['schedule_version_desc']  # 3.2第一期
    total_view = raw_data['abyss_total_view']
    last_rate = raw_data['last_rate']
    char_use_list = raw_data['character_used_list']

    # 基本数据
    avgs = total_view['avg_star']  # 人均摘星
    abc = total_view['avg_battle_count']  # 平均战斗
    ambc = total_view['avg_maxstar_battle_count']  # 满星平均战斗
    pr = total_view['pass_rate']  # 通关比例
    mr = total_view['maxstar_rate']  # 满星比例
    m12 = total_view['maxstar_12_rate']  # 12场36星

    # 倍率数据
    avgs_rate = last_rate['avg_star']  # 人均摘星
    abc_rate = last_rate['avg_battle_count']  # 平均战斗
    amb_rate = last_rate['avg_maxstar_battle_count']  # 满星平均战斗
    pr_rate = last_rate['pass_rate']  # 通关比例
    mr_rate = last_rate['maxstar_rate']  # 满星比例
    mf_rate = last_rate['maxstar_12_rate']  # 12场36星

    # 拿一些资源
    title = Image.open(TEXT_PATH / 'total_title.png')

    # 计算宽高
    h = 1020 + ((len(char_use_list) + 1) // 7 + 1) * 160 + 20

    # 开始绘图
    img = await get_color_bg(1080, h)
    img.paste(title, (0, 0), title)

    # 基础文字部分
    img_draw = ImageDraw.Draw(img)
    img_draw.text((673, 375), f'数据最后更新时间：{last_time}', grey, gs_font_30, 'mm')
    img_draw.text((855, 311), f'{version_desc}', black, gs_font_30, 'mm')

    # 概览部分 85*26
    r = 20
    img_draw.rounded_rectangle((428, 556, 513, 582), r, _c(avgs_rate))  # 人均摘星
    img_draw.text((471, 606), avgs, black, gs_font_26, 'mm')
    img_draw.text((471, 570), avgs_rate, grey, gs_font_24, 'mm')
    img_draw.rounded_rectangle((945, 556, 1030, 582), r, _c(abc_rate))  # 平均战斗
    img_draw.text((988, 606), abc, black, gs_font_26, 'mm')
    img_draw.text((988, 570), abc_rate, grey, gs_font_24, 'mm')
    img_draw.rounded_rectangle((428, 681, 513, 707), r, _c(amb_rate))  # 满星平均战斗
    img_draw.text((471, 731), ambc, black, gs_font_26, 'mm')
    img_draw.text((471, 695), amb_rate, grey, gs_font_24, 'mm')
    img_draw.rounded_rectangle((945, 681, 1030, 707), r, _c(pr_rate))  # 通关比例
    img_draw.text((988, 731), f'{pr}%', black, gs_font_26, 'mm')
    img_draw.text((988, 695), f'{pr_rate}%', grey, gs_font_24, 'mm')
    img_draw.rounded_rectangle((428, 806, 513, 832), r, _c(mr_rate))  # 满星比例
    img_draw.text((471, 856), f'{mr}%', black, gs_font_26, 'mm')
    img_draw.text((471, 820), f'{mr_rate}%', grey, gs_font_24, 'mm')
    img_draw.rounded_rectangle((945, 806, 1030, 832), r, _c(mf_rate))  # 12场36星
    img_draw.text((988, 856), f'{m12}%', black, gs_font_26, 'mm')
    img_draw.text((988, 820), f'{mf_rate}%', grey, gs_font_24, 'mm')

    # 遍历角色列表，获得使用率
    for index, char in enumerate(char_use_list):
        had_count: int = char['maxstar_person_had_count']
        use_count: int = char['maxstar_person_use_count']
        if had_count == 0 or use_count == 0:
            use_ratio = 0.0
        else:
            use_ratio = (use_count / had_count) * 100
        use_ratio = '{:.2f}%'.format(use_ratio)
        char_id: int = char['avatar_id']

        # 绘图部分
        char_bg = Image.open(TEXT_PATH / 'char_bg.png')
        charimg = Image.open(CHAR_PATH / f'{char_id}.png').resize((117, 117))
        char_bg.paste(charimg, (6, 2), charimg)
        char_bg_draw = ImageDraw.Draw(char_bg)
        if char['rarity'] >= 5:
            text = (193, 123, 0)
        else:
            text = (145, 49, 218)
        char_bg_draw.text((65, 133), use_ratio, text, gs_font_26, 'mm')

        # 粘贴
        x = index % 7 * 147
        y = index // 7 * 160
        img.paste(char_bg, (35 + x, 1010 + y), char_bg)

    bg = Image.new('RGBA', (1080, h), (255, 255, 255))
    img = Image.alpha_composite(bg, img)

    img.save(
        TOTAL_IMG,
        format='PNG',
        quality=80,
        subsampling=0,
    )
