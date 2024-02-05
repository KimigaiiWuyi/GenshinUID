import re
from typing import Tuple, Union, Optional, overload

from gsuid_core.bot import Bot
from gsuid_core.models import Event
from gsuid_core.utils.database.models import GsBind


@overload
async def get_uid(bot: Bot, ev: Event) -> Optional[str]: ...


@overload
async def get_uid(
    bot: Bot, ev: Event, get_user_id: bool = True
) -> Tuple[Optional[str], str]: ...


async def get_uid(
    bot: Bot, ev: Event, get_user_id: bool = False
) -> Union[Optional[str], Tuple[Optional[str], str]]:
    uid_data = re.findall(r'\d{9}', ev.text)
    user_id = ev.at if ev.at else ev.user_id
    if uid_data:
        uid: Optional[str] = uid_data[0]
        if uid:
            ev.text = ev.text.replace(uid, '')
    else:
        data = await GsBind.select_data(user_id, ev.bot_id)
        if data is not None:
            if not data.group_id:
                await GsBind.update_data(
                    user_id, ev.bot_id, group_id=ev.group_id
                )
            else:
                new_group_list = data.group_id.split('|')
                if ev.group_id and ev.group_id not in new_group_list:
                    new_group_list.append(ev.group_id)
                    new_group = '|'.join(new_group_list)
                    await GsBind.update_data(
                        user_id, ev.bot_id, group_id=new_group
                    )
        uid = await GsBind.get_uid_by_game(user_id, ev.bot_id)
    if get_user_id:
        return uid, user_id
    return uid
