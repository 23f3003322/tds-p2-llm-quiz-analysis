"""
Statistical Analyzer
Pure statistical analysis (no LLM)
Fast, accurate, deterministic
"""

from typing import List, Dict, Any, Optional
import statistics

from app.modules.analyzers.base_analyzer import BaseAnalyzer, AnalysisResult
from app.modules.analyzers.correlation_analyzer import CorrelationAnalyzer
from app.modules.analyzers.trend_analyzer import TrendAnalyzer
from app.modules.analyzers.analysis_utils import (
    extract_numeric_values,
    calculate_percentile,
    calculate_iqr,
    detect_outliers_zscore,
    detect_outliers_iqr
)
from app.modules.base import ModuleCapability
from app.modules.capabilities import ProcessingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class StatisticalAnalyzer(BaseAnalyzer):
    """
    Pure statistical analyzer
    No LLM - fast, accurate, cheap
    """
    
    def __init__(self):
        super().__init__(name="statistical_analyzer")
        logger.debug("StatisticalAnalyzer initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return ProcessingCapability.TRANSFORM
    
    async def analyze(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Perform statistical analysis
        
        Args:
            data: Data to analyze (list of dicts)
            options: Analysis options
                - columns: Specific columns to analyze
                - correlations: Column pairs to correlate
                - detect_outliers: Whether to detect outliers
                
        Returns:
            AnalysisResult: Statistical results
        """
        options = options or {}
        
        if not isinstance(data, list):
            return AnalysisResult(
                success=False,
                error="Data must be a list of records"
            )
        
        if not data:
            return AnalysisResult(
                success=True,
                statistics={},
                rows_analyzed=0
            )
        
        logger.info(f"Analyzing {len(data)} records")
        
        statistics_result = {}
        
        # 1. Descriptive statistics
        statistics_result['descriptive'] = self._descriptive_statistics(data, options)
        
        # 2. Correlations
        if 'correlations' in options:
            statistics_result['correlations'] = self._analyze_correlations(data, options['correlations'])
        
        # 3. Trends
        if 'trend_column' in options:
            statistics_result['trends'] = self._analyze_trends(data, options['trend_column'])
        
        # 4. Outliers
        if options.get('detect_outliers', False):
            statistics_result['outliers'] = self._detect_outliers(data, options)
        
        # 5. Segment analysis
        if 'segment_by' in options:
            statistics_result['segments'] = self._segment_analysis(
                data,
                options['segment_by'],
                options.get('segment_metric')
            )
        
        logger.info(f"✓ Statistical analysis complete")
        
        return AnalysisResult(
            success=True,
            statistics=statistics_result,
            rows_analyzed=len(data),
            analysis_type="statistical"
        )
    
    def _descriptive_statistics(
        self,
        data: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate descriptive statistics for numeric columns"""
        
        # Get numeric columns
        if 'columns' in options:
            columns = options['columns']
        else:
            # Auto-detect numeric columns
            columns = []
            if data:
                for key, value in data[0].items():
                    try:
                        float(value)
                        columns.append(key)
                    except (ValueError, TypeError):
                        pass
        
        results = {}
        
        for column in columns:
            values = extract_numeric_values(data, column)
            
            if len(values) < 1:
                continue
            
            q1, q3, iqr = calculate_iqr(values)
            
            results[column] = {
                'count': len(values),
                'mean': round(statistics.mean(values), 2),
                'median': round(statistics.median(values), 2),
                'std': round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                'min': round(min(values), 2),
                'max': round(max(values), 2),
                'q1': round(q1, 2),
                'q3': round(q3, 2),
                'iqr': round(iqr, 2),
                'range': round(max(values) - min(values), 2)
            }
        
        return results
    
    def _analyze_correlations(
        self,
        data: List[Dict[str, Any]],
        correlation_pairs: List[tuple]
    ) -> Dict[str, Any]:
        """Analyze correlations between column pairs"""
        
        results = {}
        
        for col1, col2 in correlation_pairs:
            key = f"{col1}_vs_{col2}"
            results[key] = CorrelationAnalyzer.analyze_correlation(data, col1, col2)
        
        return results
    
    def _analyze_trends(
        self,
        data: List[Dict[str, Any]],
        column: str
    ) -> Dict[str, Any]:
        """Analyze trends in a column"""
        
        values = extract_numeric_values(data, column)
        
        if not values:
            return {}
        
        trend = TrendAnalyzer.detect_trend(values)
        forecast = TrendAnalyzer.forecast_next(values)
        
        return {
            'trend': trend,
            'forecast_next': round(forecast, 2),
            'current_value': round(values[-1], 2) if values else 0
        }
    
    def _detect_outliers(
        self,
        data: List[Dict[str, Any]],
        options: Dict[str, Any]
    ) -> Dict[str, List[int]]:
        """Detect outliers in numeric columns"""
        
        columns = options.get('columns', [])
        results = {}
        
        for column in columns:
            values = extract_numeric_values(data, column)
            
            if len(values) < 3:
                continue
            
            outlier_indices = detect_outliers_zscore(values)
            
            if outlier_indices:
                results[column] = outlier_indices
        
        return results
    
    def _segment_analysis(
        self,
        data: List[Dict[str, Any]],
        segment_by: str,
        metric: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze data by segments"""
        
        from collections import defaultdict
        
        segments = defaultdict(list)
        
        # Group by segment
        for record in data:
            segment_value = record.get(segment_by)
            segments[segment_value].append(record)
        
        # Analyze each segment
        results = {}
        
        for segment_value, segment_data in segments.items():
            results[str(segment_value)] = {
                'count': len(segment_data)
            }
            
            if metric:
                values = extract_numeric_values(segment_data, metric)
                if values:
                    results[str(segment_value)]['avg'] = round(statistics.mean(values), 2)
                    results[str(segment_value)]['total'] = round(sum(values), 2)
        
        return results
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute via module interface"""
        data = parameters.get('data')
        options = parameters.get('options', {})
        
        return await self.analyze(data, options)
