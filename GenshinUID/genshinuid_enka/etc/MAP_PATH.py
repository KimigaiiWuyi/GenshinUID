import json
from typing import List, Dict
from pathlib import Path

EFFECT_PATH = Path(__file__).parents[1] / 'effect'

with open(EFFECT_PATH / 'weapon_effect.json', "r", encoding='UTF-8') as f:
    weapon_effect_map: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = json.load(f)

with open(EFFECT_PATH / 'char_effect.json', "r", encoding='UTF-8') as f:
    char_effect_map: Dict[str, Dict[str, Dict[str, Dict[str, str]]]] = json.load(f)

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
    'Anemo': (43, 170, 163),
    'Cryo': (97, 168, 202),
    'Dendro': (84, 169, 62),
    'Electro': (150, 62, 169),
    'Geo': (169, 143, 62),
    'Hydro': (66, 98, 182),
    'Pyro': (169, 62, 67),
}
