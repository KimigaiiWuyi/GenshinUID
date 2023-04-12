import os
import json
import time
import platform
import subprocess
from pathlib import Path

from ..genshinuid_config.gs_config import gsconfig

bot_start = Path(__file__).parents[4] / 'core.py'
restart_sh_path = Path().cwd() / 'gs_restart.sh'
update_log_path = Path(__file__).parent / 'update_log.json'

_restart_sh = '''#!/bin/bash
kill -9 {}
{} &'''

restart_command = gsconfig.get_config('restart_command').data


async def get_restart_sh() -> str:
    args = f'{restart_command} {str(bot_start.absolute())}'
    return _restart_sh.format(str(bot_start.absolute()), args)


async def restart_genshinuid(
    bot_id: str, send_type: str, send_id: str
) -> None:
    pid = os.getpid()
    restart_sh = await get_restart_sh()
    with open(restart_sh_path, "w", encoding="utf8") as f:
        f.write(restart_sh)
    if platform.system() == 'Linux':
        os.system(f'chmod +x {str(restart_sh_path)}')
        os.system(f'chmod +x {str(bot_start)}')
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    update_log = {
        'type': 'restart',
        'msg': '重启完成!',
        'bot_id': bot_id,
        'send_type': send_type,
        'send_to': send_id,
        'time': now_time,
    }
    with open(str(update_log_path), 'w', encoding='utf-8') as f:
        json.dump(update_log, f)
    if platform.system() == 'Linux':
        subprocess.Popen(
            f'kill -9 {pid} & {restart_command} {bot_start}',
            shell=True,
        )
    else:
        subprocess.Popen(
            f'taskkill /F /PID {pid} & {restart_command} {bot_start}',
            shell=True,
        )


async def restart_message() -> dict:
    if update_log_path.exists():
        with open(update_log_path, 'r', encoding='utf-8') as f:
            update_log = json.load(f)
        msg = f'{update_log["msg"]}\n重启时间:{update_log["time"]}'
        update_log['msg'] = msg
        os.remove(update_log_path)
        os.remove(restart_sh_path)
        return update_log
    else:
        return {}
