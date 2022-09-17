import os
import json
import time
from pathlib import Path

bot_start = Path().cwd() / 'bot.py'
restart_sh_path = Path().cwd() / 'gs_restart.sh'
update_log_path = Path(__file__).parent / 'update_log.json'

restart_sh = '''#!/bin/bash
kill -9 {}
python {} &
'''.format(
    str(bot_start.absolute()), str(bot_start.absolute())
)


async def restart_genshinuid(send_type: str, send_id: str) -> None:
    if not restart_sh_path.exists():
        with open(restart_sh_path, "w", encoding="utf8") as f:
            f.write(restart_sh)
        os.system(f'chmod +x {str(restart_sh_path)}')
    now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    update_log = {
        'type': 'restart',
        'msg': '重启完成!',
        'send_type': send_type,
        'send_to': send_id,
        'time': now_time,
    }
    with open(str(update_log_path), 'w', encoding='utf-8') as f:
        json.dump(update_log, f)
    os.execl(str(restart_sh_path), ' ')


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
