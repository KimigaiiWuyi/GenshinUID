from typing import Any, Dict, List, Union, Optional

from gsuid_core.bot import Bot
from gsuid_core.message_models import Button


async def send_diff_msg(
    bot: Bot,
    code: Any,
    data: Optional[Dict] = None,
    option_list: Optional[
        Union[List[str], List[Button], List[List[str]], List[List[Button]]]
    ] = None,
):
    if data is None:
        data = {
            0: '绑定UID成功!',
            -1: 'UID的位数不正确!',
            -2: 'UID已经绑定过了!',
            -3: '你输入了错误的格式!',
        }
    for retcode in data:
        if code == retcode:
            return await bot.send_option(
                data[retcode], option_list, False, '\n'
            )
