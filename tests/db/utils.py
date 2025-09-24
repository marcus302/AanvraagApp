from aanvraagapp import models
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from aanvraagapp.config import settings
from aanvraagapp.dependencies.auth import password_helper


# Database view management
LISTINGS_WITH_AUDIENCES_VIEW_SQL = """
CREATE OR REPLACE VIEW listings_with_target_audiences AS
SELECT 
    l.id,
    l.provider_id,
    l.website,
    l.is_open,
    l.opens_at,
    l.closes_at,
    l.last_checked,
    l.name,
    l.financial_instrument,
    l.target_audience_desc,
    l.created_at,
    l.updated_at,
    COALESCE(
        STRING_AGG(tal.name, ', ' ORDER BY tal.name), 
        ''
    ) AS target_audiences_concatenated
FROM 
    listing l
LEFT JOIN 
    listing_target_audience_label_association ltala ON l.id = ltala.listing_id
LEFT JOIN 
    target_audience_label tal ON ltala.target_audience_label_id = tal.id
GROUP BY 
    l.id, l.provider_id, l.website, l.is_open, l.opens_at, l.closes_at, 
    l.last_checked, l.name, l.financial_instrument, l.target_audience_desc, 
    l.created_at, l.updated_at;
"""

DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL = """
DROP VIEW IF EXISTS listings_with_target_audiences;
"""


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


async def drop_views_and_tables():
    engine = create_async_engine(settings.database.database_uri)

    async with engine.begin() as conn:
        await conn.execute(text(DROP_LISTINGS_WITH_AUDIENCES_VIEW_SQL))
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()


async def create_views_and_tables():
    engine = create_async_engine(settings.database.database_uri)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
        await conn.execute(text(LISTINGS_WITH_AUDIENCES_VIEW_SQL))

    await engine.dispose()
