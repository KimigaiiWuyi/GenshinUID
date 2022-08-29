import asyncio
import threading

from sqlalchemy import Column, String, Integer

from .db_config import Base, engine


class PushData(Base):
    __tablename__ = 'PushData'
    __table_args__ = {'extend_existing': True}

    UID = Column(Integer, primary_key=True)
    CoinPush = Column(String, nullable=True)
    CoinValue = Column(Integer, nullable=True)
    CoinIsPush = Column(String, nullable=True)
    ResinPush = Column(String, nullable=True)
    ResinValue = Column(Integer, nullable=True)
    ResinIsPush = Column(String, nullable=True)
    GoPush = Column(String, nullable=True)
    GoValue = Column(Integer, nullable=True)
    GoIsPush = Column(String, nullable=True)
    TransformPush = Column(String, nullable=True)
    TransformValue = Column(Integer, nullable=True)
    TransformIsPush = Column(String, nullable=True)


class UidData(Base):
    __tablename__ = 'UIDDATA'
    __table_args__ = {'extend_existing': True}

    USERID = Column(Integer, primary_key=True)
    UID = Column(String, nullable=True)
    MYSID = Column(String, nullable=True)


class NewCookiesTable(Base):
    __tablename__ = 'NewCookiesTable'
    __table_args__ = {'extend_existing': True}

    UID = Column(Integer, primary_key=True)
    Cookies = Column(String, nullable=False)
    QID = Column(Integer, nullable=False)
    StatusA = Column(String, nullable=False)
    StatusB = Column(String, nullable=False)
    StatusC = Column(String, nullable=False)
    NUM = Column(Integer, nullable=True)
    Extra = Column(String, nullable=True)
    Stoken = Column(String, nullable=True)


class CookiesCache(Base):
    __tablename__ = 'CookiesCache'
    __table_args__ = {'extend_existing': True}

    UID = Column(String, primary_key=True, nullable=True)
    MYSID = Column(String, nullable=True)
    Cookies = Column(String, nullable=False)


class Config(Base):
    __tablename__ = 'Config'
    __table_args__ = {'extend_existing': True}

    Name = Column(String, primary_key=True)
    Status = Column(String, nullable=True)
    GroupList = Column(String, nullable=True)
    Extra = Column(String, nullable=True)


async def create_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


threading.Thread(target=lambda: asyncio.run(create_all()), daemon=True).start()
