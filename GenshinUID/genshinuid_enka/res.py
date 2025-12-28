import json
from typing import List, Optional
from pathlib import Path

import aiofiles
from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error

from ..utils.mys_api import mys_api, get_base_data
from .mono.Character import Character
from ..utils.map.GS_MAP_PATH import charList, weaponList
from ..utils.map.name_covert import avatar_id_to_char_star
from ..genshinuid_enka.etc.etc import get_all_artifacts_value
from ..utils.image.image_tools import (
    get_avatar,
)
from ..genshinuid_compute.utils import get_all_char_dict
from ..utils.fonts.genshin_fonts import (
    gs_font_28,
    gs_font_30,
    gs_font_38,
    gs_font_40,
)
from ..utils.resource.RESOURCE_PATH import PLAYER_PATH
from ..genshinuid_poetry_abyss.draw_poetry_abyss import (
    TEXT_PATH as POETRY_ABYSS_PATH,
)
from ..genshinuid_hard_challenge.draw_hard_challenge import (
    TEXT_PATH as HARD_CHALLENGE_PATH,
)

TEXT_PATH = Path(__file__).parent / "count_texture2d"

ring = Image.open(TEXT_PATH / "ring.png")
ring_mask = Image.open(TEXT_PATH / "ring_mask.png")
skill_mask = Image.open(TEXT_PATH / "skill_mask.png")
value_mask = Image.open(TEXT_PATH / "value_mask.png")
div = Image.open(TEXT_PATH / "div.png")


def check_element(element: str, char: dict) -> bool:
    return element == char["avatarElement"]


EXTRA_MAP = {
    "火": [check_element, "Pyro"],
    "水": [check_element, "Hydro"],
    "冰": [check_element, "Cryo"],
    "岩": [check_element, "Geo"],
    "雷": [check_element, "Electro"],
    "草": [check_element, "Dendro"],
}


def draw_ring(img: Image.Image, star: int):
    bg_temp = Image.new("RGBA", (90, 90), (0, 0, 0, 0))
    if star >= 5:
        star = 5
    bg = Image.open(TEXT_PATH / f"star_{star}.png")

    img = img.resize((90, 90))
    bg_temp.paste(img, (0, 0), ring_mask)
    bg.paste(bg_temp, (0, 0), bg_temp)
    bg.paste(ring, (0, 0), ring)
    return bg


def extract_words_with_positions(text: str, vocabulary: List[str]) -> List[str]:
    vocab_sorted = sorted(vocabulary, key=len, reverse=True)
    result = []
    i = 0

    while i < len(text):
        matched = False
        for word in vocab_sorted:
            if text[i:].startswith(word):
                result.append(word)
                i += len(word)
                matched = True
                break

        if not matched:
            i += 1

    return result


