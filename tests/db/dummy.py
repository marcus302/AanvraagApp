from aanvraagapp import models
from .utils import (
    create_views_and_tables,
    create_dummy_clients,
    create_dummy_providers,
    create_dummy_users,
)
from aanvraagapp.database import async_session_maker


async def create_dummy_listing(session, rvo: models.Provider):
    listing = models.Listing(
        provider_id=rvo.id,
        website="https://www.rvo.nl/subsidies-financiering/eurostars",
    )

    session.add(listing)

    await session.commit()

    return listing


async def create_dummy_webpage(session, listing: models.Listing):
    html_content = open("tests/data/html_content.txt", "r", encoding="utf-8").read()
    cleaned_content = open("tests/data/cleaned_html.txt", "r", encoding="utf-8").read()
    markdown_content = open(
        "tests/data/converted_to_markdown.txt", "r", encoding="utf-8"
    ).read()

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
    await create_views_and_tables()
    async with async_session_maker() as session:
        rvo, snn = await create_dummy_providers(session)
        spheer, cursoram = await create_dummy_clients(session)
        john, jane, bob = await create_dummy_users(session)
        eurostars = await create_dummy_listing(session, rvo)
        await create_dummy_webpage(session, eurostars)
