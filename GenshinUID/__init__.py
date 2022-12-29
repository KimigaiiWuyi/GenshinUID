from pathlib import Path
from pkgutil import iter_modules
from nonebot.log import logger
from nonebot import require, load_all_plugins, get_plugin_by_module_name

from .config import config as _config

require('nonebot_plugin_apscheduler')

if get_plugin_by_module_name("GenshinUID"):
    logger.info("推荐直接加载 GenshinUID 仓库文件夹")
    load_all_plugins(
        [
            f"GenshinUID.{module.name}"
            for module in iter_modules([str(Path(__file__).parent)])
            if module.ispkg
            and (
                (name := module.name[11:]) == "meta"
                or name not in _config.disabled_plugins
            )
            # module.name[:11] == genshinuid_
        ],
        [],
    )
