import asyncio
from aanvraagapp.database import async_session_maker
from aanvraagapp import models
from aanvraagapp.parsing.listing import parse_listing, chunk_webpage
from aanvraagapp.config import settings
from aanvraagapp.controllers.client import parse_website_background_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


async def test_parse_listing(session: AsyncSession):
    result = await session.execute(
        select(models.Listing)
        .where(models.Listing.website == "https://www.rvo.nl/subsidies-financiering/eurostars")
        .options(selectinload(models.Listing.provider))
    )
    listing = result.scalar_one_or_none()
    assert listing is not None, "Dummy listing for eurostars does not exist"
    
    result = await parse_listing(listing, session)


async def test_chunk(session: AsyncSession):
    result = await session.execute(
        select(models.Webpage)
        .where(models.Webpage.url == "https://www.rvo.nl/subsidies-financiering/eurostars")
    )
    webpage = result.scalar_one_or_none()
    assert webpage is not None, "Dummy webpage for eurostars does not exist"

    result = await chunk_webpage(webpage, session)


async def test_parse_client(session: AsyncSession):
    result = await session.execute(
        select(models.Client)
        .where(models.Client.name == "Spheer.ai")
    )
    client = result.scalar_one_or_none()
    assert client is not None, "Dummy client for Spheer.ai does not exist"

    await parse_website_background_task(client.id, client.website)