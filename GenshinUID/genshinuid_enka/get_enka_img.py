import re
import json
from typing import Dict, List, Tuple, Union, Optional

from PIL import Image
from gsuid_core.logger import logger
from gsuid_core.utils.error_reply import CHAR_HINT

from .to_card import draw_enka_card
from .draw_char_card import draw_char_img
from .draw_group_dmg import draw_group_dmg_img
from .mono.Character import Character, get_char
from ..utils.map.GS_MAP_PATH import avatarName2Element
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..utils.map.name_covert import (
    name_to_avatar_id,
    alias_to_char_name,
    avatarId_to_enName,
)

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


async def get_full_char(raw_mes: str, uid: str) -> Union[str, Dict]:
    # 获取角色名
    msg = ' '.join(re.findall('[\u4e00-\u9fa5]+', raw_mes))
    _args = await get_char_args(msg, uid)
    if isinstance(_args, Tuple):
        char = await get_char(*_args)
        if isinstance(char, str):
            return char
        return char.card_prop
    else:
        return _args


async def draw_enka_img(
    raw_mes: str, uid: str, url: Optional[str]
) -> Union[str, Tuple[Union[bytes, Image.Image, str], Optional[bytes]]]:
    # 获取角色名
    msg = ' '.join(re.findall('[\u4e00-\u9fa5]+', raw_mes))
    # msg = raw_mes.strip()

    # 判断是否开启成长曲线或最佳, 并且去除
    is_curve = False
    is_group = False
    if '成长曲线' in msg or '曲线' in msg:
        is_curve = True
        msg = msg.replace('成长曲线', '').replace('曲线', '')
    if '队伍' in msg or '队伍伤害' in msg:
        is_group = True
        msg = msg.replace('队伍', '').replace('伤害', '').strip()

    if '展柜角色' in msg:
        sc = await get_showcase(uid)
        if isinstance(sc, str):
            return sc
        return sc, None

    msg_list = msg.split(' ')
    char_list = []
    for msg in msg_list:
        _args = await get_char_args(msg, uid)
        if isinstance(_args, str):
            return _args
        else:
            if isinstance(_args[0], str):
                return _args[0]
        if is_group:
            char = await get_char(*_args)
            char_list.append(char)
        else:
            break
    else:
        im = await draw_group_dmg_img(uid, char_list)
        if isinstance(im, str):
            return im
        return im, None

    char = await get_char(*_args)

    if isinstance(char, str):
        logger.info('[查询角色] 绘图失败, 替换的武器不正确!')
        return char

    im = await draw_char_img(char, url, is_curve)
    logger.info('[查询角色] 绘图完成,等待发送...')
    return im


async def get_char_data(
    uid: str, char_name: str, enable_self: bool = True
) -> Union[Dict, str]:
    player_path = PLAYER_PATH / str(uid)
    SELF_PATH = player_path / 'SELF'
    if '旅行者' in char_name:
        char_name = '旅行者'
    else:
        char_name = await alias_to_char_name(char_name)

    char_path = player_path / f'{char_name}.json'
    char_self_path = SELF_PATH / f'{char_name}.json'

    if char_path.exists():
        path = char_path
    elif enable_self and char_self_path.exists():
        path = char_self_path
    else:
        return CHAR_HINT.format(char_name)

    with open(path, 'r', encoding='utf8') as fp:
        char_data = json.load(fp)
    return char_data


async def get_showcase(uid: str) -> Union[bytes, str]:
    player_path = PLAYER_PATH / str(uid)
    char_file_list = player_path.glob('*')
    char_list = []
    for i in char_file_list:
        file_name = i.name
        if '\u4e00' <= file_name[0] <= '\u9fff':
            char_list.append(file_name.split('.')[0])
    if char_list == []:
        return '您还没有已缓存的角色噢~\n请先使用[强制刷新]命令缓存~'
    img = await draw_enka_card(uid=uid, char_list=char_list)
    return img


async def change_equip(
    uid: str, char_data: Dict, part: str, s: str, i: int
) -> Dict:
    char_name = part.replace(part[-1], '')
    fake_data = await get_char_data(uid, char_name)
    if isinstance(fake_data, str):
        return {}
    for equip in fake_data['equipList']:
        if equip['aritifactPieceName'] == s:
            char_data['equipList'][i] = equip
            break
    return char_data