async def draw_new_title(ev: Event, uid: str, _force_mode: Optional[int] = None):
    uid_fold = PLAYER_PATH / str(uid)
    char_file_list = uid_fold.glob("*")
    char_list = []
    for i in char_file_list:
        file_name = i.name
        if "\u4e00" <= file_name[0] <= "\u9fff":
            char_list.append(file_name.split(".")[0])
    if not char_list:
        return "你还没有已缓存的角色！\n请先使用【强制刷新】进行刷新！"

    extra_list = []
    if ev.text.strip():
        extra_list = extract_words_with_positions(ev.text.strip(), list(EXTRA_MAP.keys()))

    datas = await get_base_data(uid)
    if isinstance(datas, (str, bytes)):
        return datas

    raw = await get_all_char_dict()
    pack_data = await mys_api.get_batch_compute_info(uid, raw)
    if isinstance(pack_data, int):
        return get_error(pack_data)

    for item in pack_data["overall_consume"]:
        if item["id"] != 104319:
            continue
        crown_get = item["num"] - item["lack_num"]

    crown_cost = 0
    """皇冠消耗"""

    fetter_full = 0
    """满好感角色"""

    full_star4_char = 0
    """满命4星角色"""

    full_star5_char = 0
    """满命5星角色"""

    star4_char = 0
    """4星角色"""

    star5_char = 0
    """5星角色"""

    full_star4_weapon = 0
    """满命4星武器"""

    full_star5_weapon = 0
    """满命5星武器"""

    star4_weapon = 0
    """4星武器"""

    star5_weapon = 0
    """5星武器"""

    high_score_equip_num = 0
    """高分圣遗物套装数量"""

    useful_char = 0
    """有用角色"""

    ALL_STAR_5_CHAR = len([i for i in charList if charList[i]["rank"] == "QUALITY_ORANGE"])
    ALL_STAR_4_CHAR = len([i for i in charList if charList[i]["rank"] == "QUALITY_PURPLE"])

    """
    ALL_STAR_4_WEAPON = len(
        [i for i in weaponList if weaponList[i]['rank'] == 4]
    )
    """

    ALL_STAR_5_WEAPON = len([i for i in weaponList if weaponList[i]["rank"] == 5])

    char_done_list = []
    for char_name in char_list:
        temp = {}
        async with aiofiles.open(uid_fold / f"{char_name}.json", "r", encoding="UTF-8") as f:
            raw_data = json.loads(await f.read())

        skill_list = raw_data["avatarSkill"]

        temp["char_name"] = char_name
        temp["fetter"] = raw_data["avatarFetter"]
        if char_name == "旅行者":
            temp["fetter"] = 10

        temp["id"] = raw_data["avatarId"]

        char = Character(raw_data)
        await char.new()
        await char.get_fight_prop()

        temp["value"] = await get_all_artifacts_value(
            raw_data,
            char.baseHp,
            char.baseAtk,
            char.baseDef,
            char_name,
        )
        temp["value"] = float("{:.2f}".format(temp["value"]))
        temp["avatarElement"] = raw_data["avatarElement"]
        temp["a_skill_level"] = skill_list[0]["skillLevel"]
        temp["e_skill_level"] = skill_list[1]["skillLevel"]
        temp["q_skill_level"] = skill_list[-1]["skillLevel"]
        temp["talent_num"] = len(raw_data["talentList"])

        if temp["a_skill_level"] >= 10:
            crown_cost += 1
        if temp["e_skill_level"] >= 10:
            crown_cost += 1
        if temp["q_skill_level"] >= 10:
            crown_cost += 1

        # 武器
        temp["weapon_name"] = raw_data["weaponInfo"]["weaponName"]
        temp["weapon_level"] = raw_data["weaponInfo"]["weaponLevel"]
        temp["weapon_affix"] = raw_data["weaponInfo"]["weaponAffix"]
        temp["weapon_star"] = raw_data["weaponInfo"]["weaponStar"]

        char_star = int(await avatar_id_to_char_star(temp["id"]))
        temp["char_star"] = char_star

        temp["score_value"] = (
            temp["a_skill_level"]
            + temp["e_skill_level"]
            + temp["q_skill_level"]
            + temp["talent_num"] * (char_star - 3)
            + temp["weapon_affix"] * (temp["weapon_star"] - 3)
            + temp["value"]
        )

        # 角色变量
        if temp["fetter"] >= 10:
            fetter_full += 1

        if char_star == 5:
            star5_char += 1
            if temp["talent_num"] >= 6:
                full_star5_char += 1
        elif char_star == 4:
            star4_char += 1
            if temp["talent_num"] >= 6:
                full_star4_char += 1

        # 武器变量
        if temp["weapon_star"] == 5:
            star5_weapon += 1
            if temp["weapon_affix"] >= 5:
                full_star5_weapon += 1
        elif temp["weapon_star"] == 4:
            star4_weapon += 1
            if temp["weapon_affix"] >= 5:
                full_star4_weapon += 1

        if temp["value"] >= 27:
            high_score_equip_num += 1

        if temp["value"] >= 24 and (
            temp["a_skill_level"] >= 8 or temp["e_skill_level"] >= 8 or temp["q_skill_level"] >= 8
        ):
            useful_char += 1

        _toru = 0
        for extra in extra_list:
            if extra in EXTRA_MAP:
                if EXTRA_MAP[extra][0](EXTRA_MAP[extra][1], temp):
                    _toru += 1
                    continue

        if not extra_list:
            _toru = 1

        if not _toru:
            continue

        char_done_list.append(temp)

    if len(char_done_list) > 86:
        _mode = 3
    else:
        _mode = 2

    if _force_mode is not None:
        _mode = _force_mode

    img = Image.new("RGBA", (2370 if _mode == 3 else 1600, 600 + 150))

    title = Image.open(TEXT_PATH / f"title_{_mode}.png")
    title_fg = Image.open(TEXT_PATH / f"title_fg_{_mode}.png")
    char_pic = await get_avatar(ev, 180)
    title.paste(char_pic, (117, 328) if _mode == 3 else (88, 328), char_pic)
    title.paste(title_fg, (0, 0), title_fg)
    title_draw = ImageDraw.Draw(title)

    title_draw.text(
        (360, 428) if _mode == 3 else (331, 428),
        f"{ev.sender['nickname'] if 'nickname' in ev.sender else '旅行者'}",
        "white",
        gs_font_40,
        "lm",
    )
    title_draw.text(
        (456, 478) if _mode == 3 else (427, 478),
        f"UID {uid}",
        (207, 207, 207),
        gs_font_30,
        "mm",
    )

    spiral_abyss = datas["stats"]["spiral_abyss"]
    role_combat = datas["stats"]["role_combat"]
    max_round_id = role_combat["max_round_id"]
    hard_challenge = datas["stats"]["hard_challenge"]
    hard_level = hard_challenge["difficulty"] if hard_challenge["difficulty"] >= 3 else 3

    if role_combat["difficulty_id"] == 3:
        if role_combat["max_round_id"] == 8:
            icon_name = "gold_yes.png"
        else:
            icon_name = "gold_no.png"
    elif role_combat["difficulty_id"] == 4:
        if role_combat["max_round_id"] == 10:
            icon_name = "super_yes.png"
        else:
            icon_name = "super_no.png"
    elif role_combat["difficulty_id"] == 5:
        if role_combat["max_round_id"] == 10 and role_combat["tarot_finished_cnt"] == 2:
            icon_name = "moon_yes.png"
        else:
            icon_name = "moon_no.png"
    else:
        icon_name = "gold_no.png"

    icon = Image.open(POETRY_ABYSS_PATH / icon_name).convert("RGBA")
    title.paste(icon, (1882, 438) if _mode == 3 else (1151, 438), icon)

    hard_icon = Image.open(HARD_CHALLENGE_PATH / f"medal_{hard_level}.png").convert("RGBA").resize((52, 52))
    title.paste(hard_icon, (2057, 358) if _mode == 3 else (1326, 358), hard_icon)

    title_draw.text(
        (2208, 462) if _mode == 3 else (1476, 462),
        f"深渊{spiral_abyss}",
        "white",
        gs_font_28,
        "mm",
    )
    title_draw.text(
        (2208, 383) if _mode == 3 else (1476, 383),
        f"{hard_challenge['name']}",
        "white",
        gs_font_28,
        "mm",
    )
    title_draw.text(
        (2033, 462) if _mode == 3 else (1301, 462),
        f"第{max_round_id}幕",
        "white",
        gs_font_28,
        "mm",
    )
    img.paste(title, (0, 0), title)

    # title_bar部分
    title_bar = Image.open(TEXT_PATH / f"title_bar_{_mode}.png")
    title_bar_draw = ImageDraw.Draw(title_bar)
    if _mode == 3:
        title_list = [
            f"{crown_cost}/{crown_get + crown_cost}",
            f"{fetter_full}/{len(datas['avatars'])}",
            f"{full_star5_char}/{star5_char}",
            f"{full_star4_char}/{star4_char}",
            f"{star5_char}/{ALL_STAR_5_CHAR}",
            f"{star4_char}/{ALL_STAR_4_CHAR}",
            f"{star5_weapon}/{ALL_STAR_5_WEAPON}",
            f"{full_star4_weapon}/{star4_weapon}",
            f"{full_star5_weapon}/{star5_weapon}",
            high_score_equip_num,
            useful_char,
        ]
        start_pos = (181, 52)
        offset = 201.8
    else:
        title_list = [
            f"{crown_cost}/{crown_get + crown_cost}",
            f"{fetter_full}/{len(datas['role'])}",
            # f'{full_star5_char}/{star5_char}',
            f"{full_star4_char}/{star4_char}",
            f"{star5_char}/{ALL_STAR_5_CHAR}",
            f"{star4_char}/{ALL_STAR_4_CHAR}",
            f"{star5_weapon}/{ALL_STAR_5_WEAPON}",
            high_score_equip_num,
            useful_char,
        ]
        start_pos = (142, 52)
        offset = 187.4

    for index, title in enumerate(title_list):
        title_bar_draw.text(
            (int(start_pos[0] + index * offset), int(start_pos[1])),
            str(title),
            "white",
            gs_font_38,
            "mm",
        )

    img.paste(title_bar, (0, 570), title_bar)
    return img, char_done_list
