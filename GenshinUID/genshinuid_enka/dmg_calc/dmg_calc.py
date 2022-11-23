from typing import Tuple

from PIL import Image, ImageDraw

from ..mono.Enemy import Enemy
from ..mono.Fight import Fight
from ..etc.etc import TEXT_PATH
from ..mono.Character import Character
from ...utils.genshin_fonts.genshin_fonts import gs_font_28

dmgBar_1 = Image.open(TEXT_PATH / 'dmgBar_1.png')
dmgBar_2 = Image.open(TEXT_PATH / 'dmgBar_2.png')

text_color = (255, 255, 255)
title_color = (255, 255, 100)


async def draw_dmg_img(char: Character) -> Tuple[Image.Image, int]:
    # 获取值
    enemy = Enemy(char.char_level, char.char_level)
    fight = Fight({char.char_name: char}, enemy)
    dmg_data = await fight.get_dmg_dict(char.char_name)
    if dmg_data == {}:
        return Image.new('RGBA', (950, 1)), 0
    # 计算伤害计算部分图片长宽值
    w = 950
    h = 40 * (len(dmg_data) + 1)
    result_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    # 反复贴上不同颜色的长条
    for i in range(0, len(dmg_data) + 1):
        pic = dmgBar_1 if i % 2 == 0 else dmgBar_2
        result_img.paste(pic, (0, i * 40))

    result_draw = ImageDraw.Draw(result_img)

    text_size = gs_font_28
    result_draw.text((45, 22), '角色动作', title_color, text_size, anchor='lm')
    result_draw.text((450, 22), '暴击值', title_color, text_size, anchor='lm')
    result_draw.text((615, 22), '期望值', title_color, text_size, anchor='lm')
    result_draw.text((780, 22), '普通值', title_color, text_size, anchor='lm')

    for index, name in enumerate(dmg_data):
        result_draw.text(
            (45, 22 + (index + 1) * 40),
            name,
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (450, 22 + (index + 1) * 40),
            str(round(dmg_data[name]['crit'])),
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (615, 22 + (index + 1) * 40),
            str(round(dmg_data[name]['avg'])),
            text_color,
            text_size,
            anchor='lm',
        )
        result_draw.text(
            (780, 22 + (index + 1) * 40),
            str(round(dmg_data[name]['normal'])),
            text_color,
            text_size,
            anchor='lm',
        )

    return result_img, len(dmg_data) + 2
