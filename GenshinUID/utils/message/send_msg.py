from typing import List

from nonebot.adapters.onebot.v11 import Bot


# 发送聊天记录
async def send_forward_msg(
    bot: Bot,
    userid: int,
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
        "send_private_forward_msg", user_id=userid, messages=messages
    )