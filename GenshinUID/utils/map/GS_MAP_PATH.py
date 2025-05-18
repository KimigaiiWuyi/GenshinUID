from pathlib import Path
from typing import Dict, List, TypedDict

import aiofiles
from msgspec import json as msgjson
from gsuid_core.logger import logger
from gsuid_core.server import on_core_start

from ...version import Genshin_version

MAP = Path(__file__).parent / 'data'

version = Genshin_version

avatarName2Element_fileName = f'avatarName2Element_mapping_{version}.json'
weaponHash2Name_fileName = f'weaponHash2Name_mapping_{version}.json'
weaponHash2Type_fileName = f'weaponHash2Type_mapping_{version}.json'
skillId2Name_fileName = f'skillId2Name_mapping_{version}.json'
talentId2Name_fileName = f'talentId2Name_mapping_{version}.json'
avatarId2Name_fileName = f'avatarId2Name_mapping_{version}.json'
avatarId2Star_fileName = f'avatarId2Star_mapping_{version}.json'
artifact2attr_fileName = f'artifact2attr_mapping_{version}.json'
enName2Id_fileName = f'enName2AvatarID_mapping_{version}.json'
icon2Name_fileName = f'icon2Name_mapping_{version}.json'
name2Icon_fileName = f'name2Icon_mapping_{version}.json'
avatarName2Weapon_fileName = f'avatarName2Weapon_mapping_{version}.json'
monster2entry_fileName = f'monster2entry_mapping_{version}.json'
avatarId2SkillList_fileName = f'avatarId2SkillList_mapping_{version}.json'
weaponId2Name_fileName = f'weaponId2Name_mapping_{version}.json'
CharId2TalentIcon_fileName = f'CharId2TalentIcon_mapping_{version}.json'
mysData_fileName = f'mysData_{version}.json'

EXMonster_fileName = 'ExtraMonster.json'
charList_fileName = f'charList_{version}.json'
weaponList_fileName = f'weaponList_{version}.json'


class TS(TypedDict):
    Name: Dict[str, str]
    Icon: Dict[str, str]


charList: Dict[str, str] = {}
weaponList: Dict[str, str] = {}
avatarId2Name: Dict[str, str] = {}
icon2Name: Dict[str, str] = {}
artifact2attr: Dict[str, str] = {}
name2Icon: Dict[str, str] = {}
avatarName2Element: Dict[str, str] = {}
avatarName2Weapon: Dict[str, str] = {}
mysData: Dict = {}
propId2Name: Dict[str, str] = {}
Id2PropId: Dict[str, str] = {}
artifactId2Piece: Dict[str, List[str]] = {}
skillId2Name: TS = TS(Name={}, Icon={})
talentId2Name: TS = TS(Name={}, Icon={})
weaponHash2Name: Dict[str, str] = {}
weaponHash2Type: Dict[str, str] = {}
alias_data: Dict[str, List[str]] = {}
avatarId2Star_data: Dict[str, str] = {}
enName_to_avatarId_data: Dict[str, str] = {}
ex_monster_data: Dict[str, Dict] = {}
monster2entry_data: Dict[str, Dict] = {}
avatarId2SkillList_data: Dict[str, Dict[str, str]] = {}
weaponId2Name_data: Dict[str, str] = {}
CharId2TalentIcon_data: Dict[str, List[str]] = {}


