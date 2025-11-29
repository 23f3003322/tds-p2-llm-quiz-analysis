"""
Correlation Analyzer
Calculate correlations between variables
"""

from typing import List, Dict, Any, Optional
import statistics
import math

from app.modules.analyzers.analysis_utils import extract_numeric_values
from app.core.logging import get_logger

logger = get_logger(__name__)


class CorrelationAnalyzer:
    """Calculate correlations between variables"""
    
    @staticmethod
    def pearson_correlation(x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient
        
        Args:
            x: First variable
            y: Second variable
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        
        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)
        
        denominator = math.sqrt(sum_sq_x * sum_sq_y)
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    @staticmethod
    def correlation_strength(correlation: float) -> str:
        """
        Interpret correlation strength
        
        Args:
            correlation: Correlation coefficient
            
        Returns:
            Strength description
        """
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.9:
            return "very strong"
        elif abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.5:
            return "moderate"
        elif abs_corr >= 0.3:
            return "weak"
        else:
            return "very weak"
    
    @staticmethod
    def correlation_direction(correlation: float) -> str:
        """Get correlation direction"""
        if correlation > 0:
            return "positive"
        elif correlation < 0:
            return "negative"
        else:
            return "none"
    
    @staticmethod
    def analyze_correlation(
        data: List[Dict[str, Any]],
        column1: str,
        column2: str
    ) -> Dict[str, Any]:
        """
        Analyze correlation between two columns
        
        Args:
            data: List of records
            column1: First column
            column2: Second column
            
        Returns:
            Correlation analysis
        """
        values1 = extract_numeric_values(data, column1)
        values2 = extract_numeric_values(data, column2)
        
        # Match lengths
        min_len = min(len(values1), len(values2))
        values1 = values1[:min_len]
        values2 = values2[:min_len]
        
        if len(values1) < 2:
            return {
                "coefficient": 0,
                "strength": "insufficient data",
                "direction": "none"
            }
        
        coefficient = CorrelationAnalyzer.pearson_correlation(values1, values2)
        
        return {
            "coefficient": round(coefficient, 3),
            "strength": CorrelationAnalyzer.correlation_strength(coefficient),
            "direction": CorrelationAnalyzer.correlation_direction(coefficient),
            "sample_size": len(values1)
        }
    
    @staticmethod
    def correlation_matrix(
        data: List[Dict[str, Any]],
        columns: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for multiple columns
        
        Args:
            data: List of records
            columns: List of numeric columns
            
        Returns:
            Correlation matrix
        """
        matrix = {}
        
        for col1 in columns:
            matrix[col1] = {}
            
            for col2 in columns:
                if col1 == col2:
                    matrix[col1][col2] = 1.0
                else:
                    result = CorrelationAnalyzer.analyze_correlation(data, col1, col2)
                    matrix[col1][col2] = result['coefficient']
        
        return matrix
