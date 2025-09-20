import asyncio
from aanvraagapp import models
from .utils import (
    create_db_and_tables,
    create_dummy_clients,
    create_dummy_providers,
    create_dummy_users,
)
from aanvraagapp.database import async_session_maker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from aanvraagapp.parsing.parsing import (
    parse_webpage_from_client,
    parse_webpage_from_listing,
    parse_field_data_from_client,
    parse_field_data_from_listing,
    chunk_webpage,
)
from aanvraagapp.provider_workflows import run_rvo_workflow
from sqlalchemy import func


async def init_db_with_gemini():
    """Initialize db with dummy data AND Gemini usage."""
    await create_db_and_tables()
    async with async_session_maker() as session:
        rvo, snn = await create_dummy_providers(session)
        spheer, cursoram = await create_dummy_clients(session)
        john, jane, bob = await create_dummy_users(session)
    
    await run_rvo_workflow(limit_to_ten=True)

    # Get 10 random listings
    async with async_session_maker() as session: 
        result = await session.execute(
            select(models.Listing)
        )
        random_listings = result.scalars().all()

    # random_listings = random_listings[:1]
    
    # Create async tasks for parse_webpage_from_listing
    async def process_listing_webpage(listing):
        async with async_session_maker() as task_session:
            await parse_webpage_from_listing(listing, task_session)
            await task_session.commit()
    
    webpage_tasks = [process_listing_webpage(listing) for listing in random_listings]
    await asyncio.gather(*webpage_tasks)
    
    # Create async tasks for parse_field_data_from_listing  
    async def process_listing_field_data(listing):
        async with async_session_maker() as task_session:
            # Need to get the listing with its websites loaded
            result = await task_session.execute(
                select(models.Listing)
                .where(models.Listing.id == listing.id)
                .options(selectinload(models.Listing.websites))
                .options(selectinload(models.Listing.target_audience_labels))
            )
            listing_with_websites = result.scalar_one()
            
            updated_listing = await parse_field_data_from_listing(listing_with_websites, task_session)
            task_session.add(updated_listing)
            await task_session.commit()
    
    field_data_tasks = [process_listing_field_data(listing) for listing in random_listings]
    await asyncio.gather(*field_data_tasks)
    
    # Query all clients and create async tasks for parse_webpage_from_client
    async with async_session_maker() as session: 
        result = await session.execute(select(models.Client))
        all_clients = result.scalars().all()
    
    async def process_client_webpage(client):
        async with async_session_maker() as task_session:
            await parse_webpage_from_client(client, task_session)
            await task_session.commit()
    
    client_webpage_tasks = [process_client_webpage(client) for client in all_clients]
    await asyncio.gather(*client_webpage_tasks)
    
    # Create async tasks for parse_field_data_from_client
    async def process_client_field_data(client):
        async with async_session_maker() as task_session:
            # Need to get the client with its websites loaded
            result = await task_session.execute(
                select(models.Client)
                .where(models.Client.id == client.id)
                .options(selectinload(models.Client.websites))
            )
            client_with_websites = result.scalar_one()
            
            updated_client = await parse_field_data_from_client(client_with_websites, task_session)
            task_session.add(updated_client)
            await task_session.commit()
    
    client_field_data_tasks = [process_client_field_data(client) for client in all_clients]
    await asyncio.gather(*client_field_data_tasks)
    
    # Query all webpages and apply chunk_webpage
    async with async_session_maker() as session: 
        result = await session.execute(select(models.Webpage))
        all_webpages = result.scalars().all()
    
    async def process_webpage_chunks(webpage):
        async with async_session_maker() as task_session:
            # Need to merge the webpage into the new session
            task_session.add(webpage)
            await chunk_webpage(webpage, task_session)
            await task_session.commit()
    
    chunk_tasks = [process_webpage_chunks(webpage) for webpage in all_webpages]
    await asyncio.gather(*chunk_tasks)
