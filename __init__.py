import os.path

import nonebot

nonebot.load_plugins(
    os.path.split(__file__)[0]
)
