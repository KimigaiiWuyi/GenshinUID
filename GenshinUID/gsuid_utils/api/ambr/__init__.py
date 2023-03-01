"""
安柏计划 API 包装：
书籍信息；
角色信息;
武器信息;
"""
from .models import AmbrBook as AmbrBook  # noqa: F401
from .models import AmbrWeapon as AmbrWeapon  # noqa: F401
from .models import AmbrCharacter as AmbrCharacter  # noqa: F401
from .models import AmbrBookDetail as AmbrBookDetail  # noqa: F401
from .request import get_story_data as get_story_data  # noqa: F401
from .request import get_all_book_id as get_all_book_id  # noqa: F401
from .request import get_book_volume as get_book_volume  # noqa: F401
from .request import get_ambr_char_data as get_ambr_char_data  # noqa: F401
from .request import get_ambr_event_info as get_ambr_event_info  # noqa: F401
from .request import get_ambr_weapon_data as get_ambr_weapon_data  # noqa: F401

__all__ = ["request", "models", "utils"]
