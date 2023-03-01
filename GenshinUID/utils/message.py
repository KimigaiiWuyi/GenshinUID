from typing import Any, Dict

from gsuid_core.bot import Bot


async def send_diff_msg(bot: Bot, code: Any, data: Dict):
    for retcode in data:
        if code == retcode:
            return await bot.send(data[retcode])
