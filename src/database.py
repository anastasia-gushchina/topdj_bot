import logging
from urllib.parse import urlparse, urlunparse
from sqlalchemy import NullPool, AsyncAdaptedQueuePool, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from src.settings import settings

logger = logging.getLogger(__name__)


class Database:
    engine: AsyncEngine

    def __init__(self):
        db_connect_url: str = settings.db_url
        if settings.environment == "test":
            self.engine = create_async_engine(db_connect_url, poolclass=NullPool, echo=False)
        else:
            self.engine = create_async_engine(
                db_connect_url,
                pool_size=5,
                max_overflow=5,
                poolclass=AsyncAdaptedQueuePool,
                echo=settings.echo_sql,
                echo_pool=False,
            )

    def get_session_maker(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(self.engine, expire_on_commit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


database = Database()
session_maker = database.get_session_maker()
