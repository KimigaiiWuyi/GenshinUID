from typing import Dict, Tuple

from PIL import Image, ImageDraw

from ..mono.Enemy import Enemy
from ..mono.Fight import Fight
from ..etc.MAP_PATH import dmgMap
from ..mono.Character import Character
from ..etc.etc import TEXT_PATH, get_char_std
from ...utils.genshin_fonts.genshin_fonts import gs_font_28

dmgBar_1 = Image.open(TEXT_PATH / 'dmgBar_1.png')
dmgBar_2 = Image.open(TEXT_PATH / 'dmgBar_2.png')

text_color = (255, 255, 255)
title_color = (255, 255, 100)


async def get_char_dmg_percent(char: Character) -> Dict:
    enemy = Enemy(char.char_level, char.char_level)
    fight = Fight({char.char_name: char}, enemy)
    dmg_data = await fight.get_dmg_dict(char.char_name)
    percent = 0
    char.seq_str = '无匹配'
    if char.char_name in dmgMap:
        std = await get_char_std(char.card_prop, char.char_name)
        if std['skill']:
            value = 0
            std_value = 0
            if std['skill'] == 'atk':
                value = char.fight_prop['atk']
                std_value = std['atk']
            elif std['skill'] == 'def':
                value = char.fight_prop['def']
                std_value = std['other']['防御']
            elif std['skill'] in dmg_data:
                if dmg_data[std['skill']]['crit'] == 0:
                    value = dmg_data[std['skill']]['normal']
                else:
                    value = dmg_data[std['skill']]['crit']
                std_value = std['value']
                if char.char_name == '夜兰':
                    std_value *= 3
            if std_value != 0:
                percent = (value / std_value) * 100
                char.seq_str = (
                    '|'.join([i[:2] for i in std['seq'].split('|')])
                    + std['seq'][-1]
                )
    char.percent = '{:.2f}'.format(percent)
    char.dmg_data = dmg_data
    return dmg_data


async def draw_dmg_img(char: Character) -> Tuple[Image.Image, int]:
    # 获取值
    dmg_data = await get_char_dmg_percent(char)
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
