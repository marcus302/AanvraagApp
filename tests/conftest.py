import pytest
import asyncio
from aanvraagapp import models
from aanvraagapp.config import LocalDatabaseSettings
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    AsyncTransaction,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import text
from typing import AsyncGenerator
from tests.db import utils as db_utils
from tests.db import dummy as db_dummy


basic_testsuite_db_config = LocalDatabaseSettings(
    provider="local",
    host="127.0.0.1",
    port="5432",
    db="basic_testsuite",
    user="mark",
    password="mark",
)


parsed_chunks_testsuite_db_config = LocalDatabaseSettings(
    provider="local",
    host="127.0.0.1",
    port="5432",
    db="parsed_chunks_testsuite",
    user="mark",
    password="mark",
)


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
async def basic_testsuite(
    request, anyio_backend
) -> AsyncGenerator[AsyncConnection, None]:
    engine = create_async_engine(basic_testsuite_db_config.database_uri)
    async_session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Setup - drop everything first
    async with engine.begin() as transaction:
        print("dropping - startup")
        await transaction.execute(text(db_utils.DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL))
        await transaction.run_sync(models.Base.metadata.drop_all)

    # Create tables and views
    async with engine.begin() as transaction:
        print("creating - startup")
        await transaction.run_sync(models.Base.metadata.create_all)
        await transaction.execute(text(db_utils.LISTINGS_WITH_AUDIENCES_VIEW_SQL))

    async with async_session_maker() as session:
        print("adding basic test data set - startup")
        rvo, snn = await db_utils.create_dummy_providers(session)
        spheer, cursoram = await db_utils.create_dummy_clients(session)
        john, jane, bob = await db_utils.create_dummy_users(session)
        eurostars = await db_dummy.create_dummy_listing(session, rvo)
        await db_dummy.create_dummy_webpage(session, eurostars)

    async with engine.connect() as connection:
        yield connection

    # Teardown - drop views first, then tables
    async with engine.begin() as transaction:
        print("dropping - teardown")
        await transaction.execute(text(db_utils.DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL))
        await transaction.run_sync(models.Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def basic_session(
    basic_testsuite: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    async with basic_testsuite.begin() as transaction:
        async_session = AsyncSession(
            bind=basic_testsuite,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        yield async_session

        await transaction.rollback()


@pytest.fixture(scope="session")
async def parsed_chunks_testsuite(
    request, anyio_backend
) -> AsyncGenerator[AsyncConnection, None]:
    engine = create_async_engine(parsed_chunks_testsuite_db_config.database_uri)
    async_session_maker = async_sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Setup - drop everything first
    async with engine.begin() as transaction:
        print("dropping - startup")
        await transaction.execute(text(db_utils.DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL))
        await transaction.run_sync(models.Base.metadata.drop_all)

    # Create tables and views
    async with engine.begin() as transaction:
        print("creating - startup")
        await transaction.run_sync(models.Base.metadata.create_all)
        await transaction.execute(text(db_utils.LISTINGS_WITH_AUDIENCES_VIEW_SQL))

    async with async_session_maker() as session:
        print("adding basic test data set - startup")
        rvo, snn = await db_utils.create_dummy_providers(session)
        spheer, cursoram = await db_utils.create_dummy_clients(session)
        john, jane, bob = await db_utils.create_dummy_users(session)
        eurostars = await db_dummy.create_dummy_listing(session, rvo)
        await db_dummy.create_dummy_webpage(session, eurostars)

    async with engine.connect() as connection:
        yield connection

    # Teardown - drop views first, then tables
    async with engine.begin() as transaction:
        print("dropping - teardown")
        await transaction.execute(text(db_utils.DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL))
        await transaction.run_sync(models.Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def parsed_chunks_session(
    parsed_chunks_testsuite: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    async with parsed_chunks_testsuite.begin() as transaction:
        async_session = AsyncSession(
            bind=parsed_chunks_testsuite,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )

        yield async_session

        await transaction.rollback()
