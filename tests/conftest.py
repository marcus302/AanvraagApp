import pytest
import asyncio
from aanvraagapp import models
from aanvraagapp.config import settings
from aanvraagapp.database import async_session_maker, async_engine
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, AsyncTransaction
from typing import AsyncGenerator
from tests.db_utils import create_dummy_providers, create_dummy_users, create_dummy_listing


# Required per https://anyio.readthedocs.io/en/stable/testing.html#using-async-fixtures-with-higher-scopes
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def connection(request, anyio_backend) -> AsyncGenerator[AsyncConnection, None]:
    async with async_engine.begin() as transaction:
        print("dropping - startup")
        await transaction.run_sync(models.Base.metadata.drop_all)
    
    async with async_engine.begin() as transaction:
        print("creating - startup")
        await transaction.run_sync(models.Base.metadata.create_all)

    async with async_session_maker() as session:
        print("adding basic test data set - startup")
        rvo, snn = await create_dummy_providers(session)
        john, jane, bob = await create_dummy_users(session)
        eurostars = await create_dummy_listing(session, rvo)

    async with async_engine.connect() as connection:
        yield connection

    async with async_engine.begin() as transaction:
        print("dropping - teardown")
        await transaction.run_sync(models.Base.metadata.drop_all)

    await async_engine.dispose()


@pytest.fixture(scope="function")
async def transaction(
    connection: AsyncConnection,
) -> AsyncGenerator[AsyncTransaction, None]:
    async with connection.begin() as transaction:
        yield transaction


@pytest.fixture(scope="function")
async def session(
    connection: AsyncConnection, transaction: AsyncTransaction
) -> AsyncGenerator[AsyncSession, None]:
    async_session = AsyncSession(
        bind=connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )

    yield async_session

    await transaction.rollback()