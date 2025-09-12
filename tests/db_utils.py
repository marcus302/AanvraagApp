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


async def create_dummy_clients(session):
    # Create dummy client data
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
    print("Dummy clients created successfully!")

    return dummy_clients


async def create_dummy_listing(session, rvo: models.Provider):
    listing = models.Listing(
        provider_id = rvo.id,
        website = "https://www.rvo.nl/subsidies-financiering/eurostars",
    )

    session.add(listing)

    await session.commit()
    print("Dummy listing added successfully!")

    return listing


async def create_dummy_webpage(session, listing: models.Listing):
    """Create a dummy webpage using test data content - for testing only"""
    # Read the content from test data files
    html_content = open("tests/data/html_content.txt", "r", encoding="utf-8").read()
    cleaned_content = open("tests/data/cleaned_html.txt", "r", encoding="utf-8").read()
    markdown_content = open("tests/data/converted_to_markdown.txt", "r", encoding="utf-8").read()
    
    webpage = models.Webpage(
        owner_type=models.WebpageOwnerType.LISTING,
        owner_id=listing.id,
        url="https://www.rvo.nl/subsidies-financiering/eurostars",
        original_content=html_content,
        filtered_content=cleaned_content,
        markdown_content=markdown_content,
    )

    session.add(webpage)

    await session.commit()
    print("Dummy webpage added successfully!")

    return webpage


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
