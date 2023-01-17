from typing import List

from nonebot import get_driver


def get_superusers() -> List[int]:
    config = get_driver().config
    superusers: List[int] = []
    for su in config.superusers:
        if "onebot:" in su:
            # su[7:] == onebot:
            su = su[7:]
        if su.isdigit():
            superusers.append(int(su))
    return superusers
