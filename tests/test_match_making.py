from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from aanvraagapp import models
from aanvraagapp.parsing.parsing import search_suitable_listings
from aanvraagapp.types import FinancialInstrument


async def test_search_suitable_listings(parsed_chunks_session: AsyncSession):
    # Fetch the Spheer.ai client with its websites
    result = await parsed_chunks_session.execute(
        select(models.Client)
        .where(models.Client.name == "Spheer.ai")
        .options(selectinload(models.Client.websites))
    )
    client = result.scalar_one_or_none()
    assert client is not None, "Spheer.ai client not found in test data"
    assert len(client.websites) > 0, "Spheer.ai client should have parsed websites"
    
    match_results = await search_suitable_listings(
        client=client,
        session=parsed_chunks_session,
        is_open=True,
        financial_instruments=[FinancialInstrument.SUBSIDY]
    )