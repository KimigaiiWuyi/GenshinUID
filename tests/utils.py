from nonebot.adapters.onebot.v11 import Adapter, Message
from nonebot.adapters.onebot.v11.event import Sender, Event


def make_event(
        sender: Sender,
        message: Message = None,
        time: int = 0,
        self_id: int = 10000,
        post_type: str = "message",
        message_type: str = "private",
        sub_type: str = "friend",
        group_id: int = 10002,
        anonymous: dict = None,
        message_id: int = 1,
        user_id: int = 10001,
        font: int = 0,
        **kwargs
) -> Event:
    """
        :说明:

          根据消息类型自动生成事件。
          参数遵循 OneBot V11 标准
          https://github.com/botuniverse/onebot-11/blob/master/event/message.md

        :参数:

          * ``time: int = 0``: 事件发生的时间戳。
          * ``self_id: int = 10000``: 收到事件的机器人 QQ 号。
          * ``post_type: str = "message"``: 上报类型。
          * ``message_type: str = "private"``: 消息类型，`friend` 是私聊消息，`group是群消息`。
          * ``sub_type: str = "friend"``: 消息子类型：
            * 私聊消息：如果是好友则是 `friend`，如果是群临时会话则是 `group`。
            * 群消息：正常消息是 normal，匿名消息是 anonymous，系统提示（如「管理员已禁止群内匿名聊天」）是 notice
          * ``message_id: int = 1``: 消息 ID。
          * ``user_id: int = 10001``: 发送者 QQ 号。
          * ``message: Message = None``: 消息内容。
          * ``font: int = 0``: 字体。
          * ``sender: Sender = None``: 	发送人信息。
    """
    raw_message: str = message.extract_plain_text()
    return Adapter.json_to_event({
        "time": time,
        "self_id": self_id,
        "post_type": post_type,
        "message_type": message_type,
        "sub_type": sub_type,
        "message_id": message_id,
        "user_id": user_id,
        "message": message,
        "raw_message": raw_message,
        "font": font,
        "sender": sender,
        "group_id": group_id,
        "anonymous": anonymous,
        **kwargs
    })


def make_sender(
        user_id: int = 10001,
        nickname: str = "test",
        sex: str = "unknown",
        age: int = 1,
        card: str = "test",
        area: str = "北京",
        level: str = "1",
        role: str = "owner",
        title: str = "test"
):
    """
        :说明:
          生成发送人信息类型。
          参数遵循 OneBot V11 标准
          https://github.com/botuniverse/onebot-11/blob/master/event/message.md


        :参数:

          * ``user_id: int = 10001``: 发送者 QQ 号。
          * ``nickname: str = "test"``: 昵称。
          * ``sex: str = "unknown"``: 性别，`male` 或 `female` 或 `unknown`。
          * ``age: int = 1``: 年龄。
          * ``card: str = "test"``: 群名片／备注。
          * ``area: str = "北京"``: 地区。
          * ``level: str = "1"``: 成员等级。
          * ``role: str = "owner"``: 角色，`owner` 或 `admin` 或 `member`。
          * ``title: str = "test"``: 专属头衔。
    """

    return Sender(user_id=user_id, nickname=nickname, sex=sex, age=age,
                  card=card, area=area, level=level, role=role, title=title)
