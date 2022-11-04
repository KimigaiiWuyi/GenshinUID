import re
import json
import asyncio
from copy import deepcopy
from typing import Dict, List, Tuple, Union, Optional

from nonebot.log import logger

from .mono.Character import Character
from .draw_char_card import draw_char_img
from ..utils.message.error_reply import CHAR_HINT
from ..utils.enka_api.enka_to_card import draw_enka_card
from .etc.prop_calc import get_base_prop, get_simple_card_prop
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

    # 判断是否开启成长曲线或最佳, 并且去除
    is_curve = False
    is_best = False
    if '成长曲线' in msg or '曲线' in msg:
        is_curve = True
        msg = msg.replace('成长曲线', '').replace('曲线', '')
    elif '最佳' in msg:
        is_best = True
        msg = msg.replace('最佳', '')

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

    '''
    if is_best:
        char_data = await get_best_char(char_data, uid)
    '''

    im = await draw_char_img(
        char_data, weapon, weapon_affix, talent_num, url, is_curve
    )
    logger.info('[查询角色] 绘图完成,等待发送...')
    return im


async def get_best_char(char_data: Dict, uid: str) -> Dict:
    # 设定初始值
    char_level = int(char_data['avatarLevel'])
    char_name = char_data['avatarName']
    fight_prop = await get_base_prop(char_data, char_name, char_level)

    # 开始
    logger.info(f'[查找最佳圣遗物] UID:{uid}开始进行迭代...')
    best = []
    artifacts_repo = await get_artifacts_repo(uid)
    num = 0
    TASKS = []
    for flower in artifacts_repo['flower']:
        for plume in artifacts_repo['plume']:
            for sands in artifacts_repo['sands']:
                for goblet in artifacts_repo['goblet']:
                    for circlet in artifacts_repo['circlet']:
                        char_data['equipList'] = [
                            flower,
                            plume,
                            sands,
                            goblet,
                            circlet,
                        ]
                        char_data = await get_simple_card_prop(
                            char_data, fight_prop
                        )
                        num += 1
                        TASKS.append(
                            await get_single_percent(
                                deepcopy(char_data), uid, num, best
                            )
                        )
                        break
                        # await get_single_percent(char, uid, num, best)
    asyncio.gather(*TASKS)
    best.sort(key=lambda x: (-x['percent']))
    logger.info(f'[查找最佳圣遗物] UID:{uid}完成!毕业度为{best[0]["percent"]}')
    return char_data


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
