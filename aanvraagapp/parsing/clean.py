from bs4 import BeautifulSoup, Tag, Comment

# Define tags and attributes to remove
TAGS_TO_REMOVE = ['script', 'style', 'link', 'meta', 'noscript', 'header', 'footer', 'nav', 'aside']
UNWANTED_ATTRS = [
    'class', 'id', 'style', 'role', 'aria-label', 'aria-hidden', 'aria-expanded',
    'tabindex', 'onclick', 'onmouseover', 'onfocus', 'onblur',
]

def clean_html(html: str, extract_main: bool = False) -> str:
    """
    Cleans HTML using BeautifulSoup to remove non-content elements and attributes.

    Args:
        html: The raw HTML string.
        extract_main: If True, tries to extract only the <main> or <article> content.

    Returns:
        A cleaned HTML string.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 1. (Optional but Recommended) Extract main content
    if extract_main:
        main_content = soup.find('main') or soup.find('article')
        if main_content:
            # Replace the entire body with just the main content
            body = soup.new_tag('body')
            body.append(main_content)
            # Clear head and replace body
            if soup.head:
                soup.head.clear()
            # Ensure soup.html and soup.html.body exist before accessing
            if soup.html and soup.html.body:
                soup.html.body.replace_with(body)
        # If no main content found, it will proceed to clean the whole document

    # 2. Remove unwanted tags
    for tag_name in TAGS_TO_REMOVE:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 3. Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 4. Remove unwanted attributes from all remaining tags
    for tag in soup.find_all(True):
        # Only process Tag objects, not NavigableString objects
        if isinstance(tag, Tag):
            attrs = dict(tag.attrs)
            for attr in attrs:
                if attr in UNWANTED_ATTRS or attr.startswith('data-'):
                    del tag[attr]

    # 5. Simplify image tags
    for img_tag in soup.find_all('img'):
        # Only process Tag objects, not NavigableString objects
        if isinstance(img_tag, Tag):
            attrs = dict(img_tag.attrs)
            for attr in attrs:
                if attr not in ['src', 'alt']:
                    del img_tag[attr]

    # 6. Remove empty tags (optional, can sometimes remove meaningful layout tags)
    # for tag in soup.find_all():
    #     if not tag.text.strip() and not tag.find(True):
    #         tag.decompose()
            
    # Return the pretty-printed HTML
    return soup.prettify()
