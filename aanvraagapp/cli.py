import asyncio
import click
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from aanvraagapp.database import async_session_maker
from aanvraagapp.models import Listing, Client, Chunk, Webpage, ChunkOwnerType, WebpageOwnerType
from aanvraagapp.parsing.ai import create_ai_client


@click.group()
def cli():
    """AanvraagApp CLI for similarity search."""
    pass


@cli.command('search-listing')
@click.argument('listing_url', required=True)
@click.argument('query', required=True)
@click.option('--limit', default=10, help='Number of results to return (default: 10)')
def search_listing(listing_url: str, query: str, limit: int):
    """Search for similar chunks using a query string, filtered by listing URL.
    
    Takes a query string, converts it to an embedding, and finds similar chunks
    from webpages associated with the specified listing URL.
    """
    asyncio.run(_search_listing_async(listing_url, query, limit))


async def _search_listing_async(listing_url: str, query: str, limit: int):
    """Async implementation of search_listing."""
    async with async_session_maker() as session:
        # Create embedding for the query
        click.echo(f"🔍 Creating embedding for query: '{query}'")
        ai_client = create_ai_client("ollama")  # Use ollama by default like in existing patterns
        query_embedding = await ai_client.embed_query(query)
        
        # Perform similarity search with single query filtered by listing
        await _perform_listing_similarity_search(session, listing_url, query_embedding, limit)


@cli.command('search-client')
@click.argument('client_name', required=True)
@click.argument('query', required=True)
@click.option('--limit', default=10, help='Number of results to return (default: 10)')
def search_client(client_name: str, query: str, limit: int):
    """Search for similar chunks using a query string, filtered by client name.
    
    Takes a query string, converts it to an embedding, and finds similar chunks
    from webpages associated with the specified client name.
    """
    asyncio.run(_search_client_async(client_name, query, limit))


async def _search_client_async(client_name: str, query: str, limit: int):
    """Async implementation of search_client."""
    async with async_session_maker() as session:
        # Create embedding for the query
        click.echo(f"🔍 Creating embedding for query: '{query}'")
        ai_client = create_ai_client("ollama")  # Use ollama by default like in existing patterns
        query_embedding = await ai_client.embed_query(query)
        
        # Perform similarity search with single query filtered by client
        await _perform_client_similarity_search(session, client_name, query_embedding, limit)



async def _perform_listing_similarity_search(session: AsyncSession, listing_url: str, query_embedding: np.ndarray, limit: int):
    """Perform cosine similarity search filtered by listing URL using SQLAlchemy constructs."""
    query_vector = query_embedding.tolist()
    
    # Use SQLAlchemy constructs for the similarity search
    stmt = (
        select(
            Chunk.content,
            Webpage.url,
            (-Chunk.emb.cosine_distance(query_vector) + 1).label('cosine_similarity')
        )
        .select_from(Chunk)
        .join(Webpage, (Chunk.owner_id == Webpage.id) & (Chunk.owner_type == ChunkOwnerType.WEBPAGE))
        .join(Listing, (Webpage.owner_id == Listing.id) & (Webpage.owner_type == WebpageOwnerType.LISTING))
        .where(Listing.website == listing_url)
        .order_by(Chunk.emb.cosine_distance(query_vector).asc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    similar_chunks = result.fetchall()
    
    if not similar_chunks:
        click.echo(f"❌ No chunks found for listing: {listing_url}")
        return
    
    click.echo(f"🎯 Top {len(similar_chunks)} most similar chunks for listing '{listing_url}':")
    _display_results(similar_chunks)


async def _perform_client_similarity_search(session: AsyncSession, client_name: str, query_embedding: np.ndarray, limit: int):
    """Perform cosine similarity search filtered by client name using SQLAlchemy constructs."""
    query_vector = query_embedding.tolist()
    
    # Use SQLAlchemy constructs for the similarity search
    stmt = (
        select(
            Chunk.content,
            Webpage.url,
            (-Chunk.emb.cosine_distance(query_vector) + 1).label('cosine_similarity')
        )
        .select_from(Chunk)
        .join(Webpage, (Chunk.owner_id == Webpage.id) & (Chunk.owner_type == ChunkOwnerType.WEBPAGE))
        .join(Client, (Webpage.owner_id == Client.id) & (Webpage.owner_type == WebpageOwnerType.CLIENT))
        .where(Client.name == client_name)
        .order_by(Chunk.emb.cosine_distance(query_vector).asc())
        .limit(limit)
    )
    
    result = await session.execute(stmt)
    similar_chunks = result.fetchall()
    
    if not similar_chunks:
        click.echo(f"❌ No chunks found for client: {client_name}")
        return
    
    click.echo(f"🎯 Top {len(similar_chunks)} most similar chunks for client '{client_name}':")
    _display_results(similar_chunks)


def _display_results(similar_chunks):
    """Display the similarity search results in a formatted way."""
    click.echo("=" * 80)
    
    for i, (content, url, similarity) in enumerate(similar_chunks, 1):
        click.echo(f"\n{i}. Similarity: {similarity:.4f}")
        click.echo(f"   URL: {url}")
        click.echo(f"   Content: {content}")
        if i < len(similar_chunks):
            click.echo("-" * 40)


def main():
    """Main CLI entry point."""
    cli()


if __name__ == '__main__':
    main() 