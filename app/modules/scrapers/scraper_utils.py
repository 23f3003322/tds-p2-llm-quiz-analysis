"""
Scraper Utilities
Helper functions for web scraping
"""

from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import re

from bs4 import BeautifulSoup, Tag
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract all links from page
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative links
        
    Returns:
        List[str]: List of absolute URLs
    """
    links = []
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        links.append(absolute_url)
    
    return links


def extract_images(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """
    Extract all images from page
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List[Dict]: List of image info (src, alt, title)
    """
    images = []
    
    for img_tag in soup.find_all('img', src=True):
        img_info = {
            'src': urljoin(base_url, img_tag['src']),
            'alt': img_tag.get('alt', ''),
            'title': img_tag.get('title', '')
        }
        images.append(img_info)
    
    return images


def extract_text_clean(element: Tag) -> str:
    """
    Extract and clean text from element
    
    Args:
        element: BeautifulSoup element
        
    Returns:
        str: Cleaned text
    """
    if not element:
        return ""
    
    text = element.get_text(strip=True)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_table_data(
    soup: BeautifulSoup,
    table_selector: str = 'table'
) -> List[Dict[str, Any]]:
    """
    Extract data from HTML table
    
    Args:
        soup: BeautifulSoup object
        table_selector: CSS selector for table
        
    Returns:
        List[Dict]: List of row data as dictionaries
    """
    tables = soup.select(table_selector)
    
    if not tables:
        return []
    
    table = tables[0]
    rows_data = []
    
    # Get headers
    headers = []
    header_row = table.find('thead')
    
    if header_row:
        headers = [
            extract_text_clean(th)
            for th in header_row.find_all(['th', 'td'])
        ]
    
    # Get rows
    tbody = table.find('tbody') or table
    
    for row in tbody.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        
        if not cells:
            continue
        
        # If no headers, use cell index
        if not headers:
            headers = [f'column_{i}' for i in range(len(cells))]
        
        row_data = {}
        for i, cell in enumerate(cells):
            if i < len(headers):
                row_data[headers[i]] = extract_text_clean(cell)
        
        if row_data:
            rows_data.append(row_data)
    
    return rows_data


def extract_list_data(
    soup: BeautifulSoup,
    list_selector: str = 'ul, ol',
    item_selector: str = 'li'
) -> List[str]:
    """
    Extract data from HTML list
    
    Args:
        soup: BeautifulSoup object
        list_selector: CSS selector for list container
        item_selector: CSS selector for list items
        
    Returns:
        List[str]: List of item texts
    """
    lists = soup.select(list_selector)
    
    items = []
    
    for list_elem in lists:
        for item in list_elem.select(item_selector):
            text = extract_text_clean(item)
            if text:
                items.append(text)
    
    return items


def extract_with_selectors(
    soup: BeautifulSoup,
    selectors: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Extract data using CSS selectors
    
    Args:
        soup: BeautifulSoup object
        selectors: Dictionary mapping field names to CSS selectors
        
    Returns:
        List[Dict]: Extracted data
    """
    # Find the container element with most results
    max_count = 0
    best_container_selector = None
    
    for field, selector in selectors.items():
        elements = soup.select(selector)
        if len(elements) > max_count:
            max_count = len(elements)
            best_container_selector = selector
    
    if not best_container_selector:
        return []
    
    # Get all container elements
    containers = soup.select(best_container_selector)
    
    results = []
    
    for container in containers:
        row_data = {}
        
        for field, selector in selectors.items():
            # Try to find element within container first
            element = container.select_one(selector)
            
            if element:
                row_data[field] = extract_text_clean(element)
            else:
                row_data[field] = ""
        
        if any(row_data.values()):
            results.append(row_data)
    
    return results


def detect_encoding(content: bytes) -> str:
    """
    Detect content encoding
    
    Args:
        content: Raw content bytes
        
    Returns:
        str: Detected encoding
    """
    try:
        import chardet
        result = chardet.detect(content)
        return result['encoding'] or 'utf-8'
    except ImportError:
        logger.warning("chardet not installed, defaulting to utf-8")
        return 'utf-8'
