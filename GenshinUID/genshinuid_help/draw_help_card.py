import json
from pathlib import Path

from PIL import Image, ImageDraw

from ..utils.image.image_tools import CustomizeImage
from ..utils.resource.RESOURCE_PATH import TEXT2D_PATH
from ..utils.fonts.genshin_fonts import (
    gs_font_18,
    gs_font_24,
    gs_font_28,
    gs_font_40,
)


async def draw_help_img():
    TEXT_PATH = Path(__file__).parent / 'texture2d'
    help_title = Image.open(TEXT_PATH / 'help_title.png')

    first_color = (20, 20, 20)
    second_color = (57, 57, 57)

    with open(Path(__file__).parent / 'help.json', "r", encoding='UTF-8') as f:
        help_data = json.load(f)

    all_help_num = 0
    module_row = 0
    help_row = 0

    for module in help_data:
        all_help_num += len(help_data[module]['data'])
        module_row += 1
        help_row += (len(help_data[module]['data']) + 2) // 3

    # 获取背景图片各项参数
    based_w = 850
    based_h = 30 + 720 + 110 * help_row + module_row * 100

    CI_img = CustomizeImage('', based_w, based_h)
    img = CI_img.bg_img
    color = CI_img.bg_color
    color_mask = Image.new('RGBA', (based_w, based_h), color)
    help_mask = Image.open(TEXT2D_PATH / 'mask.png').resize((based_w, based_h))
    img.paste(color_mask, (0, 0), help_mask)

    module_temp = 0
    alpha_img = Image.new('RGBA', (based_w, based_h))
    alpha_img.paste(help_title, (0, 0))
    for module in help_data:
        module_title = Image.open(TEXT_PATH / 'module_title.png')
        module_title_draw = ImageDraw.Draw(module_title)
        module_desc = help_data[module]['desc']
        module_title_draw.text((76, 53), module, first_color, gs_font_40, 'lm')
        module_title_draw.text(
            (767, 59), module_desc, second_color, gs_font_24, 'rm'
        )
        alpha_img.paste(module_title, (0, 720 + module_temp))
        for index, data in enumerate(help_data[module]['data']):
            func = Image.open(TEXT_PATH / 'func.png')
            func_draw = ImageDraw.Draw(func)
            func_draw.text(
                (125, 30), data['name'], first_color, gs_font_28, 'mm'
            )
            func_draw.text(
                (125, 65), data['desc'], second_color, gs_font_18, 'mm'
            )
            func_draw.text(
                (125, 85), data['eg'], second_color, gs_font_18, 'mm'
            )
            alpha_img.paste(
                func,
                (
                    51 + (index % 3) * 254,
                    820 + module_temp + (index // 3) * 110,
                ),
            )
        module_temp += 100 + 110 * ((len(help_data[module]['data']) + 2) // 3)
    img = Image.alpha_composite(img, alpha_img).convert('RGB')

    img.save(
        Path(__file__).parent / 'help.jpg',
        format='JPEG',
        quality=80,
        subsampling=0,
    )
