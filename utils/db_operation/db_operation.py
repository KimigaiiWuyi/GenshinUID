from typing import List, Union, Optional

from .database.ConfigDAL import ConfigDAL
from .database.CookiesDAL import CookiesDAL
from .database.UidDataDAL import UidDataDAL
from .database.PushDataDAL import PushDataDAL
from .database.db_config import async_session


async def get_push_status(uid, func) -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            PushData = PushDataDAL(session)
            push_dict = await PushData.get_user_data(uid)
            if push_dict:
                if f'{func}Push' in push_dict:
                    return [
                        push_dict[f'{func}Push'],
                        push_dict[f'{func}Value'],
                    ]
            return []


async def update_push_status(uid: int, func: str, status: str) -> bool:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            PushData = PushDataDAL(session)
            return await PushData.update_user_data(
                uid, {f'{func}Push': status}
            )


async def update_push_value(uid: int, func: str, value: int) -> bool:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            PushData = PushDataDAL(session)
            return await PushData.update_user_data(
                uid, {f'{func}Value': value}
            )


async def update_is_pushed(
    uid: int, func: str, is_pushed: str = 'off'
) -> bool:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            PushData = PushDataDAL(session)
            return await PushData.update_user_data(
                uid, {f'{func}IsPush': is_pushed}
            )


async def bind_db(userid, uid=None, mys=None):
    async with async_session() as session:  # type: ignore
        async with session.begin():
            UidData = UidDataDAL(session)
            im = await UidData.bind_db(userid, {'UID': uid, 'MYSID': mys})
            return im


async def get_all_uid() -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            UidData = UidDataDAL(session)
            lst = await UidData.get_all_uid_list()
            return lst


async def get_all_cookie() -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            lst = await Cookies.get_all_cookie_list()
            return lst


async def get_all_stoken() -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            lst = await Cookies.get_all_stoken_list()
            return lst


async def select_db(userid, mode='auto') -> Union[List, str, None]:
    """
    :说明:
      选择绑定uid/mys库
    :参数:
      * userid (str): QQ号。
      * mode (str): 模式如下
        * auto(默认): 自动选择(优先mys)
        * uid: 选择uid库
        * mys: 选择mys库
        * list: 返回uid列表
    :返回:
      * data (list): 返回获取值
      mode为list时返回uid列表
      其他情况下data[0]为需要的uid/mysid
      data[1]表示data[0]是`uid` or `mysid`
    """
    async with async_session() as session:  # type: ignore
        async with session.begin():
            UidData = UidDataDAL(session)
            if mode == 'auto':
                im = await UidData.get_anyid(userid)
            elif mode == 'uid':
                im = await UidData.get_uid(userid)
            elif mode == 'mys':
                im = await UidData.get_mysid(userid)
            elif mode == 'list':
                im = await UidData.get_uid_list(userid)
            else:
                return None
            return im


async def switch_db(userid: int, uid: Optional[str] = None) -> str:
    """
    :说明:
      切换绑定的UID列表,绑定一个UID的情况下返回无法切换
      切换前 -> 12_13_14
      切换后 -> 13_14_12
    :参数:
      * userid (str): QQ号。
    :返回:
      * im (str): 回调信息。
    """
    async with async_session() as session:  # type: ignore
        async with session.begin():
            UidData = UidDataDAL(session)
            im = await UidData.switch_uid(userid, uid)
            return im


async def delete_db(userid: int, data: dict) -> str:
    """
    :说明:
      删除当前绑定的UID信息
      删除前 -> 12_13_14
      删除后 -> 13_14
    :参数:
      * userid (str): QQ号。
    :返回:
      * im (str): 回调信息。
    """
    async with async_session() as session:  # type: ignore
        async with session.begin():
            UidData = UidDataDAL(session)
            im = await UidData.delete_db(userid, data)
            return im


async def cookies_db(uid: str, cookies: str, qid: int):
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.add_cookie_db(qid, uid, cookies)
            return im


async def error_db(cookies: str, error: str):
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.add_error_db(cookies, error)
            return im


async def owner_cookies(uid: str) -> str:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            owner_ck = await Cookies.get_user_ck(uid)
            return str(owner_ck)


async def get_stoken(uid: str) -> str:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            stoken = await Cookies.get_user_stoken(uid)
            return str(stoken)


async def get_user_bind_data(uid: str) -> dict:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            lst = await Cookies.get_user_data_dict(uid)
            return lst


async def stoken_db(s_cookies: str, uid: str) -> str:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.add_stoken_db(uid, s_cookies)
            return im


async def open_push(uid, qid, status, func):
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.update_user_status(
                uid, {'QID': qid, func: status}
            )
            return im


async def config_check(func, mode='CHECK') -> bool:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Config = ConfigDAL(session)
            im = False
            if mode == 'CHECK':
                im = await Config.config_check(func)
            elif mode == 'OPEN':
                im = await Config.config_update(func, 'on')
            elif mode == 'CLOSED':
                im = await Config.config_update(func, 'off')
            return im


async def get_all_signin_list() -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.get_status_list('StatusB')
            return im


async def get_all_push_list() -> List:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.get_status_list('StatusA')
            return im


async def get_push_data(uid: int) -> dict:
    async with async_session() as session:  # type: ignore
        async with session.begin():
            PushData = PushDataDAL(session)
            push_data = await PushData.get_user_data(uid)
            return push_data


async def cache_db(uid):
    async with async_session() as session:  # type: ignore
        async with session.begin():
            Cookies = CookiesDAL(session)
            im = await Cookies.get_random_ck(uid)
            return im
