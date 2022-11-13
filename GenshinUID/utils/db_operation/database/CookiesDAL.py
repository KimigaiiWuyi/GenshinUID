from typing import List, Optional

from nonebot.log import logger
from sqlalchemy.sql import text
from sqlalchemy.future import select
from sqlalchemy import delete, update
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import CookiesCache, NewCookiesTable


class CookiesDAL:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_user_data(self, uid: str) -> Optional[NewCookiesTable]:
        try:
            await self.db_session.execute(
                ('ALTER TABLE NewCookiesTable ' 'ADD COLUMN Stoken TEXT')  # type: ignore
            )
        except Exception:
            pass
        sql = select(NewCookiesTable).where(NewCookiesTable.UID == uid)
        result = await self.db_session.execute(sql)
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

    async def get_user_ck(self, uid: str) -> str:
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

    async def get_user_ck_valid(self, uid: str) -> bool:
        data = await self.get_user_data(uid)
        if data and data.Extra:
            return False
        elif data is None:
            return False
        else:
            return True

    async def get_user_stoken(self, uid: str) -> Optional[str]:
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
            # 有可能返回None
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
        result = await self.db_session.execute(sql)
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
        result = await self.db_session.execute(sql)
        data = result.scalars().all()
        sk_list = []
        for item in data:
            sk_list.append(item.Stoken)
        return sk_list

    async def get_cache_ck(self, uid: str) -> Optional[str]:
        """
        :说明:
          获取缓存Cookies
        :参数:
          * uid (int): UID。
        :返回:
          * cookies (str): Cookies。
        """
        sql = select(CookiesCache).where(CookiesCache.UID == uid)
        result = await self.db_session.execute(sql)
        data = result.scalars().all()
        if data:
            return data[0].Cookies
        return None

    async def get_random_ck(self, uid: str) -> str:
        """
        :说明:
          获取随机Cookies并写入缓存
        :参数:
          * uid (int): UID。
        :返回:
          * cookies (str): Cookies。
        """
        cache_data = await self.get_cache_ck(uid)
        if await self.user_exists(uid) and await self.get_user_ck_valid(uid):
            return await self.get_user_ck(uid)
        elif cache_data:
            return cache_data
        else:
            regioncode = 0
            try:
                regioncode = int(uid[0])
            except:
                logger.info('[随机Cookie]uid不合法！')
                return 'uid不正确，请检查uid格式！'

            if regioncode < 6:
                # cn server
                sql = (
                    select(NewCookiesTable)
                    .where(
                        text(
                            "cast(substr(newcookiestable.uid,1,1) as int) < 6"
                        )
                    )
                    .order_by(func.random())
                )
            else:
                # os server
                sql = (
                    select(NewCookiesTable)
                    .where(
                        text(
                            "cast(substr(newcookiestable.uid,1,1) as int) >= 6"
                        )
                    )
                    .order_by(func.random())
                )

            a = await self.db_session.execute(sql)
            random_data: List[NewCookiesTable] = a.scalars().all()
            if random_data:
                for data in random_data:
                    if data.Extra:
                        continue
                    else:
                        return_ck = data.Cookies
                        await self.add_cache_db(return_ck, uid, None)
                        return return_ck
                else:
                    return '没有可以使用的Cookies！'
            else:
                return '没有可以使用的Cookies！'

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
        a = await self.db_session.execute(sql)
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
        await self.db_session.flush()
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
                .values(Cookies=cookies, Extra=None)
            )
            await self.db_session.execute(sql)
        else:
            new_data = NewCookiesTable(
                UID=int(uid),
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
        await self.db_session.flush()
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
            await self.db_session.execute(sql)
            msg = f'UID{uid}账户的Stoken绑定成功!'
        else:
            msg = '请先绑定Cookies~'
        await self.db_session.flush()
        return msg

    async def delete_user(self, uid: str) -> bool:
        """
        :说明:
          从NewCookiesTable中删除一行用户数据
        :参数:
          * uid (int): UID。
        :返回:
          * msg (str): 更新文字信息。
        """
        if await self.user_exists(uid):
            sql = delete(NewCookiesTable).where(
                NewCookiesTable.UID == int(uid)
            )
            await self.db_session.execute(sql)
            return True
        else:
            return False

    async def delete_cache(self):
        sql = (
            update(NewCookiesTable)
            .where(NewCookiesTable.Extra == 'limit30')
            .values(Extra=None)
        )
        empty_sql = delete(CookiesCache)
        await self.db_session.execute(sql)
        await self.db_session.execute(empty_sql)

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
            await self.db_session.execute(sql)
            msg = f'UID{uid}的推送状态更新成功!'
        else:
            msg = '请先绑定Cookies~'
        await self.db_session.flush()
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
        await self.db_session.execute(sql)
        await self.db_session.flush()
        return True
