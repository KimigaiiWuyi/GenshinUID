from gsuid_core.utils.plugins_config.gs_config import StringConfig

from .config_default import CONIFG_DEFAULT
from ..utils.resource.RESOURCE_PATH import CONFIG_PATH

gsconfig = StringConfig('GenshinUID', CONFIG_PATH, CONIFG_DEFAULT)
