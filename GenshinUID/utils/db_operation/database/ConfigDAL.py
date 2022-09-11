from typing import Union

from sqlalchemy import update
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from .models import Config


class ConfigDAL:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def get_config(self, func: str) -> Union[Config, None]:
        """
        :说明:
          获取配置信息
        :参数:
          * func (str): 功能名称。
        :返回:
          * data (Config): 配置信息。
        """
        sql = select(Config).where(Config.Name == func)
        result = await self.db_session.execute(sql)  # type: ignore
        data = result.scalars().all()
        if data:
            return data[0]
        else:
            return None

    async def config_check(self, func: str) -> bool:
        """
        :说明:
          检查配置状态是否为关闭
          开启为True, 关闭为False
        :参数:
          * func (str): 功能名称。
        :返回:
          * data (bool): True/False。
        """
        data = await self.get_config(func)
        if data:
            if data.Status != 'off':
                return True
            else:
                return False
        else:
            return False

    async def add_config(self, func: str, status: str) -> bool:
        """
        :说明:
          添加配置信息
        :参数:
          * func (str): 功能名称。
            * status (str): 状态。
        :返回:
            * data (bool): True/False。
        """
        new_config = Config(
            Name=func, Status=status, GroupList=None, Extra=None
        )
        self.db_session.add(new_config)
        await self.db_session.flush()  # type: ignore
        return True

    async def config_update(self, func: str, status: str) -> bool:
        """
        :说明:
          更新配置信息
        :参数:
          * func (str): 功能名称。
          * status (str): 状态。
        :返回:
          * data (bool): True/False。
        """
        if not await self.get_config(func):
            await self.add_config(func, status)
        sql = update(Config).where(Config.Name == func).values(Status=status)
        await self.db_session.execute(sql)  # type: ignore
        await self.db_session.flush()  # type: ignore
        return True
