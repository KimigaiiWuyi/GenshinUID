from nonebot import get_driver

config = get_driver().config
SUPERUSERS = {int(x) for x in config.superusers}
priority = 2
