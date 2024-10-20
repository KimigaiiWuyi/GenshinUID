import sys
from pathlib import Path

from gsuid_core.data_store import get_res_path

MAIN_PATH = get_res_path() / 'GenshinUID'
sys.path.append(str(MAIN_PATH))
CONFIG_PATH = MAIN_PATH / 'config.json'
RESOURCE_PATH = MAIN_PATH / 'resource'
WIKI_PATH = MAIN_PATH / 'wiki'
CU_BG_PATH = MAIN_PATH / 'bg'
CU_CHBG_PATH = MAIN_PATH / 'chbg'
WEAPON_PATH = RESOURCE_PATH / 'weapon'
GACHA_IMG_PATH = RESOURCE_PATH / 'gacha_img'
CHAR_PATH = RESOURCE_PATH / 'chars'
CHAR_STAND_PATH = RESOURCE_PATH / 'char_stand'
CHAR_SIDE_PATH = RESOURCE_PATH / 'char_side'
CHAR_SIDE_TEMP_PATH = RESOURCE_PATH / 'char_side_temp'
CHAR_CARD_PATH = RESOURCE_PATH / 'char_card'
CHAR_NAMECARD_PATH = RESOURCE_PATH / 'char_namecard'
CHAR_NAMECARDPIC_PATH = RESOURCE_PATH / 'char_namecard_pic'
REL_PATH = RESOURCE_PATH / 'reliquaries'
ICON_PATH = RESOURCE_PATH / 'icon'
ACHI_ICON_PATH = RESOURCE_PATH / 'achi_icon'
TEMP_PATH = RESOURCE_PATH / 'temp'
CARD_PATH = RESOURCE_PATH / 'card'
MONSTER_ICON_PATH = RESOURCE_PATH / 'monster_icon'
ABYSS_PATH = WIKI_PATH / 'abyss_review'
GUIDE_PATH = WIKI_PATH / 'guide'
REF_PATH = WIKI_PATH / 'ref'
WIKI_REL_PATH = WIKI_PATH / 'artifacts'
CONSTELLATION_PATH = WIKI_PATH / 'constellation'
WIKI_WEAPON_PATH = WIKI_PATH / 'weapon'
WIKI_FOOD_PATH = WIKI_PATH / 'food'
WIKI_TALENT_PATH = WIKI_PATH / 'talent'
WIKI_ENEMY_PATH = WIKI_PATH / 'enemy'
WIKI_CHAR_PATH = WIKI_PATH / 'char'
WIKI_COST_CHAR_PATH = WIKI_PATH / 'cost_char'
WIKI_COST_WEAPON_PATH = WIKI_PATH / 'cost_weapon'
TEXT2D_PATH = Path(__file__).parent / 'texture2d'
DATA_PATH = MAIN_PATH / 'data'
PLAYER_PATH = MAIN_PATH / 'players'


def init_dir():
    for i in [
        MAIN_PATH,
        RESOURCE_PATH,
        WIKI_PATH,
        WEAPON_PATH,
        GACHA_IMG_PATH,
        CHAR_PATH,
        CHAR_STAND_PATH,
        CHAR_SIDE_PATH,
        CHAR_NAMECARD_PATH,
        REL_PATH,
        ICON_PATH,
        TEXT2D_PATH,
        PLAYER_PATH,
        ACHI_ICON_PATH,
        TEMP_PATH,
        CARD_PATH,
        GUIDE_PATH,
        CU_BG_PATH,
        CU_CHBG_PATH,
        REF_PATH,
        CHAR_CARD_PATH,
        WIKI_REL_PATH,
        CONSTELLATION_PATH,
        WIKI_WEAPON_PATH,
        WIKI_FOOD_PATH,
        WIKI_TALENT_PATH,
        WIKI_ENEMY_PATH,
        WIKI_CHAR_PATH,
        WIKI_COST_CHAR_PATH,
        WIKI_COST_WEAPON_PATH,
        DATA_PATH,
        CHAR_SIDE_TEMP_PATH,
        MONSTER_ICON_PATH,
        ABYSS_PATH,
        CHAR_NAMECARDPIC_PATH,
    ]:
        i.mkdir(parents=True, exist_ok=True)


init_dir()
