from typing import Union, Literal
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.utils.error_reply import get_error
from gsuid_core.ai_core.trigger_bridge import ai_return

from ..version import Genshin_version
from ..utils.image.convert import convert_img
from ..utils.map.name_covert import name_to_avatar_id
from ..utils.api.teyvat.models import WeaponData, CharacterData
from ..utils.image.image_tools import get_v4_bg, add_footer
from ..utils.api.teyvat.request import teyvat_api
from ..utils.fonts.genshin_fonts import gs_font_24, gs_font_30, gs_font_38
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, WEAPON_PATH

TEXT_PATH = Path(__file__).parent / "texture2d"
COLOR_MAP = {
    1.5: (241, 18, 18),
    1.3: (112, 18, 241),
    1.1: (49, 88, 192),
    0.8: (66, 114, 14),
}


async def draw_item(
    item: Union[CharacterData, WeaponData],
    _type: Literal["char", "weapon"],
):
    days = item["days"]
    lv_str = item["history"][-1]
    last_version = float(lv_str[:3])
    version_cut = float(Genshin_version[:3]) - last_version

    for rg in COLOR_MAP:
        if version_cut >= rg:
            color = COLOR_MAP[rg]
            break
    else:
        color = (37, 37, 37)

    if _type == "char":
        char_id = await name_to_avatar_id(item["role"])
        item_img = Image.open(CHAR_PATH / f"{char_id}.png")
    else:
        item_img = Image.open(WEAPON_PATH / f"{item['role']}.png")

    star = item["star"]
    item_bg = Image.open(TEXT_PATH / f"star{star}.png")
    item_draw = ImageDraw.Draw(item_bg)

    item_img = item_img.resize((164, 164))
    item_img = item_img.convert("RGBA")
    item_bg.paste(item_img, (25, 35), item_img)

    item_draw.rounded_rectangle((55, 30, 155, 60), fill=color, radius=20)

    """
    item_draw.text(
        (105, 244),
        '未复刻天数',
        'white',
        gs_font_26,
        'mm',
    )
    """

    item_draw.text(
        (105, 228),
        f"{days}天",
        "white",
        gs_font_38,
        "mm",
    )

    item_draw.text(
        (105, 45),
        f"{lv_str[:-1]}",
        "white",
        gs_font_24,
        "mm",
    )
    return item_bg


async def draw_teyvat_returnlist_img():
    data = await teyvat_api.get_return_list()
    if isinstance(data, int):
        return get_error(data)

    version = data["version"]
    char5_list = data["result"][0][:12]
    char4_list = data["result"][1][:12]
    weapon5_list = data["result"][2][:12]
    _weapon4_list = data["result"][3][:12]

    # AI 注入：提取未复刻数据
    try:
        parts = [f"【未复刻天数排行】版本 {version}"]
        parts.append("五星角色 (按未复刻天数排序):")
        for c in char5_list[:8]:
            days = c["days"]
            history = c.get("history", [])
            last_up = history[-1] if history else "未知"
            star = c.get("star", 5)
            parts.append(f"  {c['role']}({star}★): {days}天未复刻 (上次UP: {last_up})")
        parts.append("四星角色:")
        for c in char4_list[:5]:
            parts.append(f"  {c['role']}: {c['days']}天未复刻 (上次UP: {c['history'][-1]})")
        parts.append("五星武器:")
        for w in weapon5_list[:8]:
            parts.append(f"  {w['role']}: {w['days']}天未复刻 (上次UP: {w['history'][-1]})")
        ai_return("\n".join(parts))
    except Exception:
        pass

    weapon4_list = []
    for weapon4 in _weapon4_list:
        weapon4["star"] = 4
        weapon4_list.append(weapon4)

    w, h = 1400, 500 + 150 + 100 + 110

    len1 = (((len(char5_list) - 1) // 6) + 1) * 274
    len2 = (((len(char4_list) - 1) // 6) + 1) * 274
    len3 = (((len(weapon5_list) - 1) // 6) + 1) * 274
    len4 = (((len(weapon4_list) - 1) // 6) + 1) * 274

    h += len1 + len2 + len3 + len4

    img = get_v4_bg(w, h)

    title = Image.open(TEXT_PATH / "title.png")
    title_draw = ImageDraw.Draw(title)

    bar1 = Image.open(TEXT_PATH / "bar1.png")
    bar2 = Image.open(TEXT_PATH / "bar2.png")

    title_draw.text(
        (643, 356),
        f"{version}",
        (255, 255, 255),
        gs_font_30,
        "mm",
    )

    img.paste(title, (0, 0), title)

    img.paste(bar1, (0, 540), bar1)

    for i, item in enumerate(char5_list):
        x = (i % 6) * 210 + 67
        y = (i // 6) * 274 + 623

        item = await draw_item(item, "char")
        img.paste(item, (x, y), item)

    for i, item in enumerate(char4_list):
        x = (i % 6) * 210 + 67
        y = (i // 6) * 274 + 623 + len1

        item = await draw_item(item, "char")
        img.paste(item, (x, y), item)

    img.paste(bar2, (0, 540 + 90 + 40 + len1 + len2), bar2)

    for i, item in enumerate(weapon5_list):
        x = (i % 6) * 210 + 67
        y = (i // 6) * 274 + 623 + len1 + len2 + 90 + 40

        item = await draw_item(item, "weapon")
        img.paste(item, (x, y), item)

    for i, item in enumerate(weapon4_list):
        x = (i % 6) * 210 + 67
        y = (i // 6) * 274 + 623 + len1 + len2 + len3 + 90 + 40

        item = await draw_item(item, "weapon")
        img.paste(item, (x, y), item)

    img = add_footer(img, w)
    res = await convert_img(img)
    return res
