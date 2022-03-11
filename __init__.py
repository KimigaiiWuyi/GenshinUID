import os.path

import nonebot

nonebot.load_plugin(
    os.path.join(
        os.path.split(__file__)[0], 'GenshinUID'
    )
)
