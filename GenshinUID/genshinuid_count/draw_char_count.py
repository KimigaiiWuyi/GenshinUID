import asyncio
from typing import Tuple, Union, Literal
from pathlib import Path

from PIL import Image, ImageDraw

from gsuid_core.models import Event
from gsuid_core.ai_core.trigger_bridge import ai_return

from ..genshinuid_enka.res import div, draw_ring, skill_mask, value_mask, draw_new_title
from ..utils.image.convert import convert_img
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_fetter_pic,
    get_talent_pic,
    get_weapon_affix_pic,
)
from ..utils.fonts.genshin_fonts import (
    gs_font_24,
    gs_font_26,
    gs_font_28,
)
from ..utils.resource.RESOURCE_PATH import CHAR_PATH, WEAPON_PATH

black_color = (24, 24, 24)
white_color = (245, 245, 245)
TEXT_PATH = Path(__file__).parent / "texture2d"

level_color = {
    5: (230, 0, 0),
    4: (203, 131, 21),
    3: (97, 17, 156),
    2: (17, 105, 156),
    1: (94, 96, 95),
}

level_map = {
    "skill": {
        10: 5,
        7: 4,
        5: 3,
        3: 2,
        0: 1,
    },
    "equip": {33: 5, 27: 4, 21: 3, 15: 2, 0: 1},
    "percent": {99: 5, 90: 4, 85: 3, 70: 2, 0: 1},
}
star_color_map = {
    "1": (94, 96, 95),
    "2": (17, 105, 156),
    "3": (91, 141, 192),
    "4": (143, 123, 174),
    "5": (205, 135, 76),
}


async def get_color(type: Literal["skill", "equip", "percent"], value: int) -> Tuple[int, int, int]:
    for v in level_map[type]:
        if value >= v:
            level = level_map[type][v]
            break
    else:
        level = 1
    return level_color[level]


async def draw_char_count_list(
    uid: str,
    ev: Event,
) -> Union[str, bytes]:
    title_data = await draw_new_title(ev, uid)
    if isinstance(title_data, str):
        return title_data
    elif isinstance(title_data, bytes):
        return title_data

    title, char_done_list = title_data

    if len(char_done_list) > 86:
        _mode = 3
    else:
        _mode = 2

    char_done_list.sort(key=lambda x: (-x["score_value"]))

    # AI 注入：提取毕业度统计数据
    try:
        top_chars = char_done_list[:10]
        parts = [f"【UID {uid} 毕业度统计】共 {len(char_done_list)} 个角色"]
        # 统计评分分布
        score_5 = sum(1 for c in char_done_list if c["score_value"] >= 80)
        score_4 = sum(1 for c in char_done_list if 60 <= c["score_value"] < 80)
        score_3 = sum(1 for c in char_done_list if c["score_value"] < 60)
        parts.append(f"  评分分布: 优秀(≥80) {score_5}个  良好(60-79) {score_4}个  一般(<60) {score_3}个")
        parts.append("  --- TOP 10 ---")
        for c in top_chars:
            parts.append(
                f"  {c['char_name']}: 评分{c['score_value']} "
                f"A{c['a_skill_level']} E{c['e_skill_level']} Q{c['q_skill_level']} "
                f"词条{c['value']}条 武器:{c['weapon_name']}{c['weapon_affix']}阶 Lv{c['weapon_level']}"
            )
        if len(char_done_list) > 10:
            parts.append(f"  ...及其他 {len(char_done_list) - 10} 个角色")
        ai_return("\n".join(parts))
    except Exception:
        pass

    rows = (len(char_done_list) + _mode - 1) // _mode
    h = 750 + 80 + 90 * rows
    img = get_v4_bg(2370 if _mode == 3 else 1600, h, 200)

    img.paste(title, (0, 0), title)

    tasks = []
    for index, char in enumerate(char_done_list):
        tasks.append(draw_single_rank(img, char, index, _mode))
    await asyncio.gather(*tasks)

    img = add_footer(img, 900 if _mode == 3 else 700)
    img.paste(div, (0, h - 61), div)
    res = await convert_img(img)
    return res


async def draw_single_rank(img: Image.Image, char: dict, index: int, _mode: int):
    char_id = char["id"]

    if char["value"] >= 24 and (char["a_skill_level"] >= 8 or char["e_skill_level"] >= 8 or char["q_skill_level"] >= 8):
        char_rank = Image.open(TEXT_PATH / "char_rank_yes.png")
    else:
        char_rank = Image.open(TEXT_PATH / "char_rank.png")

    char_pic = Image.open(CHAR_PATH / f"{char_id}.png")
    weapon_star = int(char["weapon_star"])
    char_pic = draw_ring(char_pic, char["char_star"])
    weapon_pic = Image.open(WEAPON_PATH / f"{char['weapon_name']}.png")
    weapon_pic = draw_ring(weapon_pic, weapon_star)

    char_rank.paste(char_pic, (8, 0), char_pic)
    char_rank.paste(weapon_pic, (472, 0), weapon_pic)

    char_rank_draw = ImageDraw.Draw(char_rank)
    # 角色名称
    char_rank_draw.text(
        (98, 31),
        char["char_name"][:4],
        "white",
        gs_font_28,
        "lm",
    )

    # AEQ等级
    for s_index, s in enumerate(["a", "e", "q"]):
        s_offset = s_index * 38
        skill_color_img = Image.new(
            "RGBA",
            (35, 28),
            await get_color("skill", char[f"{s}_skill_level"]),
        )
        char_rank.paste(skill_color_img, (99 + s_offset, 48), skill_mask)
        char_rank_draw.text(
            (116 + s_offset, 62),
            str(char[f"{s}_skill_level"]),
            white_color,
            gs_font_26,
            "mm",
        )

    # 圣遗物词条数
    value_color_img = Image.new(
        "RGBA",
        (77, 33),
        await get_color("equip", char["value"]),
    )
    char_rank.paste(value_color_img, (225, 28), value_mask)
    char_rank_draw.text(
        (263, 45),
        f"{str(char['value'])[:4]}条",
        white_color,
        gs_font_24,
        "mm",
    )

    # 好感和天赋
    fetter_pic = await get_fetter_pic(char["fetter"])
    fetter_pic = fetter_pic.resize((77, 33))
    talent_pic = await get_talent_pic(char["talent_num"])
    talent_pic = talent_pic.resize((66, 33))

    char_rank.paste(fetter_pic, (308, 28), fetter_pic)
    char_rank.paste(talent_pic, (391, 28), talent_pic)

    # 武器
    weapon_affix_pic = await get_weapon_affix_pic(char["weapon_affix"])
    char_rank.paste(weapon_affix_pic, (561, 47), weapon_affix_pic)
    char_rank_draw.text(
        (635, 61),
        f"Lv.{char['weapon_level']}",
        "white",
        gs_font_26,
        "lm",
    )
    char_rank_draw.text(
        (559, 27),
        str(char["weapon_name"][:7]),
        "white",
        gs_font_26,
        "lm",
    )

    img.paste(
        char_rank,
        (50 + (index % _mode) * 750, 750 + 90 * (index // _mode)),
        char_rank,
    )
