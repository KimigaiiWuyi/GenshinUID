import json

import aiofiles
from gsuid_core.gss import gss
from gsuid_core.data_store import get_res_path


async def reset_sv_config() -> str:
    path = get_res_path().parent / 'gsuid_core' / 'config.json'
    if path.exists():
        async with aiofiles.open(path, 'rb') as f:
            config = json.loads(await f.read())
            config['sv'] = {}
        async with aiofiles.open(path, 'w') as f:
            await f.write(json.dumps(config, indent=4))
        gss.load_plugins()
        return '成功重置配置文件！发送[gs重启]以应用配置...'
    else:
        return '未找到配置文件, 请尝试使用命令[gs重启]后重试...'
