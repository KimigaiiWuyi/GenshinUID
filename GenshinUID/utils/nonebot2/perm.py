from nonebot.permission import Permission
from nonebot.adapters.qqguild.event import DirectMessageCreateEvent


async def is_direct(_: DirectMessageCreateEvent) -> bool:
    return True


DIRECT = Permission(is_direct)
