import re
from typing import Any

from ..db_operation.db_operation import select_db


async def get_uid(user_id: Any, raw_mes: str) -> str:
    uid = re.findall(r'\d{9}', raw_mes)
    if uid:
        uid = uid[0]
    else:
        uid = await select_db(user_id, mode='uid')
        uid = str(uid)
    return uid
