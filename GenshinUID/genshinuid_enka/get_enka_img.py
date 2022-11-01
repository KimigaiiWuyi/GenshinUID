import re
import json
from typing import Tuple, Union, Optional

from nonebot.log import logger

from .draw_char_card import draw_char_img
from ..utils.message.error_reply import CHAR_HINT
from ..utils.enka_api.enka_to_card import draw_enka_card
from ..utils.alias.alias_to_char_name import alias_to_char_name
from ..utils.download_resource.RESOURCE_PATH import PLAYER_PATH

CONVERT_TO_INT = {
    '零': 0,
    '一': 1,
    '二': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '满': 6,
}


async def draw_enka_img(
    raw_mes: str, uid: str, url: Optional[str]
) -> Union[str, Tuple[Union[bytes, str], Optional[bytes]]]:
    # 获取角色名
    msg = ''.join(re.findall('[\u4e00-\u9fa5]', raw_mes))
    is_curve = False
    if '成长曲线' in msg or '曲线' in msg:
        is_curve = True
        msg = msg.replace('成长曲线', '').replace('曲线', '')
    msg_list = msg.split('换')
    char_name = msg_list[0]
    talent_num = None
    weapon = None
    weapon_affix = None
    if '命' in char_name and char_name[0] in CONVERT_TO_INT:
        talent_num = CONVERT_TO_INT[char_name[0]]
        char_name = char_name[2:]
    if len(msg_list) > 1:
        if (
            '精' in msg_list[1]
            and msg_list[1][1] != '六'
            and msg_list[1][1] != '零'
            and msg_list[1][1] in CONVERT_TO_INT
        ):
            weapon_affix = CONVERT_TO_INT[msg_list[1][1]]
            weapon = msg_list[1][2:]
        else:
            weapon = msg_list[1]

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

    im = await draw_char_img(
        char_data, weapon, weapon_affix, talent_num, url, is_curve
    )
    logger.info('[查询角色] 绘图完成,等待发送...')
    return im
