"""体力邮箱提醒：开启后树脂溢出走邮箱，优先于群/私聊推送。"""

from __future__ import annotations

import re
from typing import Dict, Tuple, Optional

from gsuid_core.logger import logger
from gsuid_core.subscribe import gs_subscribe
from gsuid_core.meta_plugins import import_api

SPECIAL_TASK = "[原神] 特别提醒"
EMAIL_REMIND_NAMES = ("邮箱提醒", "特别提醒")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email_remind_text(text: str) -> bool:
    return text.startswith(EMAIL_REMIND_NAMES)


def default_qq_email(user_id: str) -> str:
    return f"{user_id}@qq.com"


def extract_email(text: str) -> Optional[str]:
    for part in text.replace(",", " ").split():
        if _EMAIL_RE.match(part):
            return part
    return None


def compose_resin_mail(uid: str, current: int, threshold: str) -> Tuple[str, str]:
    subject = f"【邮箱提醒】原神体力即将溢出 - UID{uid}"
    body = f"UID{uid} 的树脂/体力快满了。\n当前体力：{current}\n你设置的阈值：{threshold}\n请尽快上线清理体力。\n"
    return subject, body


async def get_special_email_map() -> Dict[str, str]:
    rows = await gs_subscribe.get_subscribe(SPECIAL_TASK)
    result: Dict[str, str] = {}
    if not rows:
        return result
    for item in rows:
        if item.uid and item.extra_message and _EMAIL_RE.match(item.extra_message):
            result[str(item.uid)] = item.extra_message
    return result


async def send_resin_special_mail(email: str, uid: str, current: int, threshold: str) -> bool:
    subject, body = compose_resin_mail(uid, current, threshold)
    # 顶层 import 会让没装 gscore_mail 的用户整包加载失败
    if import_api("gscore_mail") is None:
        logger.warning("[原神邮箱提醒] gscore_mail 未安装，回退到会话推送")
        return False
    from gscore_mail.api import send

    result = await send(to=email, subject=subject, body=body)
    if result["ok"]:
        logger.info(f"[原神邮箱提醒] 已邮件提醒 UID{uid} -> {email} 体力={current}")
        return True
    logger.warning(f"[原神邮箱提醒] 邮件发送失败 UID{uid} -> {email}: {result['message']}")
    return False
