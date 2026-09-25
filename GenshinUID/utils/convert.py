import re
from typing import Tuple, Union, Optional, overload

from gsuid_core.bot import Bot
from gsuid_core.i18n import t
from gsuid_core.logger import logger
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind

UID_LEN_MIN = 9
UID_LEN_MAX = 10
# 完整数字串才算 UID，避免把 10 位截成前 9 位。
_UID_RE = re.compile(rf"(?<!\d)\d{{{UID_LEN_MIN},{UID_LEN_MAX}}}(?!\d)")


def is_genshin_uid(uid: str) -> bool:
    return uid.isdigit() and UID_LEN_MIN <= len(uid) <= UID_LEN_MAX


def split_uid_from_text(text: str) -> tuple[str | None, str]:
    matched = _UID_RE.search(text)
    if matched is None:
        return None, text
    uid = matched.group(0)

    def _repl(item: re.Match[str]) -> str:
        if item.group(0) == uid:
            return ""
        return item.group(0)

    return uid, _UID_RE.sub(_repl, text)


@overload
async def get_uid(bot: Bot, ev: Event) -> Optional[str]: ...


@overload
async def get_uid(bot: Bot, ev: Event, get_user_id: bool = True) -> Tuple[Optional[str], str]: ...


async def get_uid(bot: Bot, ev: Event, get_user_id: bool = False) -> Union[Optional[str], Tuple[Optional[str], str]]:
    uid, ev.text = split_uid_from_text(ev.text)
    user_id = ev.at if ev.at and (ev.bot_id != ev.at and ev.bot_self_id != ev.at) else ev.user_id
    if uid is None:
        data = await GsBind.select_data(user_id, ev.bot_id)
        if data is not None:
            if not data.group_id:
                await GsBind.update_data(user_id, ev.bot_id, group_id=ev.group_id)
            else:
                new_group_list = data.group_id.split("|")
                if ev.group_id and ev.group_id not in new_group_list:
                    new_group_list.append(ev.group_id)
                    new_group = "|".join(new_group_list)
                    await GsBind.update_data(user_id, ev.bot_id, group_id=new_group)
        uid = await GsBind.get_uid_by_game(user_id, ev.bot_id)
    logger.info(t("log.genshinuid.uid_uid_b166a6", uid=uid))
    if get_user_id:
        return uid, user_id
    return uid
