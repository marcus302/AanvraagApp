import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import selectinload

from aanvraagapp import models
from aanvraagapp.dependencies.auth import password_helper
from aanvraagapp.config import settings
from aanvraagapp.database import async_session_maker
from aanvraagapp.provider_workflows import run_rvo_workflow
from sqlalchemy import select
from aanvraagapp.parsing.listing import parse_webpage_from_listing, chunk_webpage, parse_field_data_from_listing
from aanvraagapp.controllers.client import parse_website_background_task

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


async def create_dummy_listing(session, rvo: models.Provider):
    listing = models.Listing(
        provider_id = rvo.id,
        website = "https://www.rvo.nl/subsidies-financiering/eurostars",
    )

    session.add(listing)

    await session.commit()

    return listing


async def create_dummy_webpage(session, listing: models.Listing):
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

    return webpage


async def init_db_with_dummy():
    """Initialize db with dummy data, no Gemini usage."""
    await create_db_and_tables()
    async with async_session_maker() as session:
        rvo, snn = await create_dummy_providers(session)
        spheer, cursoram = await create_dummy_clients(session)
        john, jane, bob = await create_dummy_users(session)
        eurostars = await create_dummy_listing(session, rvo)
        await create_dummy_webpage(session, eurostars)


async def init_db_with_gemini():
    """Initialize db with dummy data AND Gemini usage."""
    await create_db_and_tables()
    async with async_session_maker() as session:
        rvo, snn = await create_dummy_providers(session)
        spheer, cursoram = await create_dummy_clients(session)
        john, jane, bob = await create_dummy_users(session)
        
        # Temporary to speed up this setup. See TODO below.
        listing = models.Listing(
            provider_id=rvo.id,
            website="https://www.rvo.nl/subsidies-financiering/eurostars",
        )
        session.add(listing)
        await session.commit()
        # TODO: Use entire workflow
        # await run_rvo_workflow()
        
        result = await session.execute(
            select(models.Listing)
            .where(models.Listing.website == "https://www.rvo.nl/subsidies-financiering/eurostars")
            .options(selectinload(models.Listing.provider))
        )
        listing = result.scalar_one()
        await parse_webpage_from_listing(listing, session)
        result = await session.execute(
            select(models.Listing)
            .where(models.Listing.website == "https://www.rvo.nl/subsidies-financiering/eurostars")
            .options(selectinload(models.Listing.provider), selectinload(models.Listing.websites))
        )
        listing = result.scalar_one()
        await parse_field_data_from_listing(listing, session)
        result = await session.execute(
            select(models.Webpage)
            .where(models.Webpage.url == "https://www.rvo.nl/subsidies-financiering/eurostars")
        )
        webpage = result.scalar_one()
        await chunk_webpage(webpage, session)
        result = await session.execute(
            select(models.Client)
            .where(models.Client.website == "https://spheer.ai")
        )
        client = result.scalar_one()
        await parse_website_background_task(client.id, client.website, session)


async def cleanup_db():
    await delete_tables()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        asyncio.run(cleanup_db())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup-dummy":
        asyncio.run(init_db_with_dummy())
    elif len(sys.argv) > 1 and sys.argv[1] == "setup-gemini":
        asyncio.run(init_db_with_gemini())
    else:
        print("Error: Please specify 'setup-dummy', 'setup-gemini', or 'teardown'")
        print("Usage: python -m tests.db_utils setup-dummy|setup-gemini|teardown")
        sys.exit(1)
