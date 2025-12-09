from typing import Dict, List, Union
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.api.mys.models import AbyssBattleAvatar
from gsuid_core.utils.image.image_tools import get_avatar_with_ring

from ..utils.mys_api import mys_api
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import add_footer
from ..utils.fonts.genshin_fonts import (
    gs_font_22,
    gs_font_26,
    gs_font_32,
    gs_font_36,
)
from ..utils.resource.download_url import download_file
from ..utils.resource.RESOURCE_PATH import ICON_PATH, CHAR_SIDE_PATH
from ..genshinuid_abyss.draw_abyss_card import _draw_char_card

TEXT_PATH = Path(__file__).parent / "texture2d"


async def draw_hard_challenge_img(uid: str, ev: Event) -> Union[str, bytes]:
    data = await mys_api.get_hard_challenge_data(uid)
    if isinstance(data, int):
        return get_error(data)

    schedule = data["data"][0]["schedule"]
    sdata = data["data"][0]["single"]

    start_time: str = datetime.fromtimestamp(int(schedule["start_time"])).strftime("%Y/%m/%d")
    end_time: str = datetime.fromtimestamp(int(schedule["end_time"])).strftime("%Y/%m/%d")
    time_range = f"{start_time} ~ {end_time}"

    img = Image.open(TEXT_PATH / "bg.jpg").convert("RGBA")

    title = Image.open(TEXT_PATH / "title.png")
    title_draw = ImageDraw.Draw(title)
    avatar = await get_avatar_with_ring(ev, 278)
    title.paste(avatar, (315, 50), avatar)
    title_draw.text((450, 380), f"UID {uid}", "white", gs_font_26, "mm")
    title_draw.text((450, 422), time_range, (199, 199, 199), gs_font_22, "mm")
    img.paste(title, (0, 0), title)

    best_data = sdata["best"]
    if not best_data:
        return "你还没有挑战过[肃靖险乱]噢！(或需要等待数据同步后重试)"

    challenge: List[Dict] = sdata["challenge"]

    banner = Image.open(TEXT_PATH / "banner.png")
    medal = Image.open(TEXT_PATH / f"medal_{best_data['difficulty']}.png").resize((84, 84)).convert("RGBA")
    banner_draw = ImageDraw.Draw(banner)
    banner_draw.text((820, 51), f"{best_data['second']}秒", "white", gs_font_32, "rm")
    banner.paste(medal, (636, 9), medal)
    img.paste(banner, (0, 470), banner)

    card_fg = Image.open(TEXT_PATH / "card_fg.png")
    for findex, floor in enumerate(challenge):
        card = Image.open(TEXT_PATH / "card.png")
        card_draw = ImageDraw.Draw(card)
        name: str = floor["name"]
        sec: int = floor["second"]
        monster: Dict = floor["monster"]
        best_avatar: List[Dict] = floor["best_avatar"]
        teams: List[Dict] = floor["teams"]

        card_draw.text((59, 63), name, "white", gs_font_36, "lm")
        card_draw.text((79, 123), "战斗用时", "white", gs_font_26, "lm")
        card_draw.text((456, 123), f"{sec}秒", "white", gs_font_26, "rm")

        monster_bg = monster["icon"]
        monster_name = f"js_{monster['name']}.png"

        mpath = ICON_PATH / monster_name
        if not mpath.exists():
            await download_file(monster_bg, 8, monster_name)
        monster_img = Image.open(mpath).resize((563, 563))
        card.paste(monster_img, (425, -73), monster_img)
        card_draw.rounded_rectangle((726, 31, 826, 68), 5, (192, 24, 24))
        card_draw.text((776, 50), f"Lv{monster['level']}", "white", gs_font_26, "mm")

        card.paste(card_fg, (0, 0), card_fg)

        for aindex, avatar in enumerate(teams):
            avatar_data: AbyssBattleAvatar = {
                "id": avatar["avatar_id"],
                "icon": avatar["image"],
                "level": avatar["level"],
                "rarity": avatar["rarity"],
            }
            avatar_card = await _draw_char_card(avatar_data, avatar["rank"])
            avatar_card = avatar_card.resize((102, 124))
            card.paste(avatar_card, (111 * aindex + 58, 171), avatar_card)

        side_path_name_1 = f"{best_avatar[0]['avatar_id']}.png"
        side_path_1 = CHAR_SIDE_PATH / side_path_name_1
        if not side_path_1.exists():
            await download_file(
                best_avatar[0]["side_icon"],
                3,
                side_path_name_1,
            )
        side_img_1 = Image.open(side_path_1).resize((83, 83))

        side_path_name_2 = f"{best_avatar[1]['avatar_id']}.png"
        side_path_2 = CHAR_SIDE_PATH / side_path_name_2
        if not side_path_2.exists():
            await download_file(
                best_avatar[1]["side_icon"],
                3,
                side_path_name_2,
            )
        side_img_2 = Image.open(side_path_2).resize((83, 83))

        card.paste(side_img_1, (54, 291), side_img_1)
        card.paste(side_img_2, (435, 291), side_img_2)
        card_draw.text(
            (141, 354),
            "最强一击",
            "white",
            gs_font_26,
            "lm",
        )
        card_draw.text(
            (426, 354),
            best_avatar[0]["dps"],
            "white",
            gs_font_26,
            "rm",
        )

        card_draw.text(
            (521, 354),
            "最高总伤",
            "white",
            gs_font_26,
            "lm",
        )
        card_draw.text(
            (806, 354),
            best_avatar[1]["dps"],
            "white",
            gs_font_26,
            "rm",
        )

        img.paste(card, (0, 576 + findex * 420), card)

    img = add_footer(img, 800, 0)

    return await convert_img(img)
