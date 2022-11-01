import json
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw

from ...utils.genshin_fonts.genshin_fonts import genshin_font_origin

DATA_PATH = Path(__file__).parent
TEXT_PATH = DATA_PATH / 'texture2D'

WEIGHT_MAP = {
    '暴击率': 1,
    '治疗加成': 1.15,
    '百分比攻击力': 1.5,
    '百分比血量': 1.5,
    '元素伤害加成': 1.5,
    '元素充能效率': 1.67,
    '百分比防御力': 1.875,
    '物理伤害加成': 1.875,
    '暴击伤害': 2,
    '元素精通': 6,
}

COLOR_MAP = {
    '攻击': '#f19b60',
    '精通': '#4dbe6b',
    '暴击': '#5dbbee',
    '物伤': '#ffffff',
    '伤': '#a1252a',
    '生命': '#67c750',
    '防御': '#9999de',
    '治疗': '#f9deb3',
    '充能': '#ff5858',
}

# 引入曲线Map
with open(DATA_PATH / 'char_curve.json', 'r', encoding='UTF-8') as f:
    CHAR_CURVE = json.load(f)

# 引入曲线Map
with open(DATA_PATH / 'curve.json', 'r', encoding='UTF-8') as f:
    CURVE = json.load(f)


async def get_weight_temp(prop: dict, attr: str) -> List[float]:
    weight = []
    if '攻击' in attr:
        weight.append(
            (prop['atk_green'] / prop['baseAtk']) * 100 / WEIGHT_MAP['百分比攻击力']
        )
    elif '生命' in attr:
        weight.append(
            (prop['hp_green'] / prop['baseHp']) * 100 / WEIGHT_MAP['百分比血量']
        )
    elif '防御' in attr:
        weight.append(
            (prop['def_green'] / prop['baseDef']) * 100 / WEIGHT_MAP['百分比防御力']
        )
    elif '精通' in attr:
        weight.append(prop['elementalMastery'] / WEIGHT_MAP['元素精通'])
    elif '充能' in attr:
        weight.append(prop['energyRecharge'] * 100 / WEIGHT_MAP['元素充能效率'])
    elif '物伤' in attr:
        weight.append(prop['physicalDmgBonus'] * 100 / WEIGHT_MAP['物理伤害加成'])
    elif '伤' in attr:
        weight.append(prop['dmgBonus'] * 100 / WEIGHT_MAP['元素伤害加成'])
    elif '治疗' in attr:
        weight.append(prop['healBonus'] * 100 / WEIGHT_MAP['治疗加成'])
    elif '暴击' in attr:
        weight.append(prop['critRate'] * 100 / WEIGHT_MAP['暴击率'])
        weight.append(prop['critDmg'] * 100 / WEIGHT_MAP['暴击伤害'])
    return weight


async def get_weight(prop: dict, attr: str) -> List[float]:
    weight = []
    if '/' in attr:
        attr_list = attr.split('/')
    else:
        attr_list = [attr]
    for i in attr_list:
        weight.extend(await get_weight_temp(prop, i))

    return weight


BLUE = "#0000ff"
lu_point = (23, 45)
rd_point = (927, 495)
X_D = rd_point[0] - lu_point[0]
Y_D = rd_point[1] - lu_point[1]
gs_font_22 = genshin_font_origin(22)
frame_img = Image.open(TEXT_PATH / 'frame.png')
point_img = Image.open(TEXT_PATH / 'point.png')


