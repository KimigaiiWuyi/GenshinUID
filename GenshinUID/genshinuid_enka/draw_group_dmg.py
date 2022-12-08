from pathlib import Path
from typing import Dict, List, Union

from PIL import Image, ImageDraw

from .mono.Enemy import Enemy
from .mono.Fight import Fight
from .etc.etc import TEXT_PATH
from .mono.Character import Character
from .mono.SEQ import ALL_SEQ, SEQ_ARG
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.draw_image_tools.draw_image_tool import (
    get_color_bg,
    draw_pic_with_ring,
)

TD_PATH = TEXT_PATH / 'team_dmg'

team_title = Image.open(TD_PATH / 'team_title.png')
action_title = Image.open(TD_PATH / 'action_title.png')


async def get_group_dmg_data(char_list: List[Character]) -> Union[Dict, str]:
    # 获取值
    enemy = Enemy(90, 90)
    char_dict: Dict[str, Character] = {}
    char_arg = [char.char_name for char in char_list]
    for arg in SEQ_ARG:
        if sorted(char_arg) == sorted(SEQ_ARG[arg]):
            seq = ALL_SEQ[arg]
            break
    else:
        return '暂时不支持该配队...'

    for char in char_list:
        char_dict[char.char_name] = char
    fight = Fight(char_dict, enemy)
    fight.SEQ = seq

    dmg_data = await fight.update_dmg()
    return dmg_data


async def draw_group_dmg_img(char_list: List[Character]) -> Union[bytes, str]:
    # 获取数据
    dmg_data = await get_group_dmg_data(char_list)
    if isinstance(dmg_data, str):
        return dmg_data

    # 计算高度
    bar_offset = 65
    h = 900 + 120 + len(dmg_data) * bar_offset + 50

    # 开始绘图
    img = await get_color_bg(950, h, 'teamdmg_bg')
    img.paste(team_title, (0, 0), team_title)

    # 角色基本情况
    for index, char in enumerate(char_list):
        char_bg = Image.open(TD_PATH / 'char_bg.png')

        char_draw = ImageDraw.Draw(char_bg)

        # 将绘制好的角色卡贴到队伍伤害卡上
        img.paste(
            char_bg,
            (16 + 443 * (index % 2), 540 + 170 * (index // 2)),
            char_bg,
        )

    img.paste(action_title, (0, 895), action_title)
    # 粘贴动作序列
    for index, time in dmg_data:
        bar = Image.open(TD_PATH / 'dmg_bar.png')

        bar_draw = ImageDraw.Draw(bar)

        img.paste(bar, (0, 1030 + index * bar_offset), bar)

    img = await convert_img(img)
    return img
