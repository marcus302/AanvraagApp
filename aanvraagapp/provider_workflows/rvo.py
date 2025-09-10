import logging
import httpx
import asyncio
from enum import Enum
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aanvraagapp.models import Provider, Listing
from aanvraagapp.database import async_session_maker

logger = logging.getLogger(__name__)

BASE_URL = "https://www.rvo.nl"
API_URL = f"{BASE_URL}/api/v1/opendata/subsidies"
MAX_RETRIES = 3
WAIT_AFTER_FAILED_REQUEST = 10
WAIT_BETWEEN_REQUESTS = 2


class ListingCreationResult(Enum):
    """Enum for the different outcomes when attempting to create a listing"""
    SUCCESS = "success"  # New listing was successfully created
    ALREADY_EXISTS = "already_exists"  # Listing already exists in database
    SKIPPED_INVALID_URL = "skipped_invalid_url"  # URL pattern is invalid, listing skipped
    FAILED = "failed"  # Error occurred during creation (missing URL)


def _is_valid_subsidy_url(url: str) -> bool:
    """
    Valid URLs should have the pattern: /subsidies-financiering/subsidy-name
    Invalid URLs have more than 2 slashes (e.g., /subsidies-financiering/subsidy-name/sub-page)
    """
    if not url:
        return False
    
    # Count forward slashes - should be exactly 2 for valid URLs
    slash_count = url.count('/')
    return slash_count == 2


async def _create_listing_from_subsidy(
    session: AsyncSession, 
    provider: Provider, 
    subsidy: dict
) -> ListingCreationResult:
    # Construct the full URL
    subsidy_url = subsidy.get("url")
    if not subsidy_url:
        logger.error(f"Subsidy missing URL field: {subsidy}")
        return ListingCreationResult.FAILED
    
    # Validate the URL pattern before proceeding
    if not _is_valid_subsidy_url(subsidy_url):
        logger.info(f"Skipping subsidy with invalid URL pattern: {subsidy_url}")
        return ListingCreationResult.SKIPPED_INVALID_URL
    
    subsidy_url = BASE_URL + subsidy_url
    
    # Check if listing already exists. # TODO: Performance?
    existing_listing = await session.execute(
        select(Listing).where(
            Listing.provider_id == provider.id,
            Listing.website == subsidy_url
        )
    )
    if existing_listing.scalar_one_or_none():
        logger.info(f"Listing already exists for {subsidy_url}")
        return ListingCreationResult.ALREADY_EXISTS
    
    # Create new listing
    listing = Listing(
        provider_id=provider.id,
        website=subsidy_url,
        original_content=None,
        cleaned_content=None,
        markdown_content=None,
    )
    
    session.add(listing)
    await session.commit()
    logger.info(f"Created new listing for {subsidy.get('title', 'Unknown')} at {subsidy_url}")
    return ListingCreationResult.SUCCESS


async def run_rvo_workflow():
    logger.info("Starting RVO workflow")
    async with async_session_maker() as session:
        # Get the RVO provider
        result = await session.execute(
            select(Provider).where(Provider.name == "RVO")
        )
        provider = result.scalar_one_or_none()
        if not provider:
            logger.error("RVO provider not found in database")
            return
        
        # Fetch subsidies from API with pagination
        page = 0
        total_successful_listings = 0
        total_failed_listings = 0
        total_skipped_listings = 0
        total_already_existing_listings = 0
        retry_count = 0
        
        try:
            async with httpx.AsyncClient() as client:
                while True:
                    # Fetch current page
                    page_url = f"{API_URL}?page={page}"
                    logger.info(f"Fetching page {page} from RVO API")
                    
                    try:
                        response = await client.get(page_url)
                        if response.status_code != 200:
                            logger.error(f"RVO API request failed for page {page} with status {response.status_code}")
                            logger.error(f"Response headers: {dict(response.headers)}")
                            try:
                                response_text = response.text
                                logger.error(f"Response body: {response_text[:500]}...")  # Limit to first 500 chars
                            except Exception:
                                logger.error("Could not read response body")
                            break
                        
                        # Reset retry count on successful request
                        retry_count = 0
                        
                        subsidies = response.json()
                        
                        # If no subsidies returned, we've reached the end
                        if not subsidies:
                            logger.info(f"Page {page} returned no subsidies, reached end of pagination")
                            break
                        
                        logger.info(f"Successfully fetched {len(subsidies)} subsidies from page {page}")
                        
                        # Create listings for each subsidy on this page
                        page_successful_listings = 0
                        page_failed_listings = 0
                        page_skipped_listings = 0
                        page_already_existing_listings = 0
                        for subsidy in subsidies:
                            result = await _create_listing_from_subsidy(session, provider, subsidy)
                            if result == ListingCreationResult.SUCCESS:
                                page_successful_listings += 1
                            elif result == ListingCreationResult.ALREADY_EXISTS:
                                page_already_existing_listings += 1
                            elif result == ListingCreationResult.FAILED:
                                page_failed_listings += 1
                            elif result == ListingCreationResult.SKIPPED_INVALID_URL:
                                page_skipped_listings += 1
                        
                        total_successful_listings += page_successful_listings
                        total_failed_listings += page_failed_listings
                        total_skipped_listings += page_skipped_listings
                        total_already_existing_listings += page_already_existing_listings
                        
                        logger.info(f"Page {page} completed: {page_successful_listings} new listings created, {page_already_existing_listings} already existed, {page_failed_listings} failed, {page_skipped_listings} skipped.")
                        
                        # Move to next page
                        page += 1
                        
                        # Add polite delay between requests to avoid overwhelming the API
                        await asyncio.sleep(WAIT_BETWEEN_REQUESTS)
                        
                    except httpx.RequestError as e:
                        retry_count += 1
                        logger.error(f"RVO API request failed (attempt {retry_count}/{MAX_RETRIES}): {str(e)}")
                        logger.error(f"Error type: {type(e).__name__}")
                        
                        if retry_count >= MAX_RETRIES:
                            logger.error(f"Maximum retries ({MAX_RETRIES}) exceeded. Aborting RVO workflow.")
                            return
                        
                        logger.info(f"Waiting 10 seconds before retrying page {page}...")
                        await asyncio.sleep(WAIT_AFTER_FAILED_REQUEST)
                        # Don't increment page, retry the same page
                        continue
                    
        except Exception as e:
            logger.error(f"Unexpected error in RVO workflow: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return
        
        logger.info(f"RVO workflow completed: {total_successful_listings} new listings created, {total_already_existing_listings} already existed, {total_failed_listings} failed, {total_skipped_listings} skipped across {page} pages")