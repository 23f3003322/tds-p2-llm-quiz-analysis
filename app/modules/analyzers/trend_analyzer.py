"""
Trend Analyzer
Detect and analyze trends in data
"""

from typing import List, Dict, Any, Optional
import statistics

from app.modules.analyzers.analysis_utils import (
    extract_numeric_values,
    calculate_growth_rate,
    is_increasing_trend
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class TrendAnalyzer:
    """Analyze trends in time series data"""
    
    @staticmethod
    def detect_trend(
        values: List[float]
    ) -> Dict[str, Any]:
        """
        Detect trend in values
        
        Args:
            values: List of values (ordered by time)
            
        Returns:
            Trend analysis
        """
        if len(values) < 2:
            return {
                "trend": "insufficient_data",
                "direction": "unknown",
                "growth_rate": 0,
                "confidence": 0
            }
        
        # Calculate growth rate
        growth_rate = calculate_growth_rate(values)
        
        # Determine direction
        if is_increasing_trend(values):
            direction = "increasing"
        elif growth_rate < -0.01:
            direction = "decreasing"
        else:
            direction = "stable"
        
        # Calculate confidence (based on consistency)
        if len(values) > 2:
            changes = [values[i] - values[i-1] for i in range(1, len(values))]
            positive = sum(1 for c in changes if c > 0)
            negative = sum(1 for c in changes if c < 0)
            
            max_consistent = max(positive, negative)
            confidence = max_consistent / len(changes)
        else:
            confidence = 0.5
        
        return {
            "trend": direction,
            "direction": direction,
            "growth_rate": round(growth_rate, 4),
            "confidence": round(confidence, 2),
            "data_points": len(values)
        }
    
    @staticmethod
    def moving_average(
        values: List[float],
        window: int = 3
    ) -> List[float]:
        """
        Calculate moving average
        
        Args:
            values: List of values
            window: Window size
            
        Returns:
            Moving averages
        """
        if len(values) < window:
            return values
        
        averages = []
        
        for i in range(len(values) - window + 1):
            window_values = values[i:i + window]
            avg = statistics.mean(window_values)
            averages.append(avg)
        
        return averages
    
    @staticmethod
    def forecast_next(
        values: List[float],
        method: str = "simple"
    ) -> float:
        """
        Simple forecast of next value
        
        Args:
            values: List of values
            method: Forecasting method
            
        Returns:
            Forecasted value
        """
        if not values:
            return 0
        
        if method == "simple":
            # Use growth rate
            if len(values) >= 2:
                growth_rate = calculate_growth_rate(values)
                return values[-1] * (1 + growth_rate)
            else:
                return values[-1]
        
        elif method == "average":
            # Use average of last 3 values
            recent = values[-3:] if len(values) >= 3 else values
            return statistics.mean(recent)
        
        return values[-1]
