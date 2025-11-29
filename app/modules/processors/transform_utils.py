"""
Transform Utilities
Helper functions for data transformation
"""

from typing import List, Dict, Any, Optional, Callable
import random

from app.core.logging import get_logger

logger = get_logger(__name__)


def sort_data(
    data: List[Dict[str, Any]],
    columns: List[str],
    ascending: bool = True
) -> List[Dict[str, Any]]:
    """
    Sort data by columns
    
    Args:
        data: List of records
        columns: Columns to sort by (in order)
        ascending: Sort ascending or descending
        
    Returns:
        Sorted data
    """
    if not columns:
        return data
    
    def sort_key(record):
        return tuple(record.get(col) for col in columns)
    
    return sorted(data, key=sort_key, reverse=not ascending)


def select_columns(
    data: List[Dict[str, Any]],
    columns: List[str]
) -> List[Dict[str, Any]]:
    """
    Select specific columns
    
    Args:
        data: List of records
        columns: Columns to keep
        
    Returns:
        Data with selected columns
    """
    return [
        {col: record.get(col) for col in columns if col in record}
        for record in data
    ]


def rename_columns(
    data: List[Dict[str, Any]],
    mapping: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Rename columns
    
    Args:
        data: List of records
        mapping: Old name -> new name mapping
        
    Returns:
        Data with renamed columns
    """
    result = []
    
    for record in data:
        new_record = {}
        for old_name, value in record.items():
            new_name = mapping.get(old_name, old_name)
            new_record[new_name] = value
        result.append(new_record)
    
    return result


def add_column(
    data: List[Dict[str, Any]],
    column: str,
    value: Any = None,
    function: Optional[Callable] = None
) -> List[Dict[str, Any]]:
    """
    Add new column
    
    Args:
        data: List of records
        column: New column name
        value: Static value (if function is None)
        function: Function to calculate value (receives record)
        
    Returns:
        Data with new column
    """
    for record in data:
        if function:
            record[column] = function(record)
        else:
            record[column] = value
    
    return data


def limit_data(
    data: List[Dict[str, Any]],
    limit: int,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Limit number of records
    
    Args:
        data: List of records
        limit: Maximum records to return
        offset: Starting offset
        
    Returns:
        Limited data
    """
    return data[offset:offset + limit]


def sample_data(
    data: List[Dict[str, Any]],
    n: int,
    random_state: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Random sample of data
    
    Args:
        data: List of records
        n: Number of samples
        random_state: Random seed for reproducibility
        
    Returns:
        Sampled data
    """
    if random_state is not None:
        random.seed(random_state)
    
    n = min(n, len(data))
    return random.sample(data, n)


def distinct(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get distinct records
    
    Args:
        data: List of records
        columns: Columns to check for uniqueness (None = all columns)
        
    Returns:
        Distinct records
    """
    seen = set()
    result = []
    
    for record in data:
        if columns:
            key = tuple(record.get(col) for col in columns)
        else:
            key = tuple(sorted(record.items()))
        
        if key not in seen:
            seen.add(key)
            result.append(record)
    
    return result
