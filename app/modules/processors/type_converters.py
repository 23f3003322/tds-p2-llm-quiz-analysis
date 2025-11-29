"""
Type Converters
Convert data types and parse special formats
"""

import re
from typing import Any, Optional
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)


def to_number(value: Any) -> Optional[float]:
    """
    Convert value to number
    Handles currency, percentages, thousands separators
    
    Args:
        value: Value to convert
        
    Returns:
        float or None
    """
    if value is None or value == "":
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        try:
            return float(value)
        except:
            return None
    
    # Remove common formatting
    value = value.strip()
    
    # Handle percentages
    if '%' in value:
        try:
            num = float(value.replace('%', '').strip())
            return num / 100.0
        except:
            return None
    
    # Handle currency
    # Remove currency symbols: $, €, £, ¥, ₹, etc.
    value = re.sub(r'[$€£¥₹,]', '', value)
    
    # Handle negative in parentheses: (100) -> -100
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    
    # Try to convert
    try:
        return float(value)
    except:
        return None


def to_boolean(value: Any) -> Optional[bool]:
    """
    Convert value to boolean
    
    Args:
        value: Value to convert
        
    Returns:
        bool or None
    """
    if value is None or value == "":
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    if isinstance(value, str):
        value = value.strip().lower()
        
        # True values
        if value in ('true', 'yes', 'y', '1', 'on', 't'):
            return True
        
        # False values
        if value in ('false', 'no', 'n', '0', 'off', 'f'):
            return False
    
    return None


def to_date(value: Any, formats: Optional[list] = None) -> Optional[datetime]:
    """
    Convert value to datetime
    
    Args:
        value: Value to convert
        formats: List of date formats to try
        
    Returns:
        datetime or None
    """
    if value is None or value == "":
        return None
    
    if isinstance(value, datetime):
        return value
    
    if not isinstance(value, str):
        return None
    
    value = value.strip()
    
    # Default formats to try
    if formats is None:
        formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ'
        ]
    
    # Try each format
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            continue
    
    return None


def parse_special_value(value: Any) -> Optional[Any]:
    """
    Parse special values like N/A, null, etc.
    
    Args:
        value: Value to parse
        
    Returns:
        Parsed value or None
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        value = value.strip().lower()
        
        # Null-like values
        null_values = {'', 'n/a', 'na', 'null', 'none', 'nil', '-', '--', 'nan'}
        
        if value in null_values:
            return None
    
    return value


def clean_text(value: Any, strategy: str = 'trim') -> str:
    """
    Clean text value
    
    Args:
        value: Text to clean
        strategy: Cleaning strategy
        
    Returns:
        Cleaned text
    """
    if value is None:
        return ""
    
    text = str(value)
    
    if strategy == 'trim':
        return text.strip()
    
    elif strategy == 'lowercase':
        return text.strip().lower()
    
    elif strategy == 'uppercase':
        return text.strip().upper()
    
    elif strategy == 'title_case':
        return text.strip().title()
    
    elif strategy == 'remove_special':
        # Keep only alphanumeric and spaces
        return re.sub(r'[^a-zA-Z0-9\s]', '', text).strip()
    
    elif strategy == 'normalize':
        # Trim + lowercase + collapse whitespace
        text = text.strip().lower()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    return text
