"""
API Utilities
Helper functions for API clients
"""

from typing import Dict, Any, Optional, List
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


def build_url(base_url: str, path: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    Build complete URL with parameters
    
    Args:
        base_url: Base URL
        path: Path to append
        params: Query parameters
        
    Returns:
        str: Complete URL
    """
    # Join base and path
    url = urljoin(base_url, path)
    
    # Add parameters
    if params:
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        if params:
            query_string = urlencode(params)
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{query_string}"
    
    return url


def extract_pagination_info(response_data: Any, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract pagination information from response
    
    Args:
        response_data: Response data
        headers: Response headers
        
    Returns:
        Dict: Pagination info
    """
    pagination = {
        'has_next': False,
        'next_page': None,
        'total_pages': None,
        'total_items': None
    }
    
    # Check headers for Link header (GitHub style)
    if 'Link' in headers:
        link_header = headers['Link']
        if 'rel="next"' in link_header:
            pagination['has_next'] = True
            # Extract next URL
            match = re.search(r'<([^>]+)>;\s*rel="next"', link_header)
            if match:
                pagination['next_page'] = match.group(1)
    
    # Check response data for pagination (common patterns)
    if isinstance(response_data, dict):
        # Pattern 1: pagination object
        if 'pagination' in response_data:
            pag = response_data['pagination']
            pagination['has_next'] = pag.get('has_next', False)
            pagination['next_page'] = pag.get('next_page')
            pagination['total_pages'] = pag.get('total_pages')
            pagination['total_items'] = pag.get('total_items')
        
        # Pattern 2: next_page field
        elif 'next_page' in response_data:
            pagination['next_page'] = response_data['next_page']
            pagination['has_next'] = response_data['next_page'] is not None
        
        # Pattern 3: page info
        elif 'page' in response_data and 'total_pages' in response_data:
            current = response_data['page']
            total = response_data['total_pages']
            pagination['has_next'] = current < total
            pagination['total_pages'] = total
    
    return pagination


def parse_error_response(status_code: int, response_data: Any) -> Dict[str, str]:
    """
    Parse error response
    
    Args:
        status_code: HTTP status code
        response_data: Response data
        
    Returns:
        Dict: Error information
    """
    error = {
        'message': f"HTTP {status_code}",
        'code': str(status_code)
    }
    
    if isinstance(response_data, dict):
        # Common error patterns
        error['message'] = (
            response_data.get('error') or
            response_data.get('message') or
            response_data.get('error_description') or
            str(response_data)
        )
        
        error['code'] = str(
            response_data.get('error_code') or
            response_data.get('code') or
            status_code
        )
    
    return error


def flatten_nested_response(data: Any, max_depth: int = 3) -> List[Dict[str, Any]]:
    """
    Flatten nested API response to list of records
    
    Args:
        data: Response data
        max_depth: Maximum nesting depth to explore
        
    Returns:
        List[Dict]: Flattened records
    """
    if isinstance(data, list):
        return data
    
    if isinstance(data, dict):
        # Try common data keys
        data_keys = ['data', 'results', 'items', 'records', 'rows']
        
        for key in data_keys:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # If single object, wrap in list
        return [data]
    
    return []
