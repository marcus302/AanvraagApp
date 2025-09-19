import httpx
import logging
from aanvraagapp import models
from .ai import create_ai_client
from aanvraagapp.config import settings
from aanvraagapp.parsing.prompts import prompts
from .clean import clean_html
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pydantic import BaseModel
from datetime import date
from typing import Literal


logger = logging.getLogger(__name__)


async def clean_and_parse_into_md(url: str, prompt_name: str):
    # Get the raw HTML data from the web page.
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            html_content = response.text
            logger.info(f"Successfully fetched html content for {url}")
        if not html_content.strip():
            logger.warning(f"No HTML content found in response from {url}")
            raise ValueError("Empty HTML")
        logger.info(f"Successfully parsed HTML from {url}")
    except httpx.RequestError as e:
        logger.error(f"Listing API request failed : {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise e
    logger.info(f"Successfully cleaned HTML from {url}")

    # Throw away as much junk as possible.
    # cleaned_html = simplify_html(html_content)
    cleaned_html = clean_html(html_content)

    # Ask AI to rewrite into Markdown
    template = prompts.get_template(prompt_name)
    prompt_content = template.render(html_content=cleaned_html)
    ai_client = create_ai_client("gemini")  # Use gemini by default
    converted_to_markdown = await ai_client.generate_content(prompt_content)

    return html_content, cleaned_html, converted_to_markdown


class ListingFieldData(BaseModel):
    is_open: bool | None
    opens_at: date | None
    closes_at: date | None
    last_checked: date | None
    name: str
    for_mkb: bool | None
    financial_instrument: Literal["subsidy", "loan", "loan_guarantee", "other"]
    sector: Literal["culture", "sustainability", "innovation", "agriculture", "other"]


async def extract_field_data(md_content: str, prompt_name: str):
    ai_client = create_ai_client("gemini")  # Use gemini by default

    template = prompts.get_template(prompt_name)
    prompt_content = template.render(md_content=md_content)
    ai_client = create_ai_client("gemini")  # Use gemini by default
    json_with_field_data = await ai_client.generate_content(prompt_content, output_schema=ListingFieldData)
    # Parse the JSON string into a ListingFieldData instance
    field_data = ListingFieldData.model_validate_json(json_with_field_data)
    return field_data


async def parse_webpage_from_listing(listing: models.Listing, session):
    html_content, cleaned_html, converted_to_markdown = await clean_and_parse_into_md(listing.website, "rewrite_subsidy_in_md.jinja")

    webpage = models.Webpage(
        owner_type=models.WebpageOwnerType.LISTING,
        owner_id=listing.id,
        url=listing.website,
        original_content=html_content,
        filtered_content=cleaned_html,
        markdown_content=converted_to_markdown,
    )
    session.add(webpage)          
    
    await session.commit()
    return webpage


async def parse_field_data_from_listing(listing: models.Listing, session):
    assert len(listing.websites) > 0, "No parsed websites yet"
    assert len(listing.websites) == 1, "Support only single website from entry url at this moment"

    webpage = listing.websites[0]

    field_data = await extract_field_data(webpage.markdown_content, "extract_field_data_from_subsidy.jinja")
    
    # Update listing with extracted field data
    listing.is_open = field_data.is_open
    listing.opens_at = field_data.opens_at
    listing.closes_at = field_data.closes_at
    listing.last_checked = field_data.last_checked
    listing.name = field_data.name
    listing.for_mkb = field_data.for_mkb
    listing.financial_instrument = field_data.financial_instrument
    listing.sector = field_data.sector
    
    await session.commit()
    return listing


async def chunk_webpage(webpage: models.Webpage, session):
    ai_client = create_ai_client("gemini")  # Use ollama by default

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
    md_header_splits = markdown_splitter.split_text(webpage.markdown_content)
    logger.info(f"Split text into {len(md_header_splits)} chunks from webpage {webpage.url}")
    chunks = []
    for i in range(0, len(md_header_splits), 16):
        cur_set = md_header_splits[i:i + 16]
        texts = [i.page_content for i in cur_set]
        embeddings = await ai_client.embed_content(texts)
        for e, t in zip(embeddings, texts):
            c = models.Chunk(
                owner_type=models.ChunkOwnerType.WEBPAGE,
                owner_id=webpage.id,
                content=t,
                emb=e
            )
            session.add(c)
            chunks.append(c)
    
    await session.commit()