@on_core_start
async def load_map():
    global charList, weaponList, avatarId2Name, icon2Name
    global artifact2attr, name2Icon, avatarName2Element
    global avatarName2Weapon, mysData, talentId2Name
    global propId2Name, Id2PropId, artifactId2Piece, skillId2Name
    global weaponHash2Name, weaponHash2Type, alias_data, avatarId2Star_data
    global enName_to_avatarId_data, ex_monster_data, monster2entry_data
    global avatarId2SkillList_data, weaponId2Name_data, CharId2TalentIcon_data
    logger.info('[GenshinUID MAP] 正在加载资源文件...')

    try:
        async with aiofiles.open(
            MAP / charList_fileName, 'r', encoding='UTF-8'
        ) as f:
            charList = msgjson.decode(await f.read(), type=Dict)

        async with aiofiles.open(
            MAP / weaponList_fileName, 'r', encoding='UTF-8'
        ) as f:
            weaponList = msgjson.decode(await f.read(), type=Dict)

        async with aiofiles.open(
            MAP / avatarId2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            avatarId2Name = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / icon2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            icon2Name = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / artifact2attr_fileName, 'r', encoding='UTF-8'
        ) as f:
            artifact2attr = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / icon2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            icon2Name = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / name2Icon_fileName, 'r', encoding='UTF-8'
        ) as f:
            name2Icon = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / 'propId2Name_mapping.json', 'r', encoding='UTF-8'
        ) as f:
            propId2Name = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / 'Id2propId_mapping.json', 'r', encoding='UTF-8'
        ) as f:
            Id2PropId = msgjson.decode(await f.read(), type=Dict[str, str])

        async with aiofiles.open(
            MAP / weaponHash2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            weaponHash2Name = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / weaponHash2Type_fileName, 'r', encoding='UTF-8'
        ) as f:
            weaponHash2Type = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / 'artifactId2Piece_mapping.json', 'r', encoding='UTF-8'
        ) as f:
            artifactId2Piece = msgjson.decode(
                await f.read(), type=Dict[str, List[str]]
            )

        async with aiofiles.open(
            MAP / skillId2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            skillId2Name = msgjson.decode(await f.read(), type=TS)

        async with aiofiles.open(
            MAP / talentId2Name_fileName, 'r', encoding='UTF-8'
        ) as f:
            talentId2Name = msgjson.decode(await f.read(), type=TS)

        async with aiofiles.open(
            MAP / avatarName2Element_fileName, 'r', encoding='UTF-8'
        ) as f:
            avatarName2Element = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / avatarName2Weapon_fileName, 'r', encoding='UTF-8'
        ) as f:
            avatarName2Weapon = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / 'char_alias.json', 'r', encoding='UTF-8'
        ) as f:
            alias_data = msgjson.decode(
                await f.read(), type=Dict[str, List[str]]
            )

        async with aiofiles.open(
            MAP / avatarId2Star_fileName, 'r', encoding='utf8'
        ) as f:
            avatarId2Star_data = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / enName2Id_fileName, 'r', encoding='utf8'
        ) as f:
            enName_to_avatarId_data = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / EXMonster_fileName, 'r', encoding='utf8'
        ) as f:
            ex_monster_data = msgjson.decode(
                await f.read(), type=Dict[str, Dict]
            )

        async with aiofiles.open(
            MAP / monster2entry_fileName, 'r', encoding='utf8'
        ) as f:
            monster2entry_data = msgjson.decode(
                await f.read(), type=Dict[str, Dict]
            )

        async with aiofiles.open(
            MAP / avatarId2SkillList_fileName, 'r', encoding='utf8'
        ) as f:
            avatarId2SkillList_data = msgjson.decode(
                await f.read(), type=Dict[str, Dict[str, str]]
            )

        async with aiofiles.open(
            MAP / weaponId2Name_fileName, 'r', encoding='utf8'
        ) as f:
            weaponId2Name_data = msgjson.decode(
                await f.read(), type=Dict[str, str]
            )

        async with aiofiles.open(
            MAP / mysData_fileName, 'r', encoding='utf8'
        ) as f:
            mysData = msgjson.decode(await f.read(), type=Dict)

        async with aiofiles.open(
            MAP / CharId2TalentIcon_fileName, 'r', encoding='utf8'
        ) as f:
            CharId2TalentIcon_data = msgjson.decode(
                await f.read(), type=Dict[str, List[str]]
            )
        logger.success('[GenshinUID MAP] 资源文件加载完成')
    except FileNotFoundError:
        logger.error('[GenshinUID] 未找到对应版本的映射文件')
