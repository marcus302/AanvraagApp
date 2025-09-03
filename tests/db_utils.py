import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from aanvraagapp import models
from aanvraagapp.dependencies.auth import password_helper
from aanvraagapp.config import settings

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


async def create_dummy_users():
    """Create dummy users with properly hashed passwords using plain SQL - for testing only"""
    engine = create_async_engine(settings.database.database_uri)

    # Create dummy user data with hashed passwords
    dummy_users = [
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "hashed_password": password_helper.hash("password"),
        },
        {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com",
            "hashed_password": password_helper.hash("password"),
        },
        {
            "first_name": "Bob",
            "last_name": "Johnson",
            "email": "bob.johnson@example.com",
            "hashed_password": password_helper.hash("password"),
        },
    ]

    async with engine.begin() as conn:
        for user_data in dummy_users:
            await conn.execute(
                text(
                    'INSERT INTO "user" (first_name, last_name, email, hashed_password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :hashed_password, NOW(), NOW())'
                ),
                user_data,
            )

    await engine.dispose()
    print("Dummy users created successfully!")


async def create_dummy_providers():
    """Create dummy providers - for testing only"""
    engine = create_async_engine("postgresql+asyncpg://mark:mark@db:5432/mark")

    # Create dummy provider data
    dummy_providers = [
        {
            "name": "RVO",
            "website": "https://rvo.nl",
        },
        {
            "name": "SNN",
            "website": "https://snn.nl",
        },
    ]

    async with engine.begin() as conn:
        for provider_data in dummy_providers:
            await conn.execute(
                text(
                    'INSERT INTO "provider" (name, website, created_at, updated_at) VALUES (:name, :website, NOW(), NOW())'
                ),
                provider_data,
            )

    await engine.dispose()
    print("Dummy providers created successfully!")


async def init_db():
    """Initialize the database by creating all tables and dummy users - for testing only"""
    print("Creating database tables...")
    await create_db_and_tables()
    print("Database tables created successfully!")

    print("Creating dummy users...")
    await create_dummy_users()

    print("Creating dummy providers...")
    await create_dummy_providers()


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
