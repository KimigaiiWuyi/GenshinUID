from typing import Any, Dict, List, TypedDict
from pathlib import Path

from msgspec import json as msgjson

from gsuid_core.i18n import t
from gsuid_core.logger import logger

from ...version import Genshin_version

MAP = Path(__file__).parent / "data"

version = Genshin_version

avatarName2Element_fileName = f"avatarName2Element_mapping_{version}.json"
weaponHash2Name_fileName = f"weaponHash2Name_mapping_{version}.json"
weaponHash2Type_fileName = f"weaponHash2Type_mapping_{version}.json"
skillId2Name_fileName = f"skillId2Name_mapping_{version}.json"
talentId2Name_fileName = f"talentId2Name_mapping_{version}.json"
avatarId2Name_fileName = f"avatarId2Name_mapping_{version}.json"
avatarId2Star_fileName = f"avatarId2Star_mapping_{version}.json"
artifact2attr_fileName = f"artifact2attr_mapping_{version}.json"
enName2Id_fileName = f"enName2AvatarID_mapping_{version}.json"
icon2Name_fileName = f"icon2Name_mapping_{version}.json"
name2Icon_fileName = f"name2Icon_mapping_{version}.json"
avatarName2Weapon_fileName = f"avatarName2Weapon_mapping_{version}.json"
monster2entry_fileName = f"monster2entry_mapping_{version}.json"
avatarId2SkillList_fileName = f"avatarId2SkillList_mapping_{version}.json"
weaponId2Name_fileName = f"weaponId2Name_mapping_{version}.json"
CharId2TalentIcon_fileName = f"CharId2TalentIcon_mapping_{version}.json"
mysData_fileName = f"mysData_{version}.json"

EXMonster_fileName = "ExtraMonster.json"
charList_fileName = f"charList_{version}.json"
weaponList_fileName = f"weaponList_{version}.json"
reliquaryList_fileName = f"reliquaryList_{version}.json"


class TS(TypedDict):
    Name: Dict[str, str]
    Icon: Dict[str, str]


charList: Dict[str, Dict[str, Any]] = {}
weaponList: Dict[str, Dict[str, Any]] = {}
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
skillId2Name: TS = {"Name": {}, "Icon": {}}
talentId2Name: TS = {"Name": {}, "Icon": {}}
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


try:
    with open(MAP / charList_fileName, "r", encoding="UTF-8") as f:
        charList.update(msgjson.decode(f.read(), type=Dict))

    with open(MAP / weaponList_fileName, "r", encoding="UTF-8") as f:
        weaponList.update(msgjson.decode(f.read(), type=Dict))

    with open(MAP / avatarId2Name_fileName, "r", encoding="UTF-8") as f:
        avatarId2Name.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / icon2Name_fileName, "r", encoding="UTF-8") as f:
        icon2Name.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / artifact2attr_fileName, "r", encoding="UTF-8") as f:
        artifact2attr.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / icon2Name_fileName, "r", encoding="UTF-8") as f:
        icon2Name.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / name2Icon_fileName, "r", encoding="UTF-8") as f:
        name2Icon.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / "propId2Name_mapping.json", "r", encoding="UTF-8") as f:
        propId2Name.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / "Id2propId_mapping.json", "r", encoding="UTF-8") as f:
        Id2PropId.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / weaponHash2Name_fileName, "r", encoding="UTF-8") as f:
        weaponHash2Name.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / weaponHash2Type_fileName, "r", encoding="UTF-8") as f:
        weaponHash2Type.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / "artifactId2Piece_mapping.json", "r", encoding="UTF-8") as f:
        artifactId2Piece.update(msgjson.decode(f.read(), type=Dict[str, List[str]]))

    with open(MAP / skillId2Name_fileName, "r", encoding="UTF-8") as f:
        skillId2Name.update(msgjson.decode(f.read(), type=TS))

    with open(MAP / talentId2Name_fileName, "r", encoding="UTF-8") as f:
        talentId2Name.update(msgjson.decode(f.read(), type=TS))

    with open(MAP / avatarName2Element_fileName, "r", encoding="UTF-8") as f:
        avatarName2Element.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / avatarName2Weapon_fileName, "r", encoding="UTF-8") as f:
        avatarName2Weapon.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / "char_alias.json", "r", encoding="UTF-8") as f:
        alias_data.update(msgjson.decode(f.read(), type=Dict[str, List[str]]))

    with open(MAP / avatarId2Star_fileName, "r", encoding="utf8") as f:
        avatarId2Star_data.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / enName2Id_fileName, "r", encoding="utf8") as f:
        enName_to_avatarId_data.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / EXMonster_fileName, "r", encoding="utf8") as f:
        ex_monster_data.update(msgjson.decode(f.read(), type=Dict[str, Dict]))

    with open(MAP / monster2entry_fileName, "r", encoding="utf8") as f:
        monster2entry_data.update(msgjson.decode(f.read(), type=Dict[str, Dict]))

    with open(MAP / avatarId2SkillList_fileName, "r", encoding="utf8") as f:
        avatarId2SkillList_data.update(msgjson.decode(f.read(), type=Dict[str, Dict[str, str]]))

    with open(MAP / weaponId2Name_fileName, "r", encoding="utf8") as f:
        weaponId2Name_data.update(msgjson.decode(f.read(), type=Dict[str, str]))

    with open(MAP / mysData_fileName, "r", encoding="utf8") as f:
        mysData.update(msgjson.decode(f.read(), type=Dict))

    with open(MAP / CharId2TalentIcon_fileName, "r", encoding="utf8") as f:
        CharId2TalentIcon_data.update(msgjson.decode(f.read(), type=Dict[str, List[str]]))
    logger.success(t("log.genshinuid.genshinuid_map_380311"))
except FileNotFoundError:
    logger.error(t("log.genshinuid.genshinuid_267801"))
