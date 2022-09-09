from pathlib import Path

from nonebot.log import logger
from nonebot import load_plugins

gsuid_path = Path(__file__).parent
WARNING = f"""
不推荐直接加载 GenshinUID 仓库文件夹，请使用 pip 安装此包，然后使用加载插件的方式加载
安装命令：
使用 pip：<y>pip install {gsuid_path}</y>
{
    (
        "使用 nb-cli：<y>nb plugin install git+https://github.com/"
        "KimigaiiWuyi/GenshinUID.git@nonebot2-beta1#egg=GenshinUID</y>"
    )
}
加载插件：<blue>https://v2.nonebot.dev/docs/tutorial/plugin/load-plugin</blue>
"""

logger.opt(colors=True).warning(WARNING)
load_plugins(str(gsuid_path / "GenshinUID"))
