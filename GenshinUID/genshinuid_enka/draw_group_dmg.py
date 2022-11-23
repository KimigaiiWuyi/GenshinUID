from typing import Dict, List, Union

from .mono.Enemy import Enemy
from .mono.Fight import Fight
from .mono.Character import Character
from .mono.SEQ import ALL_SEQ, SEQ_ARG


async def draw_group_dmg_img(char_list: List[Character]) -> Union[bytes, str]:
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

    return ''
