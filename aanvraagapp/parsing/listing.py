import httpx
import logging
import os
from trafilatura import extract
from aanvraagapp import models
from aanvraagapp.database import async_session_maker
from .utils import chunk_text, generate_embedding

logger = logging.getLogger(__name__)

async def parse_listing(listing: models.Listing, session):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(listing.website)
            response.raise_for_status()
            html_content = response.text
            logger.info(f"Successfully fetched html content for {listing.website}")
        
        if not html_content.strip():
            logger.warning(f"No HTML content found in response from {listing.website}")
            return None
        
        logger.info(f"Successfully parsed HTML from {listing.website}")
        
        cleaned_html = extract(html_content, include_links=True, output_format="markdown")
    except httpx.RequestError as e:
        logger.error(f"Listing API request failed : {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return None
        
    if cleaned_html is None:
        logger.warning(f"Trafilatura failed to parse anything at all from {listing.website}")
        return None

    if not cleaned_html.strip():
        logger.warning(f"No meaningful content found after cleaning HTML from {listing.website}")
        return None
    
    logger.info(f"Successfully cleaned HTML from {listing.website}")
    
    listing_document = models.ListingDocument(
        doc_type=models.DocumentType.WEBPAGE,
        uri=listing.website,
    )
    session.add(listing_document)
    await listing.awaitable_attrs.listing_documents
    listing.listing_documents.append(listing_document)
    await session.flush()  # Make the id on listing_document available
    
    chunks = chunk_text(cleaned_html, chunk_size=1024, overlap=128)
    logger.info(f"Created {len(chunks)} chunks from cleaned HTML")
    
    for i, chunk_content in enumerate(chunks):
        embedding = await generate_embedding(chunk_content)
        chunk = models.ListingDocumentChunk(
            document_id=listing_document.id,
            content=chunk_content,
            emb=embedding
        )
        session.add(chunk)
        
        logger.info(f"Processed chunk {i+1}/{len(chunks)}")
    
    await session.commit()
    logger.info(f"Successfully saved {len(chunks)} chunks to database")            
    return listing_document
