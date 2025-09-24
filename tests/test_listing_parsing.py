import asyncio
from aanvraagapp.database import async_session_maker
from aanvraagapp import models
from aanvraagapp.parsing.parsing import parse_webpage_from_listing, parse_field_data_from_listing, chunk_webpage, parse_webpage_from_client
from aanvraagapp.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from unittest.mock import AsyncMock
from contextlib import asynccontextmanager


async def test_parse_webpage_from_listing(basic_session: AsyncSession):
    result = await basic_session.execute(
        select(models.Listing)
        .where(models.Listing.website == "https://www.rvo.nl/subsidies-financiering/eurostars")
        .options(selectinload(models.Listing.provider))
    )
    listing = result.scalar_one_or_none()
    assert listing is not None, "Dummy listing for eurostars does not exist"
    
    result = await parse_webpage_from_listing(listing, basic_session)
    await basic_session.commit()


async def test_parse_field_data_from_listing(basic_session: AsyncSession):
    result = await basic_session.execute(
        select(models.Listing)
        .where(models.Listing.website == "https://www.rvo.nl/subsidies-financiering/eurostars")
        .options(selectinload(models.Listing.provider), selectinload(models.Listing.websites), selectinload(models.Listing.target_audience_labels))
    )
    listing = result.scalar_one_or_none()
    assert listing is not None, "Dummy listing for eurostars does not exist"
    
    result = await parse_field_data_from_listing(listing, basic_session)
    await basic_session.commit()


async def test_chunk(basic_session: AsyncSession):
    result = await basic_session.execute(
        select(models.Webpage)
        .where(models.Webpage.url == "https://www.rvo.nl/subsidies-financiering/eurostars")
    )
    webpage = result.scalar_one_or_none()
    assert webpage is not None, "Dummy webpage for eurostars does not exist"

    result = await chunk_webpage(webpage, basic_session)
    await basic_session.commit()


async def test_parse_client(basic_session: AsyncSession, monkeypatch):
    result = await basic_session.execute(
        select(models.Client)
        .where(models.Client.name == "Spheer.ai")
    )
    client = result.scalar_one_or_none()
    assert client is not None, "Dummy client for Spheer.ai does not exist"

    await parse_webpage_from_client(client, basic_session)
    await basic_session.commit()
