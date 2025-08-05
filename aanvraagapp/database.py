from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from . import models

DATABASE_URI = "sqlite+aiosqlite:///./aanvraagapp.db"

# Create async engine and session maker
async_engine = create_async_engine(
    DATABASE_URI,
    echo=True,  # Set to False in production
    future=True
)

async_session_maker = async_sessionmaker(
    async_engine, 
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Async dependency that provides a database session"""
    async with async_session_maker() as session:
        yield session
