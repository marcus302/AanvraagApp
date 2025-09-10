import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from aanvraagapp import models
from aanvraagapp.dependencies.auth import password_helper
from aanvraagapp.config import settings
from aanvraagapp.database import async_session_maker

async def delete_tables():
    """Delete all tables from the database - for testing only"""
    engine = create_async_engine(settings.database.database_uri)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()


async def create_db_and_tables():
    """Create all tables in the database - for testing only"""
    engine = create_async_engine(settings.database.database_uri)
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await engine.dispose()


async def create_dummy_users(session):
    """Create dummy users with properly hashed passwords using ORM - for testing only"""
    # Create dummy user data with hashed passwords
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
    print("Dummy users created successfully!")

    return dummy_users


async def create_dummy_providers(session):
    """Create dummy providers using ORM - for testing only"""
    # Create dummy provider data
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
    print("Dummy providers created successfully!")

    return dummy_providers


async def create_dummy_listing(session, rvo: models.Provider):
    listing = models.Listing(
        provider_id = rvo.id,
        website = "https://www.rvo.nl/subsidies-financiering/eurostars",
        original_content = None,
        cleaned_content = None,
        markdown_content = None
    )

    session.add(listing)

    await session.commit()
    print("Dummy listing added successfully!")

    return listing


async def init_db():
    """Initialize the database by creating all tables and dummy users - for testing only"""
    print("Creating database tables...")
    await create_db_and_tables()
    print("Database tables created successfully!")

    async with async_session_maker() as session:
        print("Creating dummy users...")
        await create_dummy_users(session)

        print("Creating dummy providers...")
        await create_dummy_providers(session)


async def cleanup_db():
    """Clean up the database by dropping all tables - for testing only"""
    print("Dropping database tables...")
    await delete_tables()
    print("Database tables dropped successfully!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        asyncio.run(cleanup_db())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup":
        asyncio.run(init_db())
    else:
        print("Error: Please specify 'setup' or 'teardown'")
        print("Usage: python -m tests.db_utils setup|teardown")
        sys.exit(1)
