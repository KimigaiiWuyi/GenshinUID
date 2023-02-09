from typing import List

from nonebot.adapters.onebot.v11 import Bot


# 发送聊天记录
async def send_forward_msg(
    bot: Bot,
    groupid: int,
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
    await bot.call_api(
        "send_group_forward_msg", group_id=groupid, messages=messages
    )
