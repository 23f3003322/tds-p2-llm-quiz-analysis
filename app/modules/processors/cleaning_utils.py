"""
Cleaning Utilities
Helper functions for data cleaning
"""

from typing import List, Dict, Any, Optional
import statistics

from app.core.logging import get_logger

logger = get_logger(__name__)


def remove_duplicates(
    data: List[Dict[str, Any]],
    strategy: str = 'drop_first',
    keys: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Remove duplicate records
    
    Args:
        data: List of records
        strategy: Deduplication strategy
        keys: Keys to check for duplicates (None = all keys)
        
    Returns:
        List of unique records
    """
    if not data:
        return data
    
    if strategy == 'keep_all':
        return data
    
    seen = set()
    result = []
    
    for record in data:
        # Create hashable key
        if keys:
            key = tuple(record.get(k) for k in keys)
        else:
            # Use all keys
            key = tuple(sorted(record.items()))
        
        if strategy == 'drop_first':
            # Keep last occurrence
            if key in seen:
                # Replace previous
                result = [r for r in result if tuple(sorted(r.items())) != key]
            seen.add(key)
            result.append(record)
        
        elif strategy == 'drop_last':
            # Keep first occurrence
            if key not in seen:
                seen.add(key)
                result.append(record)
        
        elif strategy == 'drop_all':
            # Remove all duplicates
            if key not in seen:
                seen.add(key)
                result.append(record)
            else:
                # Remove from result if already added
                result = [r for r in result if tuple(sorted(r.items())) != key]
    
    return result


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate statistics for numeric values
    
    Args:
        values: List of numeric values
        
    Returns:
        Dict with statistics
    """
    if not values:
        return {}
    
    return {
        'count': len(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'std': statistics.stdev(values) if len(values) > 1 else 0,
        'min': min(values),
        'max': max(values),
        'q1': statistics.quantiles(values, n=4)[0] if len(values) >= 4 else min(values),
        'q3': statistics.quantiles(values, n=4)[2] if len(values) >= 4 else max(values)
    }


def get_mode(values: List[Any]) -> Any:
    """
    Get most common value (mode)
    
    Args:
        values: List of values
        
    Returns:
        Most common value
    """
    if not values:
        return None
    
    try:
        return statistics.mode(values)
    except statistics.StatisticsError:
        # No unique mode, return first
        return values[0]


def is_missing(value: Any) -> bool:
    """
    Check if value is missing/null
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if missing
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        value = value.strip().lower()
        null_values = {'', 'n/a', 'na', 'null', 'none', 'nil', '-', '--', 'nan'}
        return value in null_values
    
    return False
