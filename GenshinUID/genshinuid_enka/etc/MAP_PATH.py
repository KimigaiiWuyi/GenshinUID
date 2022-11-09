import json
from pathlib import Path
from typing import Dict, List

EFFECT_PATH = Path(__file__).parents[1] / 'effect'

with open(EFFECT_PATH / 'weapon_effect.json', "r", encoding='UTF-8') as f:
    weapon_effect_map: Dict[
        str, Dict[str, Dict[str, Dict[str, str]]]
    ] = json.load(f)

with open(EFFECT_PATH / 'char_effect.json', "r", encoding='UTF-8') as f:
    char_effect_map: Dict[
        str, Dict[str, Dict[str, Dict[str, str]]]
    ] = json.load(f)

with open(EFFECT_PATH / 'artifact_effect.json', "r", encoding='UTF-8') as f:
    artifact_effect_map: Dict[str, Dict[str, Dict[str, str]]] = json.load(f)

with open(EFFECT_PATH / 'value_attr.json', 'r', encoding='UTF-8') as f:
    ATTR_MAP: Dict[str, List[str]] = json.load(f)

with open(EFFECT_PATH / 'char_action.json', 'r', encoding='UTF-8') as f:
    char_action = json.load(f)

with open(EFFECT_PATH / 'dmg_map.json', 'r', encoding='UTF-8') as f:
    dmgMap = json.load(f)

with open(EFFECT_PATH / 'skill_add.json', 'r', encoding='UTF-8') as f:
    avatarName2SkillAdd: Dict[str, List[str]] = json.load(f)

COLOR_MAP = {
    'Anemo': (0, 145, 137),
    'Cryo': (4, 126, 152),
    'Dendro': (28, 145, 0),
    'Electro': (133, 12, 159),
    'Geo': (147, 112, 3),
    'Hydro': (51, 73, 162),
    'Pyro': (119, 12, 17),
}
