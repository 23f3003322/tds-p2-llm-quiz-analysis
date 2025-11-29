"""
Pivot Operations
Pivot and reshape data
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.core.logging import get_logger

logger = get_logger(__name__)


class PivotOperations:
    """Pivot and reshape operations"""
    
    @staticmethod
    def pivot(
        data: List[Dict[str, Any]],
        index: str,
        columns: str,
        values: str,
        aggfunc: str = "sum"
    ) -> List[Dict[str, Any]]:
        """
        Pivot data (wide format)
        
        Args:
            data: List of records
            index: Column to use as index (row labels)
            columns: Column to use as columns (column labels)
            values: Column to aggregate
            aggfunc: Aggregation function
            
        Returns:
            Pivoted data
        """
        # Group by index and columns
        pivot_dict = defaultdict(lambda: defaultdict(list))
        
        for record in data:
            row_key = record.get(index)
            col_key = record.get(columns)
            value = record.get(values)
            
            if value is not None:
                pivot_dict[row_key][col_key].append(value)
        
        # Aggregate and build result
        result = []
        
        for row_key, cols in pivot_dict.items():
            row = {index: row_key}
            
            for col_key, vals in cols.items():
                if aggfunc == "sum":
                    row[col_key] = sum(vals)
                elif aggfunc == "avg":
                    row[col_key] = sum(vals) / len(vals)
                elif aggfunc == "count":
                    row[col_key] = len(vals)
                elif aggfunc == "min":
                    row[col_key] = min(vals)
                elif aggfunc == "max":
                    row[col_key] = max(vals)
                elif aggfunc == "first":
                    row[col_key] = vals[0]
                elif aggfunc == "last":
                    row[col_key] = vals[-1]
            
            result.append(row)
        
        logger.debug(f"Pivoted {len(data)} records into {len(result)} rows")
        
        return result
    
    @staticmethod
    def unpivot(
        data: List[Dict[str, Any]],
        id_vars: List[str],
        value_vars: Optional[List[str]] = None,
        var_name: str = "variable",
        value_name: str = "value"
    ) -> List[Dict[str, Any]]:
        """
        Unpivot data (long format / melt)
        
        Args:
            data: List of records
            id_vars: Columns to keep as identifiers
            value_vars: Columns to unpivot (None = all others)
            var_name: Name for variable column
            value_name: Name for value column
            
        Returns:
            Unpivoted data
        """
        result = []
        
        for record in data:
            # Determine value columns
            if value_vars is None:
                value_vars = [k for k in record.keys() if k not in id_vars]
            
            # Create one row per value column
            for var in value_vars:
                if var in record:
                    row = {id_var: record[id_var] for id_var in id_vars if id_var in record}
                    row[var_name] = var
                    row[value_name] = record[var]
                    result.append(row)
        
        logger.debug(f"Unpivoted {len(data)} records into {len(result)} rows")
        
        return result
