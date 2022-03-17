import os.path

from nonebot import load_plugins, logger

load_plugins(
    os.path.dirname(__file__)
)

logger.warning('我们更推荐用本项目目录下的GenshinUID包作为插件加载，而不是整个项目')
logger.warning('本项目目录下的__init__.py仅作适配用')
