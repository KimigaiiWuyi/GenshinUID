import sys
from pathlib import Path

from gsuid_core.data_store import get_res_path

MAIN_PATH = get_res_path() / "GenshinUID"
sys.path.append(str(MAIN_PATH))
CONFIG_PATH = MAIN_PATH / "config.json"
RESOURCE_PATH = MAIN_PATH / "resource"
WIKI_PATH = MAIN_PATH / "wiki"
CU_BG_PATH = MAIN_PATH / "bg"
CU_CHBG_PATH = MAIN_PATH / "chbg"
WEAPON_PATH = RESOURCE_PATH / "weapon"
GACHA_IMG_PATH = RESOURCE_PATH / "gacha_img"
CHAR_PATH = RESOURCE_PATH / "chars"
CHAR_STAND_PATH = RESOURCE_PATH / "char_stand"
CHAR_SIDE_PATH = RESOURCE_PATH / "char_side"
CHAR_SIDE_TEMP_PATH = RESOURCE_PATH / "char_side_temp"
CHAR_CARD_PATH = RESOURCE_PATH / "char_card"
CHAR_NAMECARD_PATH = RESOURCE_PATH / "char_namecard"
CHAR_NAMECARDPIC_PATH = RESOURCE_PATH / "char_namecard_pic"
REL_PATH = RESOURCE_PATH / "reliquaries"
ICON_PATH = RESOURCE_PATH / "icon"
ACHI_ICON_PATH = RESOURCE_PATH / "achi_icon"
TEMP_PATH = RESOURCE_PATH / "temp"
CARD_PATH = RESOURCE_PATH / "card"
MONSTER_ICON_PATH = RESOURCE_PATH / "monster_icon"

CHAR_DATA_PATH = RESOURCE_PATH / "char_data"
WEAPON_DATA_PATH = RESOURCE_PATH / "weapon_data"
MONSTER_DATA_PATH = RESOURCE_PATH / "monster_data"
REL_DATA_PATH = RESOURCE_PATH / "reliquary_data"
FOOD_DATA_PATH = RESOURCE_PATH / "food_data"

ABYSS_PATH = WIKI_PATH / "abyss_review"
GUIDE_PATH = WIKI_PATH / "guide"
REF_PATH = WIKI_PATH / "ref"
WIKI_REL_PATH = WIKI_PATH / "artifacts"
CONSTELLATION_PATH = WIKI_PATH / "constellation"
WIKI_WEAPON_PATH = WIKI_PATH / "weapon"
WIKI_FOOD_PATH = WIKI_PATH / "food"
WIKI_TALENT_PATH = WIKI_PATH / "talent"
WIKI_ENEMY_PATH = WIKI_PATH / "enemy"
WIKI_CHAR_PATH = WIKI_PATH / "char"
WIKI_COST_CHAR_PATH = WIKI_PATH / "cost_char"
WIKI_COST_WEAPON_PATH = WIKI_PATH / "cost_weapon"
TEXT2D_PATH = Path(__file__).parent / "texture2d"
ELEMENT_ICON_PATH = TEXT2D_PATH / "element"
MZ_ICON_PATH = TEXT2D_PATH / "mz"
HG_ICON_PATH = TEXT2D_PATH / "hg"
DATA_PATH = MAIN_PATH / "data"
PLAYER_PATH = MAIN_PATH / "players"
WIKI_DATA_PATH = DATA_PATH / "wiki"
USAGE_RANK_PATH = DATA_PATH / "usage_rank"
WIKI_DATA_CHAR = WIKI_DATA_PATH / "char"
WIKI_DATA_WEAPON = WIKI_DATA_PATH / "weapon"
WIKI_DATA_REL = WIKI_DATA_PATH / "reliquary"
WIKI_DATA_FOOD = WIKI_DATA_PATH / "food"
WIKI_DATA_MONSTER = WIKI_DATA_PATH / "monster"
WIKI_DATA_ICON = WIKI_DATA_PATH / "icon"
WIKI_DATA_MONSTER_ICON = WIKI_DATA_PATH / "monster_icon"
WIKI_DATA_FETTER = WIKI_DATA_PATH / "fetter"
WIKI_DATA_VOICE = WIKI_DATA_PATH / "voice"


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
        CHAR_DATA_PATH,
        WEAPON_DATA_PATH,
        MONSTER_DATA_PATH,
        REL_DATA_PATH,
        FOOD_DATA_PATH,
        WIKI_DATA_PATH,
        USAGE_RANK_PATH,
        WIKI_DATA_CHAR,
        WIKI_DATA_WEAPON,
        WIKI_DATA_REL,
        WIKI_DATA_FOOD,
        WIKI_DATA_MONSTER,
        WIKI_DATA_ICON,
        WIKI_DATA_MONSTER_ICON,
        WIKI_DATA_FETTER,
        WIKI_DATA_VOICE,
    ]:
        i.mkdir(parents=True, exist_ok=True)


init_dir()


def _register_backup_hints() -> None:
    # 宿主 Core 无该模块（旧版本）时跳过，不报错
    try:
        from gsuid_core.utils.backup.hints import register_backup_path
    except ImportError:
        return
    register_backup_path(
        "GenshinUID",
        PLAYER_PATH,
        "user_data",
        "按 UID 存档的抽卡记录、面板与圣遗物仓",
    )
    register_backup_path("GenshinUID", CONFIG_PATH, "config", "插件配置", default_selected=True)
    register_backup_path("GenshinUID", CU_BG_PATH, "config", "自定义背景图")
    register_backup_path("GenshinUID", CU_CHBG_PATH, "config", "自定义角色背景图")
    register_backup_path(
        "GenshinUID",
        RESOURCE_PATH,
        "regenerable",
        "图片素材，可用「下载全部资源」命令重新下载",
    )
    register_backup_path(
        "GenshinUID",
        WIKI_PATH,
        "regenerable",
        "攻略 Wiki 数据，可用「下载全部资源」命令重新下载",
    )
    register_backup_path(
        "GenshinUID",
        DATA_PATH,
        "regenerable",
        "地图与榜单数据，可用「下载全部资源」命令重新下载",
    )


_register_backup_hints()
