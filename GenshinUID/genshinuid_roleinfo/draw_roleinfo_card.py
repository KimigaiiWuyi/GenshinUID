from typing import Union

from PIL import Image

from gsuid_core.models import Event
from gsuid_core.utils.image.convert import convert_img
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


async def draw_pic(ev: Event, uid: str) -> Union[str, bytes]:
    img = await _draw_pic(ev, uid)
    if isinstance(img, (bytes, str)):
        return img
    elif isinstance(img, (bytearray, memoryview)):
        return bytes(img)

    bg = get_v4_bg(img.size[0], img.size[1])
    bg.paste(img, (0, 0), img)

    return await convert_img(bg)


async def _draw_pic(ev: Event, uid: str) -> Union[str, bytes, Image.Image]:
    raw_data = await get_base_data(uid)
    if isinstance(raw_data, (str, bytes)):
        return raw_data
    elif isinstance(raw_data, (bytearray, memoryview)):
        return bytes(raw_data)

    # AI 注入：提取角色信息面板数据
    try:
        stats = raw_data["stats"]
        avatars = raw_data.get("avatars", [])
        parts = [f"【UID {uid} 角色信息面板】"]
        parts.append(f"活跃天数: {stats['active_day_number']}  获得角色数: {stats['avatar_number']}")
        parts.append(f"成就数: {stats['achievement_number']}  深渊: {stats.get('spiral_abyss', 'N/A')}")
        # 宝箱统计
        chest_total = (
            stats.get("common_chest_number", 0)
            + stats.get("exquisite_chest_number", 0)
            + stats.get("precious_chest_number", 0)
            + stats.get("luxurious_chest_number", 0)
            + stats.get("magic_chest_number", 0)
        )
        parts.append(
            f"宝箱总数: {chest_total}  "
            f"传送点: {stats.get('way_point_number', 'N/A')}  "
            f"秘境: {stats.get('domain_number', 'N/A')}"
        )
        if avatars:
            for a in avatars[:8]:
                name = a.get("name", str(a["id"]))
                level = a.get("level", "?")
                fetter = a.get("fetter", "?")
                const = a.get("actived_constellation_num", 0)
                weapon = a.get("weapon", {})
                w_name = weapon.get("name", "?")
                w_level = weapon.get("level", "?")
                parts.append(f"  {name}: Lv{level} {const}命 好感{fetter} 武器:{w_name}Lv{w_level}")
        ai_return("\n".join(parts))
    except Exception:
        pass

    char_img = await _draw_char_pic(uid, raw_data)
    explore_img = await _draw_explore(raw_data)
    if isinstance(char_img, (bytes, str)):
        return char_img
    elif isinstance(char_img, (bytearray, memoryview)):
        return bytes(char_img)

    char_pic = await get_avatar(ev, 377, False)
    title_img = get_v4_title(char_pic, uid, raw_data)

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
    img = add_footer(img)
    return img
