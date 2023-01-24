import sys
from pathlib import Path

MAIN_PATH = Path() / 'data' / 'GenshinUID'
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
CHAR_NAMECARD_PATH = RESOURCE_PATH / 'char_namecard'
REL_PATH = RESOURCE_PATH / 'reliquaries'
ICON_PATH = RESOURCE_PATH / 'icon'
TEMP_PATH = RESOURCE_PATH / 'temp'
CARD_PATH = RESOURCE_PATH / 'card'
GUIDE_PATH = WIKI_PATH / 'guide'
TEXT2D_PATH = Path(__file__).parents[2] / 'resource' / 'texture2d'

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
        TEMP_PATH,
        CARD_PATH,
        GUIDE_PATH,
        CU_BG_PATH,
        CU_CHBG_PATH,
    ]:
        i.mkdir(parents=True, exist_ok=True)


init_dir()
