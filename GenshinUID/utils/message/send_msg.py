from typing import List

from ...base import hoshino_bot


# 发送聊天记录
async def send_forward_msg(
    bot: hoshino_bot,
    group_id: int,
    name: str,
    uin: str,
    msgs: List[str],
):
    def to_json(msg):
        return {
            "type": "node",
            "data": {"name": name, "uin": uin, "content": msg},
        }

    messages = [to_json(msg) for msg in msgs]
    await bot.call_action(
        action='send_group_forward_msg', group_id=group_id, messages=messages
    )
