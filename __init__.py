from pathlib import Path

from nonebot import load_plugins

load_plugins(str(Path(__file__).parent / "GenshinUID"))
