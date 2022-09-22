import asyncio
import threading
from typing import Optional

from sqlmodel import Field, SQLModel

from .db_config import engine


class PushData(SQLModel, table=True):
    UID: int = Field(default=100000000, primary_key=True)
    CoinPush: Optional[str]
    CoinValue: Optional[int]
    CoinIsPush: Optional[str]
    ResinPush: Optional[str]
    ResinValue: Optional[int]
    ResinIsPush: Optional[str]
    GoPush: Optional[str]
    GoValue: Optional[int]
    GoIsPush: Optional[str]
    TransformPush: Optional[str]
    TransformValue: Optional[int]
    TransformIsPush: Optional[str]


class UidData(SQLModel, table=True):
    ID: int = Field(
        default=1, primary_key=True, sa_column_kwargs={"autoincrement": 1}
    )
    USERID: str = Field(default="100000000", primary_key=True)
    UID: Optional[str]
    MYSID: Optional[str]


class NewCookiesTable(SQLModel, table=True):
    UID: int = Field(default=100000000, primary_key=True)
    Cookies: str
    QID: str
    StatusA: str
    StatusB: str
    StatusC: str
    NUM: Optional[int]
    Extra: Optional[str]
    Stoken: Optional[str]


class CookiesCache(SQLModel, table=True):
    UID: Optional[str] = Field(default='100000000', primary_key=True)
    MYSID: Optional[str]
    Cookies: str


class Config(SQLModel, table=True):
    Name: str = Field(default='Config', primary_key=True)
    Status: Optional[str]
    GroupList: Optional[str]
    Extra: Optional[str]


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


threading.Thread(target=lambda: asyncio.run(create_all()), daemon=True).start()
