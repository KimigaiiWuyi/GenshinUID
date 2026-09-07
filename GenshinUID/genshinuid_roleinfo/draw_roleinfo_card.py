from typing import Union

from gsuid_core.models import Event
from gsuid_core.utils.api.mys.models import IndexData, MihoyoAvatar
from gsuid_core.ai_core.trigger_bridge import ai_return

from .draw_all_char import _load_char_datas, _prepare_char_datas
from .html_roleinfo import render_roleinfo_html
from ..utils.mys_api import get_base_data
from ..utils.image.image_tools import get_avatar


def _ai_return_roleinfo(uid: str, raw_data: IndexData, include_chars: bool) -> None:
    try:
        stats = raw_data["stats"]
        head = f"【UID {uid} 角色信息面板】" if include_chars else f"【UID {uid} 探索收集】"
        parts = [head]
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
        if include_chars:
            for a in raw_data["avatars"][:8]:
                parts.append(f"  {a['name']}: Lv{a['level']} {a['actived_constellation_num']}命 好感{a['fetter']}")
        else:
            for world in raw_data["world_explorations"]:
                parts.append(f"  {world['name']}: {world['exploration_percentage'] / 10:.1f}%")
        ai_return("\n".join(parts))
    except Exception:
        pass


async def draw_pic(
    ev: Event,
    uid: str,
    raw_data: IndexData | None = None,
    char_datas: list[MihoyoAvatar] | None = None,
    *,
    include_chars: bool = True,
) -> Union[str, bytes]:
    if raw_data is None:
        loaded = await get_base_data(uid)
        if isinstance(loaded, (str, bytes)):
            return loaded
        elif isinstance(loaded, (bytearray, memoryview)):
            return bytes(loaded)
        raw_data = loaded

    _ai_return_roleinfo(uid, raw_data, include_chars)

    if include_chars:
        if char_datas is None:
            loaded_chars = await _load_char_datas(uid, raw_data)
            if isinstance(loaded_chars, (str, bytes)):
                return loaded_chars
            elif isinstance(loaded_chars, (bytearray, memoryview)):
                return bytes(loaded_chars)
            char_datas = loaded_chars
        char_datas = await _prepare_char_datas(char_datas)
    else:
        char_datas = []

    char_pic = await get_avatar(ev, 377, False)
    return await render_roleinfo_html(uid, raw_data, char_datas, char_pic, include_chars=include_chars)
