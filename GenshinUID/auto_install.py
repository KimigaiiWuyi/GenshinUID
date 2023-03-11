import asyncio
import subprocess

from git.repo import Repo
from nonebot.log import logger
from pip._internal import main as pip_install

from .path import CORE_PATH, GSUID_PATH

GS_GIT = 'https://ghproxy.com/https://github.com/KimigaiiWuyi/GenshinUID.git'
CORE_GIT = 'https://ghproxy.com/https://github.com/Genshin-bots/gsuid_core.git'


async def _install():
    if not CORE_PATH.exists():
        Repo.clone_from(CORE_GIT, CORE_PATH, single_branch=True, depth=1)
    if not GSUID_PATH.exists():
        Repo.clone_from(
            GS_GIT, GSUID_PATH, b='v4', single_branch=True, depth=1
        )
    try:
        import poetry.__version__ as poetry_version

        if float(poetry_version.__version__[:3]) < 1.4:
            pip_install(['install', 'poetry'])
    except ImportError:
        pip_install(['install', 'poetry'])
    subprocess.call(['poetry', 'install'], cwd=f'{CORE_PATH}')


async def install():
    done = await asyncio.gather(_install())
    logger.info(done)
    return '安装成功...'


async def start():
    subprocess.Popen(
        ['poetry', 'run', 'python', 'gsuid_core/core.py'],
        cwd=f'{CORE_PATH}',
    )
    return '启动成功完成...'
