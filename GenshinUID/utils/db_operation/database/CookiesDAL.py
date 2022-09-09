from typing import List, Union, Optional

from sqlalchemy.future import select
from sqlalchemy import Column, update
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import CookiesCache, NewCookiesTable


class CookiesDAL:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_data(self, uid: str) -> Optional[NewCookiesTable]:
        try:
            await self.db_session.execute(
                ('ALTER TABLE NewCookiesTable ' 'ADD COLUMN Stoken TEXT')
            )
        except Exception:
            pass
        sql = select(NewCookiesTable).where(NewCookiesTable.UID == uid)
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        if data:
            return data[0]
        else:
            return None

    async def get_user_data_dict(self, uid: str) -> dict:
        data = await self.get_user_data(uid)
        if data:
            return data.__dict__
        else:
            return {}

    async def get_user_ck(self, uid: str) -> Union[Column[str], str]:
        """
        :说明:
          获取Cookies
        :参数:
          * uid (int): UID。
        :返回:
          * cookies (str): Cookies。
        """
        data = await self.get_user_data(uid)
        if data:
            return data.Cookies
        else:
            return '该用户没有绑定过Cookies噢~'

    async def get_user_stoken(self, uid: str) -> Union[Column[str], str]:
        """
        :说明:
          获取Stoken
        :参数:
          * cookies (str): Cookies。
        :返回:
          * stoken (str): SToken。
        """
        data = await self.get_user_data(uid)
        if data:
            return data.Stoken
        else:
            return '该用户没有绑定过Stoken噢~'

    async def get_all_cookie_list(self) -> List[str]:
        """
        :说明:
          获得所有Cookies列表
        :返回:
          * ck_list (List[str]): Cookie列表。
        """
        sql = select(NewCookiesTable).where(NewCookiesTable.Cookies != '')
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        ck_list = []
        for item in data:
            ck_list.append(item.Cookies)
        return ck_list

    async def get_all_stoken_list(self) -> List[str]:
        """
        :说明:
          获得所有Stoken列表
        :返回:
          * sk_list (List[str]): stoken列表。
        """
        sql = select(NewCookiesTable).where(NewCookiesTable.Stoken != '')
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        sk_list = []
        for item in data:
            sk_list.append(item.Stoken)
        return sk_list

    async def get_cache_ck(self, uid: str) -> Union[Column[str], str, None]:
        """
        :说明:
          获取缓存Cookies
        :参数:
          * uid (int): UID。
        :返回:
          * cookies (str): Cookies。
        """
        sql = select(CookiesCache).where(CookiesCache.UID == uid)
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        if data:
            return data[0].Cookies
        return None

    async def get_random_ck(self, uid: str) -> Union[Column[str], str]:
        """
        :说明:
          获取随机Cookies并写入缓存
        :参数:
          * uid (int): UID。
        :返回:
          * cookies (str): Cookies。
        """
        cache_data = await self.get_cache_ck(uid)
        if await self.user_exists(uid):
            return await self.get_user_ck(uid)
        elif cache_data:
            return cache_data
        else:
            sql = select(NewCookiesTable).order_by(func.random())
            a = await self.db_session.execute(sql)  # type: ignore
            random_data = a.scalars().all()
            if random_data:
                return_ck = random_data[0].Cookies
                await self.add_cache_db(return_ck, uid, None)
                return return_ck
            else:
                return '没有可以使用的数据~,请先用'

    async def get_status_list(self, status) -> List:
        if status == 'StatusA':
            temp = NewCookiesTable.StatusA
        elif status == 'StatusB':
            temp = NewCookiesTable.StatusB
        elif status == 'StatusC':
            temp = NewCookiesTable.StatusC
        else:
            temp = NewCookiesTable.StatusA
        sql = select(NewCookiesTable).filter(temp != 'off')
        a = await self.db_session.execute(sql)  # type: ignore
        data_list = a.scalars().all()
        uid_list = []
        for data in data_list:
            uid_list.append(data.__dict__)
        return uid_list

    async def user_exists(self, uid: str) -> bool:
        data = await self.get_user_data(uid)
        if data:
            return True
        else:
            return False

    async def add_cache_db(
        self, cookies: str, uid: Optional[str], mysid: Optional[str]
    ) -> bool:
        """
        :说明:
          缓存CK
        :参数:
          * cookies (str): ck。
          * uid (str): uid。
          * mysid (str): mysid。
        :返回:
          * bool: 是否成功。
        """
        if uid is None:
            uid = 'None'
        new_cache = CookiesCache(
            UID=uid,
            Cookies=cookies,
            MYSID=mysid,
        )
        self.db_session.add(new_cache)
        await self.db_session.flush()  # type: ignore
        return True

    async def add_cookie_db(self, userid: int, uid: str, cookies: str) -> bool:
        """
        :说明:
          绑定Cookies
        :参数:
          * userid (int): QQ号。
          * uid (int): UID。
          * cookies (str): Cookies。
        :返回:
          * msg (str): 绑定文字信息。
        """
        if await self.user_exists(uid):
            sql = (
                update(NewCookiesTable)
                .where(NewCookiesTable.UID == uid)
                .values(Cookies=cookies)
            )
            await self.db_session.execute(sql)  # type: ignore
        else:
            new_data = NewCookiesTable(
                UID=uid,
                Cookies=cookies,
                QID=userid,
                StatusA='off',
                StatusB='off',
                StatusC='off',
                NUM=140,
                Extra=None,
                Stoken=None,
            )
            self.db_session.add(new_data)
        await self.db_session.flush()  # type: ignore
        return True

    async def add_stoken_db(self, uid: str, stoken: str) -> str:
        """
        :说明:
          绑定Stoken
        :参数:
          * uid (int): UID。
          * stoken (str): Stoken。
        :返回:
          * msg (str): 绑定文字信息。
        """
        if await self.user_exists(uid):
            sql = (
                update(NewCookiesTable)
                .where(NewCookiesTable.UID == uid)
                .values(Stoken=stoken)
            )
            await self.db_session.execute(sql)  # type: ignore
            msg = f'UID{uid}账户的Stoken绑定成功!'
        else:
            msg = '请先绑定Cookies~'
        await self.db_session.flush()  # type: ignore
        return msg

    async def update_user_status(self, uid: str, data: dict) -> str:
        """
        :说明:
          更新用户状态
        :参数:
          * uid (int): UID。
          * data (dict): 数据。
            {'QID': '', 'StatusA': 'on', 'StatusB': 'on', 'StatusC': 'on'}
        :返回:
          * msg (str): 更新文字信息。
        """
        if await self.user_exists(uid):
            sql = (
                update(NewCookiesTable)
                .where(NewCookiesTable.UID == uid)
                .values(**data)
            )
            await self.db_session.execute(sql)  # type: ignore
            msg = f'UID{uid}的推送状态更新成功!'
        else:
            msg = '请先绑定Cookies~'
        await self.db_session.flush()  # type: ignore
        return msg

    async def add_error_db(self, cookies: str, err: str) -> bool:
        """
        :说明:
          为绑定的Cookies添加错误信息
        :参数:
          * cookies (str): Cookies。
          * err (str): 错误信息。
            ['limit30', 'error']
        :返回:
          * msg (str): 绑定文字信息。
        """
        sql = (
            update(NewCookiesTable)
            .where(NewCookiesTable.Cookies == cookies)
            .values(Extra=err)
        )
        await self.db_session.execute(sql)  # type: ignore
        await self.db_session.flush()  # type: ignore
        return True
