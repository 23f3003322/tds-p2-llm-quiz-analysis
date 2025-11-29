"""
Join Operations
Join/merge multiple datasets
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class JoinType:
    """Join types"""
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"
    OUTER = "outer"


class JoinOperations:
    """Join operations for combining datasets"""
    
    @staticmethod
    def join(
        left_data: List[Dict[str, Any]],
        right_data: List[Dict[str, Any]],
        left_key: str,
        right_key: str,
        join_type: str = JoinType.INNER,
        suffix: tuple = ("_left", "_right")
    ) -> List[Dict[str, Any]]:
        """
        Join two datasets
        
        Args:
            left_data: Left dataset
            right_data: Right dataset
            left_key: Key column in left dataset
            right_key: Key column in right dataset
            join_type: Type of join (inner, left, right, outer)
            suffix: Suffix for duplicate column names
            
        Returns:
            Joined dataset
        """
        # Index right data by key
        right_index = defaultdict(list)
        for record in right_data:
            key = record.get(right_key)
            right_index[key].append(record)
        
        result = []
        matched_right_keys = set()
        
        # Process left data
        for left_record in left_data:
            left_key_value = left_record.get(left_key)
            right_matches = right_index.get(left_key_value, [])
            
            if right_matches:
                # Match found
                matched_right_keys.add(left_key_value)
                
                for right_record in right_matches:
                    merged = JoinOperations._merge_records(
                        left_record,
                        right_record,
                        suffix
                    )
                    result.append(merged)
            
            elif join_type in [JoinType.LEFT, JoinType.OUTER]:
                # No match, but include for left/outer join
                result.append(left_record.copy())
        
        # For right/outer join, add unmatched right records
        if join_type in [JoinType.RIGHT, JoinType.OUTER]:
            for right_record in right_data:
                key = right_record.get(right_key)
                if key not in matched_right_keys:
                    result.append(right_record.copy())
        
        logger.debug(f"Joined {len(left_data)} + {len(right_data)} = {len(result)} records")
        
        return result
    
    @staticmethod
    def _merge_records(
        left: Dict[str, Any],
        right: Dict[str, Any],
        suffix: tuple
    ) -> Dict[str, Any]:
        """Merge two records, handling duplicate keys"""
        
        merged = left.copy()
        
        for key, value in right.items():
            if key in merged and merged[key] != value:
                # Duplicate key with different value
                merged[f"{key}{suffix[1]}"] = value
                if f"{key}{suffix[0]}" not in merged:
                    merged[f"{key}{suffix[0]}"] = merged[key]
                    del merged[key]
            else:
                merged[key] = value
        
        return merged
