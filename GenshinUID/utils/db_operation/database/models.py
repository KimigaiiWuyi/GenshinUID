import asyncio
import threading
from typing import Optional

from pydantic import BaseModel

from .db_config import Field, SQLModel, engine


class CK(BaseModel):
    __table_args__ = {'keep_existing': True}
    UID: int
    CK: str


class PushData(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    UID: int = Field(default=100000000, primary_key=True, title='UID')
    CoinPush: Optional[str] = Field(title='洞天宝钱推送')
    CoinValue: Optional[int] = Field(title='洞天宝钱阈值')
    CoinIsPush: Optional[str] = Field(title='洞天宝钱是否已推送')
    ResinPush: Optional[str] = Field(title='体力推送')
    ResinValue: Optional[int] = Field(title='体力阈值')
    ResinIsPush: Optional[str] = Field(title='体力是否已推送')
    GoPush: Optional[str] = Field(title='派遣推送')
    GoValue: Optional[int] = Field(title='派遣阈值')
    GoIsPush: Optional[str] = Field(title='派遣是否已推送')
    TransformPush: Optional[str] = Field(title='质变仪推送')
    TransformValue: Optional[int] = Field(title='质变仪阈值')
    TransformIsPush: Optional[str] = Field(title='质变仪是否已推送')


class UidData(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    USERID: str = Field(default='WX_100001', primary_key=True, title='WX号')
    UID: Optional[str] = Field(title='UID')
    MYSID: Optional[str] = Field(title='米游社通行证(废弃)')


class NewCookiesTable(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    UID: int = Field(default=100000000, primary_key=True, title='UID')
    Cookies: str = Field(title='CK')
    QID: str = Field(title='QQ号')
    StatusA: str = Field(title='全局推送开关')
    StatusB: str = Field(title='自动签到')
    StatusC: str = Field(title='自动米游币')
    NUM: Optional[int] = Field(title='废弃值')
    Extra: Optional[str] = Field(title='备注')
    Stoken: Optional[str] = Field(title='SK')


class CookiesCache(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    UID: Optional[str] = Field(default='100000000', primary_key=True)
    MYSID: Optional[str] = Field(title='米游社通行证')
    Cookies: str = Field(title='CK')


class Config(SQLModel, table=True):
    __table_args__ = {'keep_existing': True}
    Name: str = Field(default='Config', primary_key=True, title='设置项')
    Status: Optional[str] = Field(title='开启状态')
    GroupList: Optional[str] = Field(title='群组')
    Extra: Optional[str] = Field(title='额外选项')


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


threading.Thread(target=lambda: asyncio.run(create_all()), daemon=True).start()
