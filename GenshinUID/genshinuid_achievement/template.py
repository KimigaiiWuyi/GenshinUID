import json
from pathlib import Path

import aiofiles

from gsuid_core.server import on_core_start

path = Path(__file__).parent
all_achi = {}
daily_achi = {}


@on_core_start
async def load_data():
    async with aiofiles.open(path / "all_achi.json", "r", encoding="UTF-8") as f:
        all_achi.update(json.loads(await f.read()))

    async with aiofiles.open(path / "daily_achi.json", "r", encoding="UTF-8") as f:
        daily_achi.update(json.loads(await f.read()))


daily_template = """任务：【{}】
成就：【{}】
描述：【{}】
攻略：【{}】
"""

achi_template = """合辑：【{}】
成就：【{}】
描述：【{}】
"""
