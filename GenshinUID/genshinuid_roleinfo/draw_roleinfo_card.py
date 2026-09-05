from typing import Union

from PIL import Image

from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
from gsuid_core.utils.api.mys.models import IndexData, MihoyoAvatar
from gsuid_core.ai_core.trigger_bridge import ai_return
from gsuid_core.utils.image.image_tools import easy_alpha_composite

from .draw_all_char import _draw_char_pic
from ..utils.mys_api import get_base_data
from ..utils.image.image_tools import (
    get_v4_bg,
    add_footer,
    get_avatar,
    get_v4_title,
)
from ..genshinuid_collection.draw_new_collection_card import _draw_explore

CHAR_SIDE_MIN = 21
TITLE_TO_EXPLORE_Y = 650


async def draw_pic(
    ev: Event,
    uid: str,
    raw_data: IndexData | None = None,
    char_datas: list[MihoyoAvatar] | None = None,
) -> Union[str, bytes]:
    img = await _draw_pic(ev, uid, raw_data=raw_data, char_datas=char_datas)
    if isinstance(img, (bytes, str)):
        return img
    elif isinstance(img, (bytearray, memoryview)):
        return bytes(img)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    return await convert_img(bg)


async def _draw_pic(
    ev: Event,
    uid: str,
    raw_data: IndexData | None = None,
    char_datas: list[MihoyoAvatar] | None = None,
) -> Union[str, bytes, Image.Image]:
    if raw_data is None:
        loaded = await get_base_data(uid)
        if isinstance(loaded, (str, bytes)):
            return loaded
        elif isinstance(loaded, (bytearray, memoryview)):
            return bytes(loaded)
        raw_data = loaded

    # AI 注入：提取角色信息面板数据
    try:
        stats = raw_data["stats"]
        avatars = raw_data["avatars"]
        parts = [f"【UID {uid} 角色信息面板】"]
        parts.append(f"活跃天数: {stats['active_day_number']}  获得角色数: {stats['avatar_number']}")
        parts.append(f"成就数: {stats['achievement_number']}  深渊: {stats['spiral_abyss']}")
        chest_total = (
            stats["common_chest_number"]
            + stats["exquisite_chest_number"]
            + stats["precious_chest_number"]
            + stats["luxurious_chest_number"]
            + stats["magic_chest_number"]
        )
        parts.append(f"宝箱总数: {chest_total}  传送点: {stats['way_point_number']}  秘境: {stats['domain_number']}")
        for a in avatars[:8]:
            name = a["name"]
            level = a["level"]
            fetter = a["fetter"]
            const = a["actived_constellation_num"]
            parts.append(f"  {name}: Lv{level} {const}命 好感{fetter}")
        ai_return("\n".join(parts))
    except Exception:
        pass

    explore_img = await _draw_explore(raw_data)
    char_count = raw_data["stats"]["avatar_number"]
    side_by_side = char_count >= CHAR_SIDE_MIN
    match_height = TITLE_TO_EXPLORE_Y + explore_img.size[1] if side_by_side else None

    char_img = await _draw_char_pic(
        uid,
        raw_data,
        match_height=match_height,
        char_datas=char_datas,
    )
    if isinstance(char_img, (bytes, str)):
        return char_img
    elif isinstance(char_img, (bytearray, memoryview)):
        return bytes(char_img)

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

    if side_by_side:
        left_w = max(title_img.size[0], explore_img.size[0])
        left_h = TITLE_TO_EXPLORE_Y + explore_img.size[1]
        img = Image.new("RGBA", (left_w + char_img.size[0], left_h))
        img.paste(title_img, (0, 0), title_img)
        img = easy_alpha_composite(img, explore_img, (0, TITLE_TO_EXPLORE_Y))
        img = easy_alpha_composite(img, char_img, (left_w, 0))
        return add_footer(img)

    w = char_img.size[0]
    h = char_img.size[1] + explore_img.size[1] + 560
    o = 150

    img = Image.new("RGBA", (w, h))
    img.paste(title_img, (0, 0), title_img)
    img = easy_alpha_composite(
        img,
        explore_img,
        (-int((explore_img.size[0] - char_img.size[0]) / 2), 500 + o),
    )
    img = easy_alpha_composite(img, char_img, (0, 500 + explore_img.size[1] - 110 + o))
    return add_footer(img)
