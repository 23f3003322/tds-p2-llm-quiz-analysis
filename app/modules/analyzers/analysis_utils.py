"""
Analysis Utilities
Helper functions for data analysis
"""

from typing import List, Dict, Any, Optional
import statistics
import math

from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_numeric_values(
    data: List[Dict[str, Any]],
    column: str
) -> List[float]:
    """
    Extract numeric values from column
    
    Args:
        data: List of records
        column: Column name
        
    Returns:
        List of numeric values
    """
    values = []
    
    for record in data:
        value = record.get(column)
        
        if value is not None:
            try:
                values.append(float(value))
            except (ValueError, TypeError):
                pass
    
    return values


def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate percentile
    
    Args:
        values: List of values
        percentile: Percentile (0-100)
        
    Returns:
        Percentile value
    """
    if not values:
        return 0
    
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (percentile / 100)
    f = math.floor(k)
    c = math.ceil(k)
    
    if f == c:
        return sorted_values[int(k)]
    
    d0 = sorted_values[int(f)] * (c - k)
    d1 = sorted_values[int(c)] * (k - f)
    
    return d0 + d1


def calculate_iqr(values: List[float]) -> tuple[float, float, float]:
    """
    Calculate interquartile range
    
    Args:
        values: List of values
        
    Returns:
        Tuple of (Q1, Q3, IQR)
    """
    if len(values) < 4:
        return (0, 0, 0)
    
    q1 = calculate_percentile(values, 25)
    q3 = calculate_percentile(values, 75)
    iqr = q3 - q1
    
    return (q1, q3, iqr)


def detect_outliers_zscore(
    values: List[float],
    threshold: float = 3.0
) -> List[int]:
    """
    Detect outliers using Z-score method
    
    Args:
        values: List of values
        threshold: Z-score threshold
        
    Returns:
        List of outlier indices
    """
    if len(values) < 3:
        return []
    
    mean = statistics.mean(values)
    std = statistics.stdev(values)
    
    if std == 0:
        return []
    
    outliers = []
    
    for i, value in enumerate(values):
        z_score = abs((value - mean) / std)
        if z_score > threshold:
            outliers.append(i)
    
    return outliers


def detect_outliers_iqr(values: List[float]) -> List[int]:
    """
    Detect outliers using IQR method
    
    Args:
        values: List of values
        
    Returns:
        List of outlier indices
    """
    if len(values) < 4:
        return []
    
    q1, q3, iqr = calculate_iqr(values)
    
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    outliers = []
    
    for i, value in enumerate(values):
        if value < lower_bound or value > upper_bound:
            outliers.append(i)
    
    return outliers


def calculate_growth_rate(values: List[float]) -> float:
    """
    Calculate average growth rate
    
    Args:
        values: List of values (ordered by time)
        
    Returns:
        Average growth rate
    """
    if len(values) < 2:
        return 0
    
    growth_rates = []
    
    for i in range(1, len(values)):
        if values[i-1] != 0:
            growth = (values[i] - values[i-1]) / values[i-1]
            growth_rates.append(growth)
    
    return statistics.mean(growth_rates) if growth_rates else 0


def is_increasing_trend(values: List[float]) -> bool:
    """
    Check if values show increasing trend
    
    Args:
        values: List of values
        
    Returns:
        True if increasing
    """
    if len(values) < 2:
        return False
    
    increases = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
    
    return increases > len(values) / 2
