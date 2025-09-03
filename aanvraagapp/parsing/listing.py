import httpx
import logging
from bs4 import BeautifulSoup, Comment, Tag
from bs4.element import NavigableString
from aanvraagapp import models

logger = logging.getLogger(__name__)

def simplify_html(html_content):
    """
    Simplify HTML content to preserve only human-readable content and structure.
    
    Args:
        html_content (str): The HTML content to simplify
        
    Returns:
        str: Simplified HTML
    """
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Define tags we want to preserve (content-related tags)
    preserve_tags = {
        # Text content
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'span', 'strong', 'b', 'em', 'i', 'u',
        'blockquote', 'pre', 'code',
        # Lists
        'ul', 'ol', 'li', 'dl', 'dt', 'dd',
        # Tables
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'td', 'th',
        # Links
        'a',
        # Other content elements
        'br', 'hr', 'abbr', 'cite', 'mark', 'sub', 'sup'
    }
    
    # Tags to always remove (even if they have content)
    always_remove_tags = {
        'script', 'style', 'meta', 'link', 'noscript', 
        'img', 'svg', 'canvas', 'video', 'audio', 'iframe',
        'object', 'embed', 'source', 'track', 'area', 'map'
    }
    
    # First pass: Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Remove all tags that should always be removed
    for tag_name in always_remove_tags:
        for tag in soup.find_all(tag_name):
            tag.decompose()
    
    def has_text_content(element):
        """Check if an element or its descendants contain meaningful text."""
        if isinstance(element, NavigableString):
            return bool(element.strip())
        if hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            return bool(text)
        return False
    
    # Process all elements to clean attributes and handle unwrapping
    # We need to collect elements first to avoid modifying the tree while iterating
    all_elements = list(soup.find_all(True))  # Find all tags
    
    for element in all_elements:
        # Skip if element was already removed
        if not element.parent:
            continue
            
        if element.name in preserve_tags:
            # For preserved tags, clean attributes
            if element.name == 'a':
                # Keep only href for links
                href = element.get('href')
                element.attrs.clear()
                if href:
                    element['href'] = href
            else:
                # Remove all attributes for other preserved tags
                element.attrs.clear()
        else:
            # For non-preserved tags (div, section, article, etc.)
            # Check if they have text content
            if has_text_content(element):
                # Unwrap - replace tag with its contents
                element.unwrap()
            else:
                # Remove empty elements
                element.decompose()
    
    # Clean up whitespace in text nodes
    def clean_whitespace(soup):
        """Clean up excessive whitespace."""
        for element in soup.find_all(string=True):
            if isinstance(element, NavigableString):
                # Skip if in a pre tag
                if element.parent and element.parent.name == 'pre':
                    continue
                    
                # Get the text and clean it
                text = str(element)
                # Collapse multiple spaces and newlines
                text = ' '.join(text.split())
                
                if text:
                    element.replace_with(text)
                elif element.parent:
                    # Remove empty text nodes
                    element.extract()
    
    clean_whitespace(soup)
    
    # Format the output nicely
    result = soup.prettify()
    
    # Clean up empty lines from prettify
    lines = result.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip():
            cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines)

async def parse_listing(listing: models.Listing):
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
        
        # Use the improved HTML simplification function
        cleaned_html = simplify_html(html_content)
        
        if not cleaned_html.strip():
            logger.warning(f"No meaningful content found after cleaning HTML from {listing.website}")
            return None
        
        logger.info(f"Successfully cleaned HTML from {listing.website}")
        
        return cleaned_html
        
    except httpx.RequestError as e:
        logger.error(f"Listing API request failed : {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return None
