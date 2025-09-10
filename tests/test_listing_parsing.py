import asyncio
from aanvraagapp.database import async_session_maker
from aanvraagapp.models import Listing
from aanvraagapp.parsing.listing import parse_listing
from aanvraagapp.config import settings
from sqlalchemy import select

async def test_parse_listing():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Listing).where(Listing.website == "https://www.rvo.nl/subsidies-financiering/eureka")
        )
        listing = result.scalar_one_or_none()

        if listing is None:
            raise ValueError("Listing does not exist")
        
        result = await parse_listing(listing, session)
