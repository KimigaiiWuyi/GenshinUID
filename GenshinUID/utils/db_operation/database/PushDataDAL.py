from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from .models import PushData


class PushDataDAL:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_user_data(self, uid: int):
        """
        :说明:
          添加用户的绑定信息
        :参数:
          * data (dict): 数据信息。
        :返回:
            * data (bool): True/False。
        """
        new_data = PushData(
            UID=uid,
            CoinPush='off',
            CoinValue=2100,
            CoinIsPush='off',
            ResinPush='on',
            ResinValue=140,
            ResinIsPush='off',
            GoPush='off',
            GoValue=120,
            GoIsPush='off',
            TransformPush='off',
            TransformValue=140,
            TransformIsPush='off',
        )
        self.db_session.add(new_data)
        await self.db_session.flush()  # type: ignore

    async def update_user_data(self, uid: int, data: dict) -> bool:
        """
        :说明:
          更新用户的绑定信息
        :参数:
          * uid (int): UID。
          * data (dict): 数据信息。
        :返回:
          * data (bool): True/False。
        """
        if not await self.user_exists(uid):
            await self.add_user_data(uid)
        sql = update(PushData).where(PushData.UID == uid).values(**data)
        await self.db_session.execute(sql)  # type: ignore
        await self.db_session.flush()  # type: ignore
        return True

    async def get_user_data(self, uid: int) -> dict:
        """
        :说明:
          获取用户的绑定信息
        :参数:
          * userid (int): QQ号。
        :返回:
          * data[0] (UidData): 数据信息。
        """
        if await self.user_exists(uid):
            sql = select(PushData).where(PushData.UID == uid)
            result = await self.db_session.execute(sql)  # type: ignore
            data = result.scalars().all()
            if data:
                return data[0].__dict__
        return {}

    async def user_exists(self, uid: int) -> bool:
        """
        :说明:
          是否存在用户的绑定信息
        :参数:
          * userid (int): QQ号。
        :返回:
          * data (bool): True/False。
        """
        sql = select(PushData).where(PushData.UID == uid)
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        if data:
            return True
        await self.add_user_data(uid)
        return True
