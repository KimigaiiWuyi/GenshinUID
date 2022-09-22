from typing import Optional, cast

from nonebot.adapters.qqguild.api.model import User


def cast_to_int(user: Optional[User]) -> int:
    return cast(int, cast(User, user).id)
