from pathlib import Path
from typing import Dict, List, Union

from PIL import Image, ImageDraw

from .mono.Enemy import Enemy
from .mono.Fight import Fight
from .etc.etc import TEXT_PATH
from .mono.Character import Character
from .mono.SEQ import ALL_SEQ, SEQ_ARG
from ..utils.download_resource.RESOURCE_PATH import CHAR_PATH
from ..utils.draw_image_tools.send_image_tool import convert_img
from ..utils.alias.avatarId_and_name_covert import name_to_avatar_id
from ..utils.draw_image_tools.draw_image_tool import (
    get_color_bg,
    draw_pic_with_ring,
)
from ..utils.genshin_fonts.genshin_fonts import (
    gs_font_26,
    gs_font_32,
    gs_font_44,
    gs_font_50,
)

TD_PATH = TEXT_PATH / 'team_dmg'

team_title = Image.open(TD_PATH / 'team_title.png')
action_title = Image.open(TD_PATH / 'action_title.png')


async def get_group_dmg_data(
    char_list: List[Character],
) -> Union[Dict[float, Dict], str]:
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

    dmg_data: Dict[float, Dict] = await fight.update_dmg()
    return dmg_data


def _f(value: float) -> str:
    return '{:.2f}'.format(value)


async def draw_group_dmg_img(
    uid: str, char_list: List[Character]
) -> Union[bytes, str]:
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

    # 初始化一些数值
    all_avgdmg = 0
    all_critdmg = 0
    ac_len = len(dmg_data)
    all_time = list(dmg_data.keys())[-1]
    avg_dps = all_avgdmg / all_time

    # 粘贴动作序列
    for index, time in enumerate(dmg_data):
        _data = dmg_data[time]
        char_id = await name_to_avatar_id(_data['char'])
        char_pic = Image.open(CHAR_PATH / f'{char_id}.png')
        char_img = await draw_pic_with_ring(char_pic, 50)

        bar = Image.open(TD_PATH / 'dmg_bar.png')

        bar.paste(char_img, (100, 10), char_img)

        bar_draw = ImageDraw.Draw(bar)

        # Action
        bar_draw.text((190, 35), _data['action'], 'white', gs_font_32, 'lm')
        # 具体伤害
        _dmg = _f(_data['avg_dmg'])
        bar_draw.text((600, 35), _dmg, 'white', gs_font_32, 'lm')

        img.paste(bar, (0, 1030 + index * bar_offset), bar)

        all_avgdmg += _data['avg_dmg']
        all_critdmg += _data['crit_dmg']

    img_draw = ImageDraw.Draw(img)
    # UID
    img_draw.text((395, 98), f'UID{uid}', 'white', gs_font_50, 'lm')

    # 标题
    img_draw.text((396, 200), '总期望伤害', 'white', gs_font_26, 'lm')
    img_draw.text((656, 200), '总暴击伤害', 'white', gs_font_26, 'lm')
    img_draw.text((396, 297), '平均DPS', 'white', gs_font_26, 'lm')
    img_draw.text((656, 297), f'{ac_len}个动作', 'white', gs_font_26, 'lm')

    # 数值
    img_draw.text((396, 236), f'{_f(all_avgdmg)}', 'white', gs_font_44, 'lm')
    img_draw.text((656, 236), f'{_f(all_critdmg)}', 'white', gs_font_44, 'lm')
    img_draw.text((396, 333), f'{_f(avg_dps)}', 'white', gs_font_44, 'lm')
    img_draw.text((656, 333), f'{_f(all_time)}秒内', 'white', gs_font_44, 'lm')

    img = await convert_img(img)
    return img
