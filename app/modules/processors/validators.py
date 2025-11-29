"""
Data Validators
Validate data quality and format
"""

import re
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def is_valid_email(value: Any) -> bool:
    """Validate email address"""
    if not isinstance(value, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value.strip()))


def is_valid_url(value: Any) -> bool:
    """Validate URL"""
    if not isinstance(value, str):
        return False
    
    pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(pattern, value.strip()))


def is_valid_phone(value: Any) -> bool:
    """Validate phone number (simple check)"""
    if not isinstance(value, str):
        return False
    
    # Remove common formatting
    cleaned = re.sub(r'[\s\-\(\)\+]', '', value)
    
    # Check if 10-15 digits
    return bool(re.match(r'^\d{10,15}$', cleaned))


def is_in_range(value: Any, min_val: float = None, max_val: float = None) -> bool:
    """Check if value is in range"""
    try:
        num = float(value)
        
        if min_val is not None and num < min_val:
            return False
        
        if max_val is not None and num > max_val:
            return False
        
        return True
    except:
        return False


def detect_outlier_zscore(value: float, mean: float, std: float, threshold: float = 3.0) -> bool:
    """
    Detect outlier using Z-score method
    
    Args:
        value: Value to check
        mean: Mean of dataset
        std: Standard deviation
        threshold: Z-score threshold (default: 3.0)
        
    Returns:
        bool: True if outlier
    """
    if std == 0:
        return False
    
    z_score = abs((value - mean) / std)
    return z_score > threshold


def detect_outlier_iqr(value: float, q1: float, q3: float) -> bool:
    """
    Detect outlier using IQR method
    
    Args:
        value: Value to check
        q1: First quartile (25th percentile)
        q3: Third quartile (75th percentile)
        
    Returns:
        bool: True if outlier
    """
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    return value < lower_bound or value > upper_bound
