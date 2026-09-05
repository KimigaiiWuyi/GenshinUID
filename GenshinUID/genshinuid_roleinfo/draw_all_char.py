import math
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.utils.error_reply import get_error_img
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.mys.models import IndexData, MihoyoAvatar

from ..utils.mys_api import mys_api, get_base_data
from ..utils.map.name_covert import avatar_id_to_char_star
from ..utils.image.image_tools import get_v4_bg
from ..utils.fonts.genshin_fonts import gs_font_28, gs_font_30
from ..utils.resource.RESOURCE_PATH import (
    CHAR_PATH,
    WEAPON_PATH,
    CHAR_NAMECARDPIC_PATH,
)

TEXT_PATH = Path(__file__).parent / "texture2d"
char_mask = Image.open(TEXT_PATH / "charcard_mask.png")
char_fg = Image.open(TEXT_PATH / "char_fg.png")

CHAR_CARD_W = 374
CHAR_CARD_H = 195
CHAR_GAP_X = 5
CHAR_PAD_X = 95
CHAR_HEAD = 160
CHAR_FOOT = 80
CHAR_COLS_DEFAULT = 4
CHAR_CANVAS_W = 1680
CHAR_DIV_Y = 65
CHAR_SIDE_PAD_X = 40


def _open_rgba(path: Path, fallback: tuple[int, int]) -> Image.Image:
    if path.exists():
        return Image.open(path).convert("RGBA")
    return Image.new("RGBA", fallback)


def _fit_bar_width(bar: Image.Image, width: int) -> Image.Image:
    if bar.size[0] == width:
        return bar
    if width < bar.size[0]:
        return bar.crop((0, 0, width, bar.size[1]))
    extra = width - bar.size[0]
    edge = bar.crop((bar.size[0] - 1, 0, bar.size[0], bar.size[1]))
    edge = edge.resize((extra, bar.size[1]))
    canvas = Image.new("RGBA", (width, bar.size[1]))
    canvas.paste(bar, (0, 0), bar)
    canvas.paste(edge, (bar.size[0], 0))
    return canvas


