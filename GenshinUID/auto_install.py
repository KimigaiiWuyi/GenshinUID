import asyncio
import subprocess

from git.repo import Repo
from pip._internal import main as pip_install

from .path import RUN_CORE, CORE_PATH, GSUID_PATH

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
    done, _ = await asyncio.wait([_install()])
    for future in done:
        if future.result is None:
            return '安装出现错误, 请查看控制台信息！'
    return '安装成功...'


async def start():
    subprocess.Popen(
        ['poetry', 'run', 'python', 'core.py'],
        cwd=f'{RUN_CORE}',
    )
    return '启动成功完成...'
