import os
from configparser import ConfigParser
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from powonline.config import default
from powonline.pusher import PusherWrapper

SQLALCHEMY_DATABASE_URL = os.getenv("POWONLINE_DSN", "")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
async_session = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)


async def get_db():
    async with async_session() as session:
        yield session
        await session.commit()


def get_pusher(config: Annotated[ConfigParser, Depends(default)]):
    output = PusherWrapper.create(
        config,
        config.get("pusher", "app_id", fallback=""),
        config.get("pusher", "key", fallback=""),
        config.get("pusher", "secret", fallback=""),
    )
    return output
