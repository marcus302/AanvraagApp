from aanvraagapp import models
from sqlalchemy.ext.asyncio import create_async_engine
from aanvraagapp.config import settings
from aanvraagapp.dependencies.auth import password_helper


async def create_dummy_users(session):
    dummy_users = [
        models.User(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            hashed_password=password_helper.hash("password"),
        ),
        models.User(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            hashed_password=password_helper.hash("password"),
        ),
        models.User(
            first_name="Bob",
            last_name="Johnson",
            email="bob.johnson@example.com",
            hashed_password=password_helper.hash("password"),
        ),
    ]

    for user in dummy_users:
        session.add(user)

    await session.commit()

    return dummy_users


async def create_dummy_providers(session):
    dummy_providers = [
        models.Provider(
            name="RVO",
            website="https://rvo.nl",
        ),
        models.Provider(
            name="SNN",
            website="https://snn.nl",
        ),
    ]

    for provider in dummy_providers:
        session.add(provider)

    await session.commit()

    return dummy_providers


async def create_dummy_clients(session):
    dummy_clients = [
        models.Client(
            name="Spheer.ai",
            website="https://spheer.ai",
        ),
        models.Client(
            name="CursorAM",
            website="https://cursoram.com",
        ),
    ]

    for client in dummy_clients:
        session.add(client)

    await session.commit()

    return dummy_clients


async def delete_tables():
    engine = create_async_engine(settings.database.database_uri)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()


async def create_db_and_tables():
    engine = create_async_engine(settings.database.database_uri)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await engine.dispose()


async def cleanup_db():
    await delete_tables()
