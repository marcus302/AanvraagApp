from typing import AsyncGenerator

import redis.asyncio as redis
from fastapi import Depends
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


DATABASE_URI = "sqlite+aiosqlite:///./aanvraagapp.db"
REDIS_URI = "redis://redis:6379/0"

# Create async engine and session maker
async_engine = create_async_engine(
    DATABASE_URI,
    echo=True,  # Set to False in production
    future=True,
)

async_session_maker = async_sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency that provides a database session"""
    async with async_session_maker() as session:
        yield session


DBSession: AsyncSession = Depends(get_async_session)


async def get_redis_client():
    client = redis.Redis.from_pool(
        redis.ConnectionPool.from_url(REDIS_URI, decode_responses=True)
    )
    yield client
    await client.aclose()


RedisSession: Redis = Depends(get_redis_client)
