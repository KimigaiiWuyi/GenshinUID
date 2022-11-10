from nonebot import get_driver

config = get_driver().config
SUPERUSERS = {x for x in config.superusers}
priority = 2
