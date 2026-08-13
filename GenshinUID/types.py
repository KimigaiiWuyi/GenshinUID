from typing import Any, Literal, TypedDict

UserType = Literal["group", "direct", "channel", "sub_channel"]


class SenderInfo(TypedDict, total=False):
    nickname: str
    name: str
    avatar: str
    user_id: str


class ButtonPayload(TypedDict, total=False):
    text: str
    data: str
    action: int
    style: int
    pressed_text: str
    permisson: int
    specify_role_ids: list[str]
    specify_user_ids: list[str]
    unsupport_tips: str


class TemplateMarkdown(TypedDict):
    template_id: str
    para: dict[str, str]


class BanPayload(TypedDict, total=False):
    user_id: str
    group_id: str
    duration: int | str


class DeletePayload(TypedDict, total=False):
    message_id: str


class NodeItem(TypedDict, total=False):
    type: str
    data: Any