async def get_char_args(
    msg: str, uid: str
) -> Union[Tuple[Dict, Optional[str], Optional[int], Optional[int]], str]:
    # 可能进来的值
    # 六命公子带天空之卷换可莉圣遗物换刻晴羽换可莉花
    # 六命公子带天空之卷换刻晴羽
    # 公子换刻晴羽
    fake_name = ''
    talent_num = None
    char_data = {}
    weapon, weapon_affix = None, None

    msg = msg.replace('带', '换').replace('拿', '换')

    # 公子带天空之卷换可莉圣遗物
    msg_list = msg.split('换')
    for index, part in enumerate(msg_list):
        # 判断主体
        if index == 0:
            fake_name, talent_num = await get_fake_char_str(part)
            # 判断是否开启fake_char
            if '圣遗物' in msg:
                char_data = await get_fake_char_data(char_data, fake_name, uid)
            else:
                char_data = await get_char_data(uid, fake_name)
            if isinstance(char_data, str):
                return char_data
            continue

        if '圣遗物' in part:
            fake_data = await get_char_data(uid, part.replace('圣遗物', ''))
            if isinstance(fake_data, str):
                return fake_data
            char_data = await get_fake_char_data(fake_data, fake_name, uid)
            if isinstance(char_data, str):
                return char_data
        else:
            for i, s in enumerate(['生之花', '死之羽', '时之沙', '空之杯', '理之冠']):
                if '赤沙' in part:
                    continue
                if part[-1] == s[-1]:
                    if isinstance(char_data, str):
                        return char_data
                    char_data = await change_equip(uid, char_data, part, s, i)
                    if not char_data:
                        return '要替换的部件不存在噢~'
                    break
            else:
                weapon, weapon_affix = await get_fake_weapon_str(part)

    return char_data, weapon, weapon_affix, talent_num


async def get_single_percent(char_data: Dict, uid: str, num: int, best: List):
    char = Character(char_data)
    await char.init_prop()
    percent = float(char.percent.replace('%', ''))
    logger.info(f'[查找最佳圣遗物] UID:{uid}第{num}次迭代...毕业度为{percent}!')
    best.append({'percent': percent, 'char_data': char.card_prop})


async def get_artifacts_repo(uid: str) -> Dict[str, List[Dict]]:
    artifacts_repo = {
        'flower': [],
        'plume': [],
        'sands': [],
        'goblet': [],
        'circlet': [],
    }
    logger.info(f'[建立圣遗物仓库] UID:{uid}开始...')
    # 开始查找全部角色
    uid_fold = PLAYER_PATH / str(uid)
    char_file_list = uid_fold.glob('*')
    for i in char_file_list:
        if '\u4e00' <= i.name[0] <= '\u9fff':
            with open(uid_fold / f'{i.name}', 'r', encoding='UTF-8') as f:
                raw_data = json.load(f)
            for equip in raw_data['equipList']:
                if equip not in artifacts_repo[equip['aritifactSetPiece']]:
                    artifacts_repo[equip['aritifactSetPiece']].append(equip)
    logger.info(
        f'[建立圣遗物仓库] UID:{uid}完成!共计\
          {len(artifacts_repo["flower"])},\
          {len(artifacts_repo["plume"])},\
          {len(artifacts_repo["sands"])},\
          {len(artifacts_repo["goblet"])},\
          {len(artifacts_repo["circlet"])}个圣遗物!'
    )
    return artifacts_repo


async def get_fake_char_data(
    char_data: Dict, fake_name: str, uid: str
) -> Union[Dict, str]:
    fake_name = await alias_to_char_name(fake_name)
    original_data = await get_char_data(uid, fake_name)
    if isinstance(original_data, Dict):
        char_data['weaponInfo'] = original_data['weaponInfo']
        char_data['talentList'] = original_data['talentList']
    char_data['avatarName'] = fake_name
    char_data['avatarId'] = await name_to_avatar_id(fake_name)
    en_name = await avatarId_to_enName(char_data['avatarId'])
    char_data['avatarEnName'] = en_name
    if fake_name in avatarName2Element:
        char_data['avatarElement'] = avatarName2Element[fake_name]
    else:
        return '要查询的角色不存在...'
    char_data['avatarLevel'] = '90'
    char_data['avatarSkill'] = [
        {'skillLevel': 10, 'skillIcon': 'Skill_A_02'},
        {'skillLevel': 10, 'skillIcon': f'Skill_S_{en_name}_01'},
        {'skillLevel': 10, 'skillIcon': f'Skill_E_{en_name}_01'},
    ]
    return char_data


async def get_fake_char_str(char_name: str) -> Tuple[str, Optional[int]]:
    '''
    获取一个角色信息

    '''
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
