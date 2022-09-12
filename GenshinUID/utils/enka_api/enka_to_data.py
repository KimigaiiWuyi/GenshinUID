import json
import time
from pathlib import Path
from typing import Union, Optional

from ...version import Genshin_version
from .get_enka_data import get_enka_info
from ..minigg_api.get_minigg_data import get_weapon_info
from ..download_resource.RESOURCE_PATH import PLAYER_PATH

R_PATH = Path(__file__).parent
MAP_PATH = R_PATH / 'map'

version = Genshin_version

PROP_ATTR_MAP = {
    'Anemo': '44',
    'Cryo': '46',
    'Dendro': '43',
    'Electro': '41',
    'Geo': '45',
    'Hydro': '42',
    'Pyro': '40',
}

avatarName2Element_fileName = f'avatarName2Element_mapping_{version}.json'
weaponHash2Name_fileName = f'weaponHash2Name_mapping_{version}.json'
weaponHash2Type_fileName = f'weaponHash2Type_mapping_{version}.json'
skillId2Name_fileName = f'skillId2Name_mapping_{version}.json'
talentId2Name_fileName = f'talentId2Name_mapping_{version}.json'
avatarId2Name_fileName = f'avatarId2Name_mapping_{version}.json'

artifact2attr_fileName = f'artifact2attr_mapping_{version}.json'
icon2Name_fileName = f'icon2Name_mapping_{version}.json'

with open(MAP_PATH / avatarId2Name_fileName, "r", encoding='UTF-8') as f:
    avatarId2Name = json.load(f)

with open(MAP_PATH / icon2Name_fileName, "r", encoding='UTF-8') as f:
    icon2Name = json.load(f)

with open(MAP_PATH / artifact2attr_fileName, "r", encoding='UTF-8') as f:
    artifact2attr = json.load(f)

with open(MAP_PATH / 'propId2Name_mapping.json', "r", encoding='UTF-8') as f:
    propId2Name = json.load(f)

with open(MAP_PATH / weaponHash2Name_fileName, "r", encoding='UTF-8') as f:
    weaponHash2Name = json.load(f)

with open(MAP_PATH / weaponHash2Type_fileName, "r", encoding='UTF-8') as f:
    weaponHash2Type = json.load(f)

with open(
    MAP_PATH / 'artifactId2Piece_mapping.json', "r", encoding='UTF-8'
) as f:
    artifactId2Piece = json.load(f)

with open(MAP_PATH / skillId2Name_fileName, "r", encoding='UTF-8') as f:
    skillId2Name = json.load(f)

with open(MAP_PATH / talentId2Name_fileName, "r", encoding='UTF-8') as f:
    talentId2Name = json.load(f)

with open(MAP_PATH / avatarName2Element_fileName, 'r', encoding='UTF-8') as f:
    avatarName2Element = json.load(f)


