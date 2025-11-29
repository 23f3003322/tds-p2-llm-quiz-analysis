"""
Aggregator
Statistical aggregations and group by operations
"""

from typing import List, Dict, Any, Callable, Optional
import statistics
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class AggregateFunction:
    """Aggregate functions"""
    
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    STD = "std"
    VARIANCE = "variance"
    FIRST = "first"
    LAST = "last"
    UNIQUE = "unique"
    CONCAT = "concat"


class Aggregator:
    """
    Aggregator for statistical operations
    Supports group by and multiple aggregations
    """
    
    @staticmethod
    def aggregate(
        data: List[Dict[str, Any]],
        aggregations: Dict[str, Dict[str, Any]],
        group_by: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Aggregate data with optional grouping
        
        Args:
            data: List of records
            aggregations: Aggregation specifications
                Example: {
                    "total_sales": {"column": "sales", "function": "sum"},
                    "avg_price": {"column": "price", "function": "avg"},
                    "count": {"function": "count"}
                }
            group_by: Column to group by
            
        Returns:
            Aggregated results
        """
        if not data:
            return []
        
        if group_by:
            return Aggregator._aggregate_grouped(data, aggregations, group_by)
        else:
            return [Aggregator._aggregate_single(data, aggregations)]
    
    @staticmethod
    def _aggregate_grouped(
        data: List[Dict[str, Any]],
        aggregations: Dict[str, Dict[str, Any]],
        group_by: str
    ) -> List[Dict[str, Any]]:
        """Aggregate with grouping"""
        
        # Group data
        groups = defaultdict(list)
        for record in data:
            key = record.get(group_by)
            groups[key].append(record)
        
        # Aggregate each group
        results = []
        
        for group_key, group_records in groups.items():
            result = {group_by: group_key}
            
            # Apply aggregations
            for agg_name, agg_spec in aggregations.items():
                value = Aggregator._apply_aggregation(group_records, agg_spec)
                result[agg_name] = value
            
            results.append(result)
        
        logger.debug(f"Aggregated into {len(results)} groups")
        
        return results
    
    @staticmethod
    def _aggregate_single(
        data: List[Dict[str, Any]],
        aggregations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate without grouping"""
        
        result = {}
        
        for agg_name, agg_spec in aggregations.items():
            value = Aggregator._apply_aggregation(data, agg_spec)
            result[agg_name] = value
        
        return result
    
    @staticmethod
    def _apply_aggregation(
        records: List[Dict[str, Any]],
        spec: Dict[str, Any]
    ) -> Any:
        """Apply single aggregation"""
        
        function = spec.get('function')
        column = spec.get('column')
        
        # Extract values
        if column:
            values = [r.get(column) for r in records if r.get(column) is not None]
        else:
            values = records
        
        # Apply function
        if function == AggregateFunction.COUNT:
            return len(values)
        
        elif function == AggregateFunction.SUM:
            return sum(values) if values else 0
        
        elif function in [AggregateFunction.AVG, AggregateFunction.MEAN]:
            return statistics.mean(values) if values else 0
        
        elif function == AggregateFunction.MEDIAN:
            return statistics.median(values) if values else 0
        
        elif function == AggregateFunction.MIN:
            return min(values) if values else None
        
        elif function == AggregateFunction.MAX:
            return max(values) if values else None
        
        elif function == AggregateFunction.STD:
            return statistics.stdev(values) if len(values) > 1 else 0
        
        elif function == AggregateFunction.VARIANCE:
            return statistics.variance(values) if len(values) > 1 else 0
        
        elif function == AggregateFunction.FIRST:
            return values[0] if values else None
        
        elif function == AggregateFunction.LAST:
            return values[-1] if values else None
        
        elif function == AggregateFunction.UNIQUE:
            return len(set(values)) if values else 0
        
        elif function == AggregateFunction.CONCAT:
            separator = spec.get('separator', ', ')
            return separator.join(str(v) for v in values)
        
        return None
    
    @staticmethod
    def group_by(
        data: List[Dict[str, Any]],
        column: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """
        Group data by column
        
        Args:
            data: List of records
            column: Column to group by
            
        Returns:
            Dictionary of grouped records
        """
        groups = defaultdict(list)
        
        for record in data:
            key = record.get(column)
            groups[key].append(record)
        
        return dict(groups)
