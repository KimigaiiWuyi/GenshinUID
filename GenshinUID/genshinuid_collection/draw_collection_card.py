from typing import Union
from pathlib import Path

from gsuid_core.models import Event

from ..utils.mys_api import get_base_data

TEXT_PATH = Path(__file__).parent / "texture2D"


async def draw_explore_card(ev: Event, uid: str) -> Union[str, bytes]:
    from ..genshinuid_roleinfo.draw_roleinfo_card import draw_pic

    return await draw_pic(ev, uid, include_chars=False)


__all__ = ["TEXT_PATH", "get_base_data", "draw_explore_card"]
