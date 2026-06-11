from typing import Dict, List, Union


def _bt(button: Dict):
    from nonebot.adapters.qq.models import (
        Action,
        Button,
        Permission,
        RenderData,
    )

    action = button["action"]
    if action == -1:
        action = 2
    enter = None
    if action == 1:
        action = 2
        enter = True
    return Button(
        render_data=RenderData(
            label=button["text"],
            visited_label=button["pressed_text"],
            style=button["style"],
        ),
        action=Action(
            type=action,
            permission=Permission(
                type=button["permisson"],
                specify_role_ids=button["specify_role_ids"],
                specify_user_ids=button["specify_user_ids"],
            ),
            enter=enter,
            unsupport_tips=button["unsupport_tips"],
            data=button["data"],
        ),
    )


def _kb(buttons: Union[List[Dict], List[List[Dict]]]):
    from nonebot.adapters.qq.models import (
        InlineKeyboard,
        MessageKeyboard,
        InlineKeyboardRow,
    )

    _rows = []
    _buttons = []
    _buttons_rows = []
    for button in buttons:
        if isinstance(button, Dict):
            _buttons.append(_bt(button))
            if len(_buttons) >= 2:
                _rows.append(InlineKeyboardRow(buttons=_buttons))
                _buttons = []
        else:
            _buttons_rows.append([_bt(b) for b in button])

    if _buttons:
        _rows.append(InlineKeyboardRow(buttons=_buttons))
    if _buttons_rows:
        _rows.extend([InlineKeyboardRow(buttons=b) for b in _buttons_rows])

    return MessageKeyboard(content=InlineKeyboard(rows=_rows))


def _tg_kb(button: Dict):
    from nonebot.adapters.telegram.model import InlineKeyboardButton

    return InlineKeyboardButton(
        text=button["text"],
        callback_data=button["data"],
    )


def _dc_kb(button: Dict):
    from nonebot.adapters.discord.api import Button, ButtonStyle

    return Button(
        label=button["text"],
        custom_id=button["data"],
        style=ButtonStyle.Primary,
    )
