import asyncio
from typing import Dict, Union
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.models import Event

from .get_enka_img import get_char_data
from .draw_role_rank import get_color
from .get_akasha_data import _get_rank
from ..utils.image.convert import convert_img
from ..utils.map.GS_MAP_PATH import mysData, weaponList
from ..utils.map.name_covert import avatar_id_to_name, avatar_id_to_char_star
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_talent_pic,
    get_weapon_affix_pic,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_22,
    gs_font_26,
    gs_font_30,
    gs_font_32,
)
from ..utils.resource.download_url import download_file
from ..utils.resource.RESOURCE_PATH import REL_PATH, CHAR_PATH, WEAPON_PATH
from ..genshinuid_count.draw_char_count import div, draw_ring, draw_new_title

TEXTURE_PATH = Path(__file__).parent / "rank_texture2d"
rank_bar_text = Image.open(TEXTURE_PATH / "rank_bar_text.png")
rank_bar_fill = Image.open(TEXTURE_PATH / "rank_bar_fill.png")


def get_weapon_name(weapon_icon_name: str):
    for i in weaponList:
        weapon = weaponList[i]
        if weapon["icon"] == weapon_icon_name:
            return weapon["CHS"]
    else:
        return "无锋剑"


async def draw_single_rank(
    uid: str,
    img: Image.Image,
    char_id: str,
    char_data: Dict,
    index: int,
):
    char = char_data["calculations"]["fit"]

    if "variant" in char:
        _type: str = char["variant"]["displayName"]
    else:
        _type = char["short"]

    result = str(int(char["result"]))
    ranking: int = char["ranking"]
    outof: int = char["outOf"]
    percent: float = (ranking / outof) * 100

    rank_bar = Image.open(TEXTURE_PATH / "rank_bar.png")
    bar_draw = ImageDraw.Draw(rank_bar)

    _c: int = char["priority"]
    _wc: int = char["weapon"]["refinement"]
    hp: int = int(char["stats"]["maxHP"])
    atk: int = int(char["stats"]["maxATK"])
    cr = "{:.1f}".format(char["stats"]["critRate"] * 100)
    cd = "{:.1f}".format(char["stats"]["critDMG"] * 100)
    cv = "{:.1f}".format(char["stats"]["critValue"])

    rank_mask = Image.new("RGBA", rank_bar.size, (0, 0, 0, 0))
    rank_mask_draw = ImageDraw.Draw(rank_mask)
    rect_x = 81 + (1266 - 81) * percent / 100
    rect = (int(rect_x), 0, 1266, 90)
    rank_mask_draw.rectangle(rect, fill="white")
    rank_bar.paste(rank_bar_fill, (0, 0), rank_mask)

    cv_color = get_color(float(cv), [260, 245, 225, 180])

    affix_pic = await get_weapon_affix_pic(_wc)
    talent_pic = await get_talent_pic(_c)

    char_pic = Image.open(CHAR_PATH / f"{char_id}.png")
    weapon_star = int(char["weapon"]["rarity"])
    char_star = await avatar_id_to_char_star(char_id)
    char_pic = draw_ring(char_pic, int(char_star))
    weapon_icon: str = char["weapon"]["icon"].split("/")[-1].split(".")[0]
    weapon_icon_name = weapon_icon.replace("_Awaken", "")
    weapon_name = get_weapon_name(weapon_icon_name)
    weapon_pic = Image.open(WEAPON_PATH / f"{weapon_name}.png")
    weapon_pic = draw_ring(weapon_pic, weapon_star)

    enka_char_data = await get_char_data(
        uid,
        await avatar_id_to_name(char_id),
    )

    if isinstance(enka_char_data, str):
        pass
    else:
        if (
            "equipSets" in enka_char_data
            and "type" in enka_char_data["equipSets"]
            and "set" in enka_char_data["equipSets"]
        ):
            sets = enka_char_data["equipSets"]
            sets_type = "2+2" if sets["type"] == "22" else "4"
            artifactSets = sets["set"].split("|")

            if artifactSets:
                icon_list = []
                for art in artifactSets:
                    rel_path = REL_PATH / f"{art}.png"
                    if not rel_path.exists():
                        for i in mysData["data"]["all_set"]:
                            if i["name"] == art:
                                await download_file(i["icon"], 7, f"{i['name']}.png")
                                break

                    icon_img = Image.open(rel_path)

                    if sets_type == "4":
                        icon_list.clear()
                        icon_list.append(icon_img.resize((64, 64)))
                    else:
                        icon_list.append(icon_img.resize((51, 51)))

                if len(icon_list) == 1:
                    rank_bar.paste(icon_list[0], (166, 17), icon_list[0])
                    text = "4"
                elif len(icon_list) == 2:
                    text = "2+2"
                    rank_bar.paste(icon_list[0], (155, 24), icon_list[0])
                    rank_bar.paste(icon_list[1], (171, 9), icon_list[1])
                else:
                    text = "0"
                bar_draw.text((207, 61), text, (214, 255, 192), gs_font_20, "mm")

    rank_bar.paste(rank_bar_text, (0, 0), rank_bar_text)

    rank_bar.paste(char_pic, (68, 6), char_pic)
    rank_bar.paste(weapon_pic, (844, 0), weapon_pic)

    bar_draw.text((242, 36), f"{cr}: {cd}", "white", gs_font_26, "lm")
    bar_draw.text((242, 59), f"{cv} cv", cv_color, gs_font_20, "lm")
    bar_draw.text((483, 46), f"{hp}", "white", gs_font_26, "lm")
    bar_draw.text((690, 46), f"{atk}", "white", gs_font_26, "lm")

    rank_bar.paste(talent_pic, (770, 30), talent_pic)
    rank_bar.paste(affix_pic, (953, 30), affix_pic)

    bar_draw.text((1401, 34), result, "white", gs_font_32, "mm")
    bar_draw.text((1401, 64), _type, (150, 150, 150), gs_font_22, "mm")
    bar_draw.text((1238, 34), f"全球前{percent:.1f}%", "white", gs_font_30, "rm")
    bar_draw.text((1238, 64), f"{ranking} / {outof}", (150, 150, 150), gs_font_22, "rm")

    img.paste(rank_bar, (0, 700 + index * 90), rank_bar)


async def draw_rank_img(ev: Event, uid: str) -> Union[bytes, str]:
    rank_data = await _get_rank(uid)
    if isinstance(rank_data, str):
        return rank_data

    h = 570 + 150 + len(rank_data) * 90 + 80
    img = get_v4_bg(1600, h, 200)
    title = await draw_new_title(ev, uid, 2)
    if isinstance(title, str):
        return title
    elif isinstance(title, bytes):
        return title

    title, _ = title
    img.paste(title, (0, 0), title)

    tasks = []
    for index, char in enumerate(rank_data):
        tasks.append(draw_single_rank(uid, img, char, rank_data[char], index))
    await asyncio.gather(*tasks)

    img = add_footer(img, 700)
    img.paste(div, (0, h - 61), div)
    res = await convert_img(img)
    return res
