import httpx
from sqlalchemy.dialects.postgresql import insert
import logging
from aanvraagapp import models
from .ai_client import get_client
from aanvraagapp.config import settings
from aanvraagapp.parsing.prompts import prompts
from aanvraagapp.parsing.structured_outputs import StructuredOutputSchema, ListingFieldData, ClientFieldData
from .clean import clean_html
from langchain_text_splitters import MarkdownHeaderTextSplitter
from typing import TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Sequence


logger = logging.getLogger(__name__)


# UTILS
async def clean_and_parse_into_md(url: str, prompt_name: str):
    # Get the raw HTML data from the web page.
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
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
    ai_client = get_client("gemini")
    converted_to_markdown = await ai_client.generate_content(prompt_content)

    return html_content, cleaned_html, converted_to_markdown


T = TypeVar("T", bound=StructuredOutputSchema)


async def extract_field_data(
    md_content: str, prompt_name: str, output_schema: type[T]
) -> T:
    ai_client = get_client("gemini")
    template = prompts.get_template(prompt_name)
    prompt_content = template.render(md_content=md_content, schema=output_schema)
    json_with_field_data = await ai_client.generate_content(
        prompt_content, output_schema=output_schema
    )
    # Gemini does not support sets in its schema enforcement (unique values),
    # however, by instantiating the schema, we filter out duplicates for set
    # fields in Pydantic.
    field_data = output_schema.model_validate_json(json_with_field_data)
    return field_data


# WEBPAGE
async def chunk_webpage(webpage: models.Webpage, session: AsyncSession):
    ai_client = get_client("gemini")

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on, strip_headers=False
    )
    md_header_splits = markdown_splitter.split_text(webpage.markdown_content)
    logger.info(
        f"Split text into {len(md_header_splits)} chunks from webpage {webpage.url}"
    )
    chunks = []
    for i in range(0, len(md_header_splits), 16):
        cur_set = md_header_splits[i : i + 16]
        texts = [i.page_content for i in cur_set]
        embeddings = await ai_client.embed_content(texts)
        for e, t in zip(embeddings, texts):
            c = models.Chunk(
                owner_type=models.ChunkOwnerType.WEBPAGE,
                owner_id=webpage.id,
                content=t,
                emb=e,
            )
            session.add(c)
            chunks.append(c)


# LISTING
async def parse_webpage_from_listing(listing: models.Listing, session: AsyncSession):
    html_content, cleaned_html, converted_to_markdown = await clean_and_parse_into_md(
        listing.website, "rewrite_subsidy_in_md.jinja"
    )

    webpage = models.Webpage(
        owner_type=models.WebpageOwnerType.LISTING,
        owner_id=listing.id,
        url=listing.website,
        original_content=html_content,
        filtered_content=cleaned_html,
        markdown_content=converted_to_markdown,
    )
    session.add(webpage)

    return webpage


async def parse_field_data_from_listing(listing: models.Listing, session: AsyncSession):
    assert len(listing.websites) > 0, "No parsed websites yet"
    assert len(listing.websites) == 1, (
        "Support only single website from entry url at this moment"
    )
    assert len(listing.target_audience_labels) == 0, "Labels are already added to this listing"

    webpage = listing.websites[0]

    field_data = await extract_field_data(
        webpage.markdown_content, "extract_field_data_from_md.jinja", ListingFieldData
    )

    listing.is_open = field_data.is_open
    listing.opens_at = field_data.opens_at
    listing.closes_at = field_data.closes_at
    listing.last_checked = field_data.last_checked
    listing.name = field_data.name
    listing.financial_instrument = field_data.financial_instrument
    listing.target_audience_desc = field_data.target_audience_desc

    # Ensure all extracted target audience names exist. If one of them
    # already exists, no conflict occurs.
    extracted_target_audience_names = [t.value for t in field_data.target_audiences]
    for name in extracted_target_audience_names:
        stmt = insert(models.TargetAudienceLabel).values(name=name)
        stmt = stmt.on_conflict_do_nothing(index_elements=['name'])
        await session.execute(stmt)
    
    # Flush to ensure inserts are processed
    await session.flush()
    
    # Now fetch all the labels (both newly created and pre-existing)
    # (This query also ensures duplicate target audience names by Gemini are removed)
    result = await session.execute(
        select(models.TargetAudienceLabel).where(
            models.TargetAudienceLabel.name.in_(extracted_target_audience_names)
        )
    )
    target_audience_labels = list(result.scalars().all())
    
    # Associate all labels with the listing
    for label in target_audience_labels:
        listing.target_audience_labels.append(label)

    return listing


# CLIENT
async def parse_webpage_from_client(client: models.Client, session: AsyncSession):
    html_content, cleaned_html, converted_to_markdown = await clean_and_parse_into_md(
        client.website, "rewrite_client_in_md.jinja"
    )

    webpage = models.Webpage(
        owner_type=models.WebpageOwnerType.CLIENT,
        owner_id=client.id,
        url=client.website,
        original_content=html_content,
        filtered_content=cleaned_html,
        markdown_content=converted_to_markdown,
    )
    session.add(webpage)

    return webpage


async def parse_field_data_from_client(client: models.Client, session: AsyncSession):
    assert len(client.websites) > 0, "No parsed websites yet"
    assert len(client.websites) == 1, (
        "Support only single website from entry url at this moment"
    )

    webpage = client.websites[0]

    field_data = await extract_field_data(
        webpage.markdown_content, "extract_field_data_from_md.jinja", ClientFieldData
    )

    client.business_identity = field_data.business_identity
    client.audience_desc = field_data.audience_desc

    return client
