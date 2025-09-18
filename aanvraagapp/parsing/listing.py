import httpx
import logging
from aanvraagapp import models
from .ai import create_ai_client
from aanvraagapp.config import settings
from aanvraagapp.parsing.prompts import prompts
from .clean import clean_html
from langchain_text_splitters import MarkdownHeaderTextSplitter


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


async def parse_listing(listing: models.Listing, session):
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
