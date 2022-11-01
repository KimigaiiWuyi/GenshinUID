import json
from pathlib import Path

from ....version import Genshin_version

MAP_PATH = Path(__file__).parent

version = Genshin_version

avatarName2Element_fileName = f'avatarName2Element_mapping_{version}.json'
weaponHash2Name_fileName = f'weaponHash2Name_mapping_{version}.json'
weaponHash2Type_fileName = f'weaponHash2Type_mapping_{version}.json'
skillId2Name_fileName = f'skillId2Name_mapping_{version}.json'
talentId2Name_fileName = f'talentId2Name_mapping_{version}.json'
avatarId2Name_fileName = f'avatarId2Name_mapping_{version}.json'

artifact2attr_fileName = f'artifact2attr_mapping_{version}.json'
icon2Name_fileName = f'icon2Name_mapping_{version}.json'
avatarName2Weapon_fileName = f'avatarName2Weapon_mapping_{version}.json'

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

with open(MAP_PATH / avatarName2Weapon_fileName, 'r', encoding='UTF-8') as f:
    avatarName2Weapon = json.load(f)
