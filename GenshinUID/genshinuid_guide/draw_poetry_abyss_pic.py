import re
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw

from gsuid_core.utils.error_reply import get_error
from gsuid_core.utils.image.convert import convert_img

from ..utils.map.name_covert import avatar_id_to_name
from ..utils.image.image_tools import add_footer
from ..utils.api.hakush.request import hakush_api
from ..utils.fonts.genshin_fonts import (
    gs_font_20,
    gs_font_22,
    gs_font_26,
    gs_font_28,
    gs_font_30,
    gs_font_38,
)
from ..utils.resource.RESOURCE_PATH import CHAR_CARD_PATH, MONSTER_ICON_PATH

TEXT_PATH = Path(__file__).parent / "texture2d2"


def remove_angle_brackets(text: str) -> str:
    cleaned_text = re.sub(r"<.*?>", "", text)
    return cleaned_text


def is_current_time_in_range(start_time: str, end_time: str) -> bool:
    start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    current_datetime = datetime.now()

    return start_datetime <= current_datetime <= end_datetime


async def draw_poetry_abyss_image(v: str):
    data = await hakush_api.get_hakush_rolecombats()
    if isinstance(data, int):
        return get_error(data)

    poetry_id = 0
    for _id in data:
        item = data[_id]
        if "live_begin" in item:
            begin = item["live_begin"]
        else:
            begin = item["begin"]

        if "live_end" in item:
            end = item["live_end"]
        else:
            end = item["end"]

        if is_current_time_in_range(begin, end):
            if "下" in v:
                poetry_id = str(int(_id) + 1)
                if poetry_id not in data:
                    return "没有找到下期的阵容, 可能暂未更新, 请尝试查找当期阵容!"
            else:
                poetry_id = _id
            break
    else:
        return "没有找到当前的活动!"

    pdata = await hakush_api.get_hakush_rolecombat(poetry_id)
    if isinstance(pdata, int):
        return get_error(pdata)

    w, h = 1000, 1270 + 50

    monster_list = list(pdata["DifficultyConfig"].values())[-1]
    monster_room = monster_list["Room"]

    for room_id in monster_room:
        monster = monster_room[room_id]
        if "Title" in monster:
            h += 301
        else:
            h += 145

    time = f"{pdata['BeginTime']} ~ {pdata['EndTime']}"
    img = Image.new("RGBA", (w, h), (22, 18, 20, 255))

    title = Image.open(TEXT_PATH / "title.png")
    title_draw = ImageDraw.Draw(title)
    title_draw.text(
        (500, 473),
        f"剧诗ID：{poetry_id} 详细信息",
        (255, 255, 255),
        font=gs_font_38,
        anchor="mm",
    )
    img.paste(title, (0, 0), title)

    avatar_bg = Image.open(TEXT_PATH / "avatar_bg.png")
    avatar_draw = ImageDraw.Draw(avatar_bg)

    avatar_draw.text(
        (500, 184),
        time,
        (139, 137, 133),
        font=gs_font_22,
        anchor="mm",
    )

    avatar_draw.text(
        (500, 474),
        pdata["AvatarConfig"]["BuffAvatarList"][0]["Desc"][16:-9],
        (139, 137, 133),
        font=gs_font_26,
        anchor="mm",
    )

    for cindex, char in enumerate(pdata["AvatarConfig"]["BuffAvatarList"]):
        char_id = str(char["Id"])
        char_img = Image.open(CHAR_CARD_PATH / f"{char_id}.png")
        char_img = char_img.resize((102, 124))
        char_name = await avatar_id_to_name(char_id)
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text(
            (51, 111),
            char_name,
            (10, 10, 10),
            font=gs_font_20,
            anchor="mm",
        )
        avatar_bg.paste(char_img, (121 + cindex * 130, 302), char_img)

    for iindex, char_id in enumerate(pdata["AvatarConfig"]["InviteAvatarList"]):
        char_id = str(char_id)
        char_img = Image.open(CHAR_CARD_PATH / f"{char_id}.png")
        char_img = char_img.resize((102, 124))
        char_name = await avatar_id_to_name(char_id)
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text(
            (51, 111),
            char_name,
            (10, 10, 10),
            font=gs_font_20,
            anchor="mm",
        )
        avatar_bg.paste(char_img, (252 + iindex * 130, 576), char_img)

    img.paste(avatar_bg, (0, 482), avatar_bg)

    point = 1270
    for room_id in monster_room:
        monster = monster_room[room_id]
        if "Title" in monster:
            monster_bg = Image.open(TEXT_PATH / "long_monster_bg.png")
            monster_draw = ImageDraw.Draw(monster_bg)
            desc = remove_angle_brackets(monster["Desc"])
            desc = desc[:26] + "..."
            monster_draw.text(
                (245, 69),
                f"{monster['Title']}",
                "black",
                font=gs_font_30,
                anchor="lm",
            )
            for mindex, m in enumerate(monster["MonsterPreviewList"]):
                monster_icon = m["Icon"]
                monster_img = await hakush_api.get_hakush_ui(monster_icon, MONSTER_ICON_PATH)
                monster_img = monster_img.resize((90, 90))
                monster_name = m["Name"]
                if "·" in monster_name:
                    monster_name = monster_name.split("·")[-1]

                monster_name = monster_name[:6]

                monster_hp = int(m["Hp"])
                mimg = Image.new(
                    "RGBA",
                    (250, 90),
                    (219, 209, 203),
                )
                ming_draw = ImageDraw.Draw(mimg)
                monster_img = monster_img.convert("RGBA")
                mimg.paste(monster_img, (0, 0), monster_img)
                ming_draw.text(
                    (100, 30),
                    f"{monster_name}",
                    (36, 36, 36),
                    font=gs_font_22,
                    anchor="lm",
                )

                ming_draw.text(
                    (100, 57),
                    f"HP {monster_hp}",
                    (90, 90, 90),
                    font=gs_font_22,
                    anchor="lm",
                )
                monster_bg.paste(mimg, (126 + mindex * 257, 158), mimg)
        else:
            monster_bg = Image.open(TEXT_PATH / "short_monster_bg.png")
            monster_draw = ImageDraw.Draw(monster_bg)
            desc = f"怪物等级 Lv{monster['MonsterLevel']}"

        monster_draw.text(
            (131, 69),
            f"第{room_id}幕",
            "black",
            font=gs_font_30,
            anchor="lm",
        )

        monster_draw.text(
            (131, 114),
            desc,
            (99, 99, 99),
            font=gs_font_28,
            anchor="lm",
        )

        if "Title" not in monster:
            point -= 12

        img.paste(monster_bg, (0, point), monster_bg)
        if "Title" not in monster:
            point += 145
        else:
            point += 301

    img = add_footer(img, 1000)
    res = await convert_img(img)
    return res
