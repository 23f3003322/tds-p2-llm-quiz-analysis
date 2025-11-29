"""
Filter Engine
Advanced filtering with multiple operators and conditions
"""

from typing import List, Dict, Any
import re

from app.core.logging import get_logger

logger = get_logger(__name__)


class FilterOperator:
    """Filter operators"""
    
    EQ = "eq"              # Equal
    NE = "ne"              # Not equal
    GT = "gt"              # Greater than
    GTE = "gte"            # Greater than or equal
    LT = "lt"              # Less than
    LTE = "lte"            # Less than or equal
    IN = "in"              # In list
    NOT_IN = "not_in"      # Not in list
    CONTAINS = "contains"  # Contains substring
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"    # Between two values
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"        # Regular expression


class FilterEngine:
    """
    Filter engine for data records
    Supports complex filtering with multiple conditions
    """
    
    @staticmethod
    def filter(
        data: List[Dict[str, Any]],
        conditions: Dict[str, Any],
        match_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Filter data based on conditions
        
        Args:
            data: List of records
            conditions: Filter conditions
            match_all: True = AND logic, False = OR logic
            
        Returns:
            Filtered records
        """
        if not conditions:
            return data
        
        filtered = []
        
        for record in data:
            if match_all:
                if FilterEngine._matches_all(record, conditions):
                    filtered.append(record)
            else:
                if FilterEngine._matches_any(record, conditions):
                    filtered.append(record)
        
        logger.debug(f"Filtered {len(filtered)}/{len(data)} records")
        
        return filtered
    
    @staticmethod
    def _matches_all(record: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Check if record matches all conditions (AND)"""
        for field, condition in conditions.items():
            if not FilterEngine._matches_condition(record, field, condition):
                return False
        return True
    
    @staticmethod
    def _matches_any(record: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Check if record matches any condition (OR)"""
        for field, condition in conditions.items():
            if FilterEngine._matches_condition(record, field, condition):
                return True
        return False
    
    @staticmethod
    def _matches_condition(
        record: Dict[str, Any],
        field: str,
        condition: Any
    ) -> bool:
        """Check if record matches a single field condition"""
        value = record.get(field)
        
        # Simple equality check
        if not isinstance(condition, dict):
            return value == condition
        
        # Complex conditions with operators
        for operator, expected in condition.items():
            if not FilterEngine._apply_operator(value, operator, expected):
                return False
        
        return True
    
    @staticmethod
    def _apply_operator(value: Any, operator: str, expected: Any) -> bool:
        """Apply filter operator"""
        
        if operator == FilterOperator.EQ:
            return value == expected
        
        elif operator == FilterOperator.NE:
            return value != expected
        
        elif operator == FilterOperator.GT:
            return value is not None and value > expected
        
        elif operator == FilterOperator.GTE:
            return value is not None and value >= expected
        
        elif operator == FilterOperator.LT:
            return value is not None and value < expected
        
        elif operator == FilterOperator.LTE:
            return value is not None and value <= expected
        
        elif operator == FilterOperator.IN:
            return value in expected
        
        elif operator == FilterOperator.NOT_IN:
            return value not in expected
        
        elif operator == FilterOperator.CONTAINS:
            if value is None:
                return False
            return str(expected).lower() in str(value).lower()
        
        elif operator == FilterOperator.STARTS_WITH:
            if value is None:
                return False
            return str(value).startswith(str(expected))
        
        elif operator == FilterOperator.ENDS_WITH:
            if value is None:
                return False
            return str(value).endswith(str(expected))
        
        elif operator == FilterOperator.BETWEEN:
            if value is None:
                return False
            return expected[0] <= value <= expected[1]
        
        elif operator == FilterOperator.IS_NULL:
            return value is None
        
        elif operator == FilterOperator.IS_NOT_NULL:
            return value is not None
        
        elif operator == FilterOperator.REGEX:
            if value is None:
                return False
            return bool(re.search(expected, str(value)))
        
        return False
