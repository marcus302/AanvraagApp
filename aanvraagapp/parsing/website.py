import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Set, Optional
import asyncio
import logging
import trafilatura

logger = logging.getLogger(__name__)

async def create_client(timeout: int = 10) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={
            'User-Agent': 'Mozilla/5.0 (compatible; SitemapBot/1.0)'
        },
        timeout=timeout
    )

async def find_sitemap_urls(client: httpx.AsyncClient, base_url: str) -> List[str]:
    """
    Find sitemap URLs by checking common locations and robots.txt
    """
    sitemap_urls = []
    base_url = base_url.rstrip('/')
    
    # Common sitemap locations
    common_locations = [
        '/sitemap.xml',
        '/sitemap_index.xml',
        '/sitemaps.xml',
        '/sitemap1.xml'
    ]
    
    # Check robots.txt first
    try:
        robots_url = urljoin(base_url, '/robots.txt')
        response = await client.get(robots_url)
        if response.status_code == 200:
            for line in response.text.split('\n'):
                line = line.strip().lower()
                if line.startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemap_urls.append(sitemap_url)
    except httpx.RequestError:
        pass
    
    # Check common locations
    for location in common_locations:
        sitemap_url = urljoin(base_url, location)
        try:
            response = await client.head(sitemap_url)
            if response.status_code == 200:
                sitemap_urls.append(sitemap_url)
        except httpx.RequestError:
            continue
    
    return list(set(sitemap_urls))  # Remove duplicates

async def fetch_sitemap_content(client: httpx.AsyncClient, sitemap_url: str) -> Optional[str]:
    """
    Fetch the content of a sitemap URL
    """
    try:
        response = await client.get(sitemap_url)
        response.raise_for_status()
        return response.text
    except httpx.RequestError as e:
        logger.error(f"Failed to fetch {sitemap_url}: {e}")
        return None

def parse_sitemap_xml(xml_content: str) -> tuple[List[str], List[str]]:
    """
    Parse sitemap XML and extract URLs and nested sitemaps
    """
    page_urls = []
    nested_sitemaps = []
    
    try:
        root = ET.fromstring(xml_content)
        
        # TODO: I don't fully understand why I need this yet.
        # Handle different XML namespaces
        namespaces = {
            'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1',
            'news': 'http://www.google.com/schemas/sitemap-news/0.9'
        }
        
        # Check if this is a sitemap index
        sitemapindex_elements = root.findall('.//sitemap:sitemap', namespaces)
        if sitemapindex_elements:
            for sitemap_elem in sitemapindex_elements:
                loc_elem = sitemap_elem.find('sitemap:loc', namespaces)
                if loc_elem is not None:
                    nested_sitemaps.append(loc_elem.text.strip())
        
        # Extract regular URLs
        url_elements = root.findall('.//sitemap:url', namespaces)
        for url_elem in url_elements:
            loc_elem = url_elem.find('sitemap:loc', namespaces)
            if loc_elem is not None:
                page_urls.append(loc_elem.text.strip())
                
    except ET.ParseError as e:
        logger.error(f"Failed to parse XML: {e}")
    
    return page_urls, nested_sitemaps

async def extract_all_urls(client: httpx.AsyncClient, base_url: str) -> Set[str]:
    """
    Extract all URLs from sitemaps recursively. base_url could be https://spheer.ai e.g.
    """
    all_urls = set()
    processed_sitemaps = set()
    sitemap_queue = await find_sitemap_urls(client, base_url)
    
    logger.info(f"Found {len(sitemap_queue)} initial sitemap(s)")
    
    while sitemap_queue:
        current_sitemap = sitemap_queue.pop(0)
        if current_sitemap in processed_sitemaps:
            continue
        processed_sitemaps.add(current_sitemap)
        logger.info(f"Processing: {current_sitemap}")
        xml_content = await fetch_sitemap_content(client, current_sitemap)
        if not xml_content:
            continue
        page_urls, nested_sitemaps = parse_sitemap_xml(xml_content)
        all_urls.update(page_urls)
        for nested_sitemap in nested_sitemaps:
            if nested_sitemap not in processed_sitemaps:
                sitemap_queue.append(nested_sitemap)
        await asyncio.sleep(0.1)
    
    return all_urls

def build_hierarchy(urls: Set[str], base_url: str) -> Dict:
    """
    Build hierarchical structure from flat URL list
    """
    hierarchy = {}
    base_domain = urlparse(base_url).netloc
    
    for url in urls:
        parsed = urlparse(url)
        
        # Skip external URLs
        if parsed.netloc and parsed.netloc != base_domain:
            continue
            
        path = parsed.path.strip('/')
        if not path:
            path = 'home'
        
        # Split path into segments
        segments = path.split('/')
        
        # Navigate/create nested structure
        current_level = hierarchy
        for segment in segments:
            if segment not in current_level:
                current_level[segment] = {}
            current_level = current_level[segment]
    
    return hierarchy

def print_hierarchy(hierarchy: Dict, indent: int = 0) -> str:
    """
    Print hierarchy in tree format
    """
    result = ""
    for key, value in sorted(hierarchy.items()):
        result += "  " * indent + f"/{key}\n"
        if isinstance(value, dict) and value:
            result += print_hierarchy(value, indent + 1)
    return result


async def extract_page_content(client: httpx.AsyncClient, url: str) -> Optional[str]:
    """
    Extract page content using trafilatura and return as markdown string
    """
    try:
        response = await client.get(url)
        response.raise_for_status()
        # TODO: Research if this is blocking the event loop or is hurting performance.
        markdown_content = trafilatura.extract(response.text, include_links=True, output_format="markdown")
        logger.info(f"Successfully extracted content from {url}")
        return markdown_content
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.error(f"Failed to extract content from {url}: {e}")
        return None


async def extract_website_hierarchy(website_url: str, timeout: int = 10) -> tuple[Set[str], List[str | None]]:
    """
    Main function to extract and build URL hierarchy
    """
    logger.info(f"Extracting sitemap hierarchy from: {website_url}")
    
    client = await create_client(timeout)
    try:
        # Extract all URLs
        all_urls = await extract_all_urls(client, website_url)
        logger.info(f"Found {len(all_urls)} total URLs")
        
        # Extract content from all URLs
        markdown_contents = []
        for url in all_urls:
            content = await extract_page_content(client, url)
            markdown_contents.append(content)
            await asyncio.sleep(0.1)  # Rate limiting
        
        logger.info(f"Successfully extracted content from {len(markdown_contents)} pages")
        
        return all_urls, markdown_contents
    finally:
        await client.aclose()