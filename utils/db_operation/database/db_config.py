from pathlib import Path

from sqlalchemy import event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

DATABASE_URL = "sqlite+aiosqlite:///{}".format('ID_DATA.db')

engine = create_async_engine(DATABASE_URL, future=True)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
Base = declarative_base()


@event.listens_for(engine.sync_engine, 'connect')
def engine_connect(conn, branch):
    cursor = conn.cursor()
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.close()