def _char_grid_metrics(
    char_num: int,
    match_height: int | None,
) -> tuple[int, int, int, int, int, int, int, int]:
    """based_w, based_h, cols, card_w, card_h, pad_x, head, foot"""
    if match_height is None:
        cols = CHAR_COLS_DEFAULT
        hang = 1 + (char_num - 1) // cols if char_num else 1
        based_h = hang * CHAR_CARD_H + CHAR_HEAD + CHAR_FOOT
        return (
            CHAR_CANVAS_W,
            based_h,
            cols,
            CHAR_CARD_W,
            CHAR_CARD_H,
            CHAR_PAD_X,
            CHAR_HEAD,
            CHAR_FOOT,
        )

    # 双列无横幅，底边留给整图 footer
    head = CHAR_SIDE_PAD_X
    foot = CHAR_FOOT
    avail_h = max(CHAR_CARD_H, match_height - head - foot)
    max_rows = max(1, avail_h // CHAR_CARD_H)
    cols = max(1, math.ceil(char_num / max_rows) if char_num else 1)
    rows = max(1, math.ceil(char_num / cols) if char_num else 1)
    card_h = avail_h // rows
    card_w = round(card_h * CHAR_CARD_W / CHAR_CARD_H)
    based_w = CHAR_SIDE_PAD_X * 2 + cols * card_w + max(0, cols - 1) * CHAR_GAP_X
    return based_w, match_height, cols, card_w, card_h, CHAR_SIDE_PAD_X, head, foot


async def _load_char_datas(uid: str, raw_data: IndexData) -> list[MihoyoAvatar] | str | bytes:
    if not raw_data["avatars"]:
        return "没有找到角色信息!"

    char_ids = [i["id"] for i in raw_data["avatars"]]
    char_rawdata = await mys_api.get_character(uid, char_ids)
    if isinstance(char_rawdata, int):
        return await get_error_img(char_rawdata)
    return char_rawdata["list"]


async def _prepare_char_datas(char_datas: list[MihoyoAvatar]) -> list[MihoyoAvatar]:
    prepared = list(char_datas)
    for char in prepared:
        rarity = char["rarity"] if "rarity" in char else None
        if rarity is None:
            try:
                rarity = int(await avatar_id_to_char_star(str(char["id"])))
            except (KeyError, TypeError, ValueError):
                rarity = 4
        char["rarity"] = min(int(rarity), 5)

    prepared.sort(
        key=lambda x: (
            -x["rarity"],
            -x["fetter"],
            -x["actived_constellation_num"],
        )
    )
    return prepared


async def _draw_char_pic(
    uid: str,
    raw_data: IndexData,
    match_height: int | None = None,
    char_datas: list[MihoyoAvatar] | None = None,
) -> Image.Image | str | bytes:
    if char_datas is None:
        loaded = await _load_char_datas(uid, raw_data)
        if isinstance(loaded, (str, bytes)):
            return loaded
        char_datas = loaded

    char_datas = await _prepare_char_datas(char_datas)
    char_num = len(char_datas)
    based_w, based_h, cols, card_w, card_h, pad_x, head, foot = _char_grid_metrics(char_num, match_height)
    target = (card_w, card_h)

    img = Image.new("RGBA", (based_w, based_h))
    if match_height is None:
        div_d = _fit_bar_width(Image.open(TEXT_PATH / "div_d.png"), based_w)
        img.paste(div_d, (0, CHAR_DIV_Y), div_d)

    rows = max(1, math.ceil(char_num / cols) if char_num else 1)
    y_slack = based_h - head - foot - rows * card_h
    card_y0 = head + max(0, y_slack // 2)

    for index, char in enumerate(char_datas):
        char_star = char["rarity"]
        char_id = char["id"]
        char_talent = char["actived_constellation_num"]
        char_fetter = char["fetter"]
        char_lv = char["level"]

        weapon = char["weapon"]
        weapon_star = min(max(int(weapon["rarity"]), 1), 5)
        weapon_name = weapon["name"]
        weapon_lv = weapon["level"]
        weapon_affix = weapon["affix_level"]

        char_bg = Image.open(TEXT_PATH / f"char_bg{char_star}.png")
        weapon_bg = Image.open(TEXT_PATH / f"weapon{weapon_star}.png")
        char_icon = _open_rgba(CHAR_PATH / f"{char_id}.png", (256, 256))
        talent_icon = Image.open(TEXT_PATH / "mz" / f"{char_talent}.png")
        fetter_icon = Image.open(TEXT_PATH / "hg" / f"{char_fetter}.png")
        weapon_icon = _open_rgba(WEAPON_PATH / f"{weapon_name}.png", (174, 174))

        char_card_path = CHAR_NAMECARDPIC_PATH / f"{char_id}.png"
        if char_card_path.exists():
            char_card = Image.open(char_card_path).convert("RGBA")
        else:
            char_card = Image.new("RGBA", (560, 268))

        weapon_icon = weapon_icon.resize((174, 174)).convert("RGBA")
        char_card = char_card.resize((560, 268))

        char_bg.paste(char_card, (32, 29), char_mask)
        char_bg.paste(char_icon, (43, 35), char_icon)
        char_bg.paste(weapon_bg, (343, 33), weapon_bg)
        char_bg.paste(weapon_icon, (366, 55), weapon_icon)
        char_bg.paste(char_fg, (0, 0), char_fg)
        char_bg.paste(talent_icon, (273, 55), talent_icon)
        char_bg.paste(fetter_icon, (273, 124), fetter_icon)

        char_draw = ImageDraw.Draw(char_bg)
        char_draw.text((110, 261), f"Lv{char_lv}", "White", gs_font_30, "mm")
        char_draw.text((453, 264), weapon_name, "White", gs_font_28, "mm")
        char_draw.text((496, 212), f"Lv{weapon_lv}", "White", gs_font_28, "mm")
        char_draw.text((513, 80), str(weapon_affix), "White", gs_font_28, "mm")

        char_bg = char_bg.resize(target, Image.Resampling.LANCZOS)
        img.paste(
            char_bg,
            (
                pad_x + (index % cols) * (card_w + CHAR_GAP_X),
                card_y0 + (index // cols) * card_h,
            ),
            char_bg,
        )

    return img


async def draw_char_pic(uid: str) -> str | bytes:
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes, bytearray, memoryview)):
        return raw_data

    img = await _draw_char_pic(uid, raw_data)
    if isinstance(img, (bytes, str)):
        return img
    elif isinstance(img, (bytearray, memoryview)):
        return bytes(img)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    return await convert_img(bg)
