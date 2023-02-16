from pathlib import Path

from nonebot import load_plugins

dir_ = Path(__file__).parent
load_plugins(str(dir_ / 'GenshinUID'))
