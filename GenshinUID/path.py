from pathlib import Path

from nonebot import get_driver

driver = get_driver()

_CORE_PATH = Path().cwd().parent / 'gsuid_core'

CORE_PATH = (
    Path(driver.config.gsuid_core_path)
    if hasattr(driver.config, 'gsuid_core_path')
    else _CORE_PATH
)

GSUID_PATH = CORE_PATH / 'gsuid_core' / 'plugins' / 'GenshinUID'