async def draw_char_curve_data(
    char_name: str, raw_data: dict
) -> Tuple[Image.Image, int]:
    # 如果曲线列表里不存在该角色,则返回空白图片
    if char_name not in CHAR_CURVE or CHAR_CURVE[char_name] == {}:
        return Image.new('RGBA', (950, 1)), 0

    # 获得面板属性
    if 'avatarFightProp' in raw_data:
        fight_prop = raw_data['avatarFightProp']
    else:
        fight_prop = raw_data
    fight_prop['atk_green'] = fight_prop['atk'] - fight_prop['baseAtk']
    fight_prop['def_green'] = fight_prop['def'] - fight_prop['baseDef']
    fight_prop['hp_green'] = fight_prop['hp'] - fight_prop['baseHp']

    img = Image.open(TEXT_PATH / 'curve_bg.png')
    img_draw = ImageDraw.Draw(img)

    # 初始化X_MAX和Y_MAX值
    X_MAX = 0
    Y_MAX = 0
    wight_point_dict: dict = {}
    line_points_dict: dict = {}
    wight_temp_dict: dict = {}
    # 遍历曲线列表,根据函数获得权重
    for col in CHAR_CURVE[char_name]:
        wight_temp = await get_weight(fight_prop, CHAR_CURVE[char_name][col])
        wight_temp_dict[CHAR_CURVE[char_name][col]] = wight_temp
        # 对单个属性的权重列表进行遍历
        for i in wight_temp:
            # 确定X_MAX值
            if i >= X_MAX:
                X_MAX = i
            # 确定Y_MAX值
            for j in CURVE[col]:
                if j >= Y_MAX:
                    Y_MAX = j

    # 增加Y_MAX和X_MAX的值
    X_MAX = X_MAX + 15
    Y_MAX = Y_MAX + 0.002

    # 遍历曲线列表,COL为列名,这一步拿到所有曲线的点,和所有权重的点
    for col_index, col in enumerate(CHAR_CURVE[char_name]):
        line_points = []
        # 确定颜色
        for m in COLOR_MAP:
            if m in CHAR_CURVE[char_name][col]:
                color = COLOR_MAP[m]
                break
        else:
            color = '#ffffff'

        for index, i in enumerate(CURVE[col]):
            if index >= X_MAX:
                break
            x, y = (X_D / X_MAX) * index + lu_point[0], (
                Y_D - (Y_D / Y_MAX) * i
            ) + lu_point[1]
            line_points.append((x, y))
        line_points_dict[color] = line_points

        for wight in wight_temp_dict[CHAR_CURVE[char_name][col]]:
            w_x = (wight / X_MAX) * X_D + lu_point[0]
            w_y = line_points[int(wight)][1]
            if CHAR_CURVE[char_name][col] not in wight_point_dict:
                wight_point_dict[CHAR_CURVE[char_name][col]] = {
                    'color': color,
                    'point': [(w_x, w_y)],
                }
            else:
                wight_point_dict[CHAR_CURVE[char_name][col]]['point'].append(
                    (w_x, w_y)
                )

        # 绘制右上角方块和文字
        img_draw.rectangle(
            ((710, 65 + col_index * 30), (750, 85 + col_index * 30)),
            fill=color,
        )
        img_draw.text(
            (762, 75 + col_index * 30),
            f'{CHAR_CURVE[char_name][col]}',
            color,
            gs_font_22,
            'lm',
        )

    # 根据素材画曲线
    for c in line_points_dict:
        img_draw.line(line_points_dict[c], width=6, fill=c, joint='curve')

    for attr in wight_point_dict:
        attr_str = attr.replace('收益', '')
        if attr_str == '暴击':
            attr_list = ['暴击', '爆伤']
        else:
            attr_list = attr_str.split('/')
        for index, point in enumerate(wight_point_dict[attr]['point']):
            img_draw.text(
                (point[0], 512),
                f'{int((point[0] - lu_point[0])/X_D * X_MAX)}',
                wight_point_dict[attr]['color'],
                gs_font_22,
                'mm',
            )
            img_draw.text(
                (point[0], 535),
                attr_list[index],
                wight_point_dict[attr]['color'],
                gs_font_22,
                'mm',
            )
            img.paste(
                point_img, (int(point[0] - 15), int(point[1] - 15)), point_img
            )
            img_draw.line(
                [point, (point[0], rd_point[1])], width=1, fill=(255, 255, 255)
            )

    img.paste(frame_img, (0, 0), frame_img)
    return img, 550
