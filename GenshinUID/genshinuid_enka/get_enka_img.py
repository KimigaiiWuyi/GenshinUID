import re
import json
from typing import Dict, Tuple, Union, Optional

from nonebot.log import logger

from .draw_char_card import draw_char_img
from ..utils.message.error_reply import CHAR_HINT
from ..utils.enka_api.enka_to_card import draw_enka_card
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.alias.enName_to_avatarId import avatarId_to_enName
from ..utils.download_resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.enka_api.map.GS_MAP_PATH import avatarName2Element
from ..utils.alias.avatarId_and_name_covert import name_to_avatar_id

CHAR_TO_INT = {
    '零': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '满': 6,
}

WEAPON_TO_INT = {
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '满': 5,
}


async def draw_enka_img(
    raw_mes: str, uid: str, url: Optional[str]
) -> Union[str, Tuple[Union[bytes, str], Optional[bytes]]]:
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))

    # 判断是否开启去成长曲线, 并且去除
    is_curve = False
    if '成长曲线' in msg or '曲线' in msg:
        is_curve = True
        msg = msg.replace('成长曲线', '').replace('曲线', '')

    # 以 带 作为分割
    fake_char_name = ''
    if '带' in msg and '换' in msg:
        # 公子带天空之卷换可莉圣遗物
        msg_list = msg.split('带')
        fake_char_name, talent_num = await get_fake_char_str(msg_list[0])
        msg_list = msg_list[1].split('换')
        weapon, weapon_affix = await get_fake_weapon_str(msg_list[0])
        char_name, _ = await get_fake_char_str(msg_list[1].replace('圣遗物', ''))
    else:
        # 以 换 作为分割
        msg = msg.replace('带', '换')
        msg_list = msg.split('换')
        char_name, talent_num = await get_fake_char_str(msg_list[0])
        if len(msg_list) > 1:
            weapon, weapon_affix = await get_fake_weapon_str(msg_list[1])
        else:
            weapon, weapon_affix = None, None

    player_path = PLAYER_PATH / str(uid)
    if char_name == '展柜角色':
        char_file_list = player_path.glob('*')
        char_list = []
        for i in char_file_list:
            file_name = i.name
            if '\u4e00' <= file_name[0] <= '\u9fff':
                char_list.append(file_name.split('.')[0])
        img = await draw_enka_card(uid=uid, char_list=char_list)
        return img, None
    else:
        if '旅行者' in char_name:
            char_name = '旅行者'
        else:
            char_name = await alias_to_char_name(char_name)
        char_path = player_path / f'{char_name}.json'
        if char_path.exists():
            with open(char_path, 'r', encoding='utf8') as fp:
                char_data = json.load(fp)
        else:
            return CHAR_HINT.format(char_name)

    if fake_char_name:
        char_data = await get_fake_char_data(char_data, fake_char_name)

    im = await draw_char_img(
        char_data, weapon, weapon_affix, talent_num, url, is_curve
    )
    logger.info('[查询角色] 绘图完成,等待发送...')
    return im


async def get_fake_char_data(char_data: Dict, fake_name: str) -> Dict:
    fake_name = await alias_to_char_name(fake_name)
    char_data['avatarName'] = fake_name
    char_data['avatarId'] = await name_to_avatar_id(fake_name)
    en_name = await avatarId_to_enName(char_data['avatarId'])
    char_data['avatarElement'] = avatarName2Element[fake_name]
    char_data['avatarLevel'] = '90'
    char_data['avatarSkill'] = [
        {'skillLevel': 10, 'skillIcon': 'Skill_A_02'},
        {'skillLevel': 10, 'skillIcon': f'Skill_S_{en_name}_01'},
        {'skillLevel': 10, 'skillIcon': f'Skill_E_{en_name}_01'},
    ]
    return char_data


async def get_fake_char_str(char_name: str) -> Tuple[str, Optional[int]]:
    talent_num = None
    if '命' in char_name and char_name[0] in CHAR_TO_INT:
        talent_num = CHAR_TO_INT[char_name[0]]
        char_name = char_name[2:]
    return char_name, talent_num


async def get_fake_weapon_str(msg: str) -> Tuple[str, Optional[int]]:
    weapon_affix = None
    if '精' in msg and msg[1] in WEAPON_TO_INT:
        weapon_affix = WEAPON_TO_INT[msg[1]]
        weapon = msg[2:]
    else:
        weapon = msg
    return weapon, weapon_affix