async def enka_to_data(
    uid: str, enka_data: Optional[dict] = None
) -> Union[dict, str]:
    """
    :说明:
      访问enkaAPI并转换为genshinUID的数据Json。
    :参数:
      * ``uid: str``: 玩家uid。
      * ``enka_data: Optional[dict] = None``: 来自enka的dict, 可留空。
    :返回:
      * ``刷新完成提示语: str``: 包含刷新成功的角色列表。
    """
    if enka_data:
        pass
    else:
        enka_data = await get_enka_info(uid)
    if isinstance(enka_data, str):
        return enka_data
    if isinstance(enka_data, dict):
        if 'playerInfo' not in enka_data:
            im = (
                '服务器正在维护或者关闭中...\n'
                f'检查https://enka.network/u/{uid}是否可以访问\n'
                '如可以访问,尝试[切换api]或上报Bug!'
            )
            return im
    elif enka_data is None:
        return {}

    now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    playerInfo = enka_data['playerInfo']
    path = PLAYER_PATH / str(uid)
    path.mkdir(parents=True, exist_ok=True)
    with open(
        path / '{}.json'.format(str(uid)), 'w', encoding='UTF-8'
    ) as file:
        json.dump(playerInfo, file, ensure_ascii=False)
    with open(path / 'rawData.json', 'w', encoding='UTF-8') as file:
        json.dump(enka_data, file, ensure_ascii=False)

    if 'avatarInfoList' not in enka_data:
        return f'UID{uid}刷新失败！未打开角色展柜!'

    char_name_list = []
    for char in enka_data['avatarInfoList']:
        # 处理基本信息
        char_data = {}
        avatarId = char['avatarId']
        char_data['playerUid'] = str(uid)
        char_data['playerName'] = enka_data['playerInfo']['nickname']
        char_data['avatarId'] = avatarId
        avatarName = avatarId2Name[str(char['avatarId'])]
        char_data['avatarName'] = avatarId2Name[str(char['avatarId'])]
        char_name_list.append(char_data['avatarName'])
        char_data['avatarFetter'] = char['fetterInfo']['expLevel']
        char_data['avatarLevel'] = char['propMap']['4001']['val']

        try:
            char_data['avatarElement'] = avatarName2Element[
                char_data['avatarName']
            ]
        except KeyError:
            check = skillId2Name['Name'][
                str(list(char['skillLevelMap'].keys())[2])
            ]
            if '风' in check:
                char_data['avatarElement'] = 'Anemo'
            elif '雷' in check:
                char_data['avatarElement'] = 'Electro'
            elif '岩' in check:
                char_data['avatarElement'] = 'Geo'
            elif '草' in check:
                char_data['avatarElement'] = 'Dendro'
            elif '冰' in check:
                char_data['avatarElement'] = 'Cryo'
            elif '水' in check:
                char_data['avatarElement'] = 'Hydro'
            else:
                char_data['avatarElement'] = 'Pyro'

        char_data['dataTime'] = now

        char_data['avatarSkill'] = []
        # 处理天赋
        for skill in char['skillLevelMap']:
            skill_temp = {}
            skill_temp['skillId'] = skill
            skill_temp['skillName'] = skillId2Name['Name'][
                skill_temp['skillId']
            ]
            skill_temp['skillLevel'] = char['skillLevelMap'][skill]
            skill_temp['skillIcon'] = skillId2Name['Icon'][
                skill_temp['skillId']
            ]
            char_data['avatarSkill'].append(skill_temp)

        if char_data['avatarName'] in ['神里绫华', '安柏']:
            char_data['avatarSkill'][0], char_data['avatarSkill'][-1] = (
                char_data['avatarSkill'][-1],
                char_data['avatarSkill'][0],
            )
            char_data['avatarSkill'][2], char_data['avatarSkill'][-1] = (
                char_data['avatarSkill'][-1],
                char_data['avatarSkill'][2],
            )
            char_data['avatarEnName'] = char_data['avatarSkill'][1][
                'skillIcon'
            ].split('_')[-2]
        elif char_data['avatarName'] in ['旅行者']:
            char_data['avatarSkill'][0], char_data['avatarSkill'][-1] = (
                char_data['avatarSkill'][-1],
                char_data['avatarSkill'][0],
            )
            char_data['avatarSkill'][1], char_data['avatarSkill'][-1] = (
                char_data['avatarSkill'][-1],
                char_data['avatarSkill'][1],
            )
            char_data['avatarEnName'] = str(avatarId)
        else:
            char_data['avatarEnName'] = char_data['avatarSkill'][-1][
                'skillIcon'
            ].split('_')[-2]

        # 处理命座
        talent_temp = []
        if 'talentIdList' in char:
            for index, talent in enumerate(char['talentIdList']):
                talentTemp = {}
                talentTemp['talentId'] = char['talentIdList'][index]
                talentTemp['talentName'] = talentId2Name['Name'][str(talent)]
                talentTemp['talentIcon'] = talentId2Name['Icon'][str(talent)]
                talent_temp.append(talentTemp)
        char_data['talentList'] = talent_temp

        # 处理属性
        fight_prop = {}
        # 血量
        fight_prop['hp'] = char["fightPropMap"]["2000"]
        fight_prop['baseHp'] = char["fightPropMap"]["1"]
        fight_prop['addHp'] = (
            char["fightPropMap"]["2000"] - char["fightPropMap"]["1"]
        )
        # 攻击力
        fight_prop['atk'] = char["fightPropMap"]["2001"]
        fight_prop['baseAtk'] = char["fightPropMap"]["4"]
        fight_prop['addAtk'] = (
            char["fightPropMap"]["2001"] - char["fightPropMap"]["4"]
        )
        # 防御力
        fight_prop['def'] = char["fightPropMap"]["2002"]
        fight_prop['baseDef'] = char["fightPropMap"]["7"]
        fight_prop['addDef'] = (
            char["fightPropMap"]["2002"] - char["fightPropMap"]["7"]
        )
        # 元素精通
        fight_prop['elementalMastery'] = char["fightPropMap"]["28"]
        # 暴击率
        fight_prop['critRate'] = char["fightPropMap"]["20"]
        # 暴击伤害
        fight_prop['critDmg'] = char["fightPropMap"]["22"]
        # 充能效率
        fight_prop['energyRecharge'] = char["fightPropMap"]["23"]
        # 治疗&受治疗
        fight_prop['healBonus'] = char["fightPropMap"]["26"]
        fight_prop['healedBonus'] = char["fightPropMap"]["27"]
        # 物理伤害加成 & 抗性
        fight_prop['physicalDmgSub'] = char["fightPropMap"]["29"]
        fight_prop['physicalDmgBonus'] = char["fightPropMap"]["30"]
        # 伤害加成
        fight_prop['dmgBonus'] = char["fightPropMap"][
            PROP_ATTR_MAP[char_data['avatarElement']]
        ]

        char_data['avatarFightProp'] = fight_prop

        # 处理武器
        weapon_info = {}
        weapon_data = char['equipList'][-1]
        weapon_info['itemId'] = weapon_data['itemId']
        weapon_info['nameTextMapHash'] = weapon_data['flat']['nameTextMapHash']
        weapon_info['weaponIcon'] = weapon_data['flat']['icon']
        weapon_info['weaponType'] = weaponHash2Type[
            weapon_info['nameTextMapHash']
        ]
        weapon_info['weaponName'] = weaponHash2Name[
            weapon_info['nameTextMapHash']
        ]
        weapon_info['weaponStar'] = weapon_data['flat']['rankLevel']
        # 防止未精炼
        if 'promoteLevel' in weapon_data['weapon']:
            weapon_info['promoteLevel'] = weapon_data['weapon']['promoteLevel']
        else:
            weapon_info['promoteLevel'] = 0
        weapon_info['weaponLevel'] = weapon_data['weapon']['level']
        if 'affixMap' in weapon_data['weapon']:
            weapon_info['weaponAffix'] = (
                list(weapon_data['weapon']['affixMap'].values())[0] + 1
            )
        else:
            weapon_info['weaponAffix'] = 1
        weapon_info['weaponStats'] = []
        for k in weapon_data['flat']['weaponStats']:
            weapon_prop_temp = {}
            weapon_prop_temp['appendPropId'] = k['appendPropId']
            weapon_prop_temp['statName'] = propId2Name[k['appendPropId']]
            weapon_prop_temp['statValue'] = k['statValue']
            weapon_info['weaponStats'].append(weapon_prop_temp)
        # 武器特效，须请求API
        effect_raw = await get_weapon_info(weapon_info['weaponName'])
        if 'effect' in effect_raw:
            effect = effect_raw['effect'].format(
                *effect_raw['r{}'.format(str(weapon_info['weaponAffix']))]
            )
        else:
            effect = '无特效。'
        weapon_info['weaponEffect'] = effect
        char_data['weaponInfo'] = weapon_info

        # 处理圣遗物
        artifacts_info = []
        artifacts_data = char['equipList'][:-1]
        artifact_set_list = []
        for artifact in artifacts_data:
            artifact_temp = {}
            artifact_temp['itemId'] = artifact['itemId']
            artifact_temp['nameTextMapHash'] = artifact['flat'][
                'nameTextMapHash'
            ]
            artifact_temp['icon'] = artifact['flat']['icon']
            artifact_temp['aritifactName'] = icon2Name[
                artifact['flat']['icon']
            ]
            artifact_temp['aritifactSetsName'] = artifact2attr[
                artifact_temp['aritifactName']
            ]
            artifact_set_list.append(artifact_temp['aritifactSetsName'])
            artifact_temp['aritifactSetPiece'] = artifactId2Piece[
                artifact_temp['icon'].split('_')[-1]
            ][0]
            artifact_temp['aritifactPieceName'] = artifactId2Piece[
                artifact_temp['icon'].split('_')[-1]
            ][1]

            artifact_temp['aritifactStar'] = artifact['flat']['rankLevel']
            artifact_temp['aritifactLevel'] = (
                artifact['reliquary']['level'] - 1
            )

            artifact_temp['reliquaryMainstat'] = artifact['flat'][
                'reliquaryMainstat'
            ]
            artifact_temp['reliquaryMainstat']['statName'] = propId2Name[
                artifact_temp['reliquaryMainstat']['mainPropId']
            ]

            artifact_temp['reliquarySubstats'] = artifact['flat'][
                'reliquarySubstats'
            ]
            for sub in artifact_temp['reliquarySubstats']:
                sub['statName'] = propId2Name[sub['appendPropId']]
            artifacts_info.append(artifact_temp)

        equipSetList = set(artifact_set_list)
        char_data['equipSets'] = {'type': '', 'set': ''}
        char_data['equipList'] = artifacts_info
        for equip in equipSetList:
            if artifact_set_list.count(equip) >= 4:
                char_data['equipSets']['type'] = '4'
                char_data['equipSets']['set'] = equip
                break
            elif artifact_set_list.count(equip) == 1:
                pass
            elif artifact_set_list.count(equip) >= 2:
                char_data['equipSets']['type'] += '2'
                char_data['equipSets']['set'] += equip

        with open(
            path / '{}.json'.format(avatarName), 'w', encoding='UTF-8'
        ) as file:
            json.dump(char_data, file, ensure_ascii=False)
    char_name_list_str = ','.join(char_name_list)
    return f'UID{uid}刷新完成！\n本次缓存：{char_name_list_str}'
