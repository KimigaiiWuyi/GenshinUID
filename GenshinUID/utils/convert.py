import re
from typing import Tuple, Union, Optional, overload

from gsuid_core.bot import Bot
from gsuid_core.models import Event

from .mys_api import mys_api
from .database import get_sqla
from .error_reply import VERIFY_HINT
from ..gsuid_utils.api.mys.models import AbyssData, IndexData


@overload
async def get_uid(bot: Bot, ev: Event) -> Optional[str]:
    ...


@overload
async def get_uid(
    bot: Bot, ev: Event, get_user_id: bool = True
) -> Tuple[Optional[str], str]:
    ...


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
        sqla = get_sqla(ev.bot_id)
        uid = await sqla.get_bind_uid(user_id)
    if get_user_id:
        return uid, user_id
    return uid


class GsCookie:
    def __init__(self) -> None:
        self.cookie: Optional[str] = None
        self.uid: str = '0'
        self.raw_data = None
        self.sqla = get_sqla('TEMP')

    async def get_cookie(self, uid: str) -> str:
        self.uid = uid
        while True:
            self.cookie = await self.sqla.get_random_cookie(uid)
            if self.cookie is None:
                return '没有可以使用的cookie!'
            await self.get_uid_data()
            msg = await self.check_cookies_useable()
            if isinstance(msg, str):
                return msg
            elif msg:
                return ''

    async def get_uid_data(self) -> Union[int, IndexData]:
        data = await mys_api.get_info(self.uid, self.cookie)
        if not isinstance(data, int):
            self.raw_data = data
        return data

    async def get_spiral_abyss_data(
        self, schedule_type: str = '1'
    ) -> Union[AbyssData, int]:
        data = await mys_api.get_spiral_abyss_info(
            self.uid, schedule_type, self.cookie
        )
        return data

    async def check_cookies_useable(self):
        if isinstance(self.raw_data, int) and self.cookie:
            retcode = self.raw_data
            if retcode == 10001:
                await self.sqla.mark_invalid(self.cookie, 'error')
                return False
                # return '您的cookie已经失效, 请重新获取!'
            elif retcode == 10101:
                await self.sqla.mark_invalid(self.cookie, 'limit30')
                return False
                # return '当前查询CK已超过每日30次上限!'
            elif retcode == 10102:
                return '当前查询id已经设置了隐私, 无法查询!'
            elif retcode == 1034:
                return VERIFY_HINT
            else:
                return f'API报错, 错误码为{retcode}!'
        else:
            return True
