"""
Data Transformer
Main transformation module with filtering, sorting, aggregation, etc.
"""

from typing import List, Dict, Any, Optional
import time

from app.modules.processors.base_processor import BaseProcessor, ProcessingResult
from app.modules.processors.filter_engine import FilterEngine
from app.modules.processors.aggregator import Aggregator
from app.modules.processors.join_operations import JoinOperations
from app.modules.processors.pivot_operations import PivotOperations
from app.modules.processors.transform_utils import (
    sort_data,
    select_columns,
    rename_columns,
    add_column,
    limit_data,
    sample_data,
    distinct
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import ProcessingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataTransformer(BaseProcessor):
    """
    Data transformation module
    Filter, sort, aggregate, join, pivot, and reshape data
    """
    
    def __init__(self):
        super().__init__(name="data_transformer")
        logger.debug("DataTransformer initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return ProcessingCapability.TRANSFORM
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute data transformation
        
        Args:
            parameters: Transformation parameters
                - data: Data to transform (required)
                - operations: List of operations to apply
                Example: {
                    "data": [...],
                    "operations": [
                        {"type": "filter", "conditions": {...}},
                        {"type": "sort", "columns": ["price"], "ascending": False},
                        {"type": "limit", "limit": 10}
                    ]
                }
            context: Execution context
            
        Returns:
            ModuleResult: Transformation result
        """
        data = parameters.get('data')
        
        if not data:
            return ModuleResult(
                success=False,
                error="Data parameter is required"
            )
        
        logger.info("[DATA TRANSFORMER] Starting transformation")
        
        start_time = time.time()
        
        # Apply operations
        operations = parameters.get('operations', [])
        
        result = await self.process(
            data=data,
            options={'operations': operations}
        )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data=result.data,
                metadata={
                    'rows_processed': result.rows_processed,
                    'rows_output': len(result.data) if isinstance(result.data, list) else 1,
                    'operations_applied': len(operations),
                    'changes_made': result.changes_made
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )
    
    async def process(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process data with transformations
        
        Args:
            data: Data to transform
            options: Processing options with operations
            
        Returns:
            ProcessingResult: Processing result
        """
        options = options or {}
        operations = options.get('operations', [])
        
        # Convert single record to list
        single_record = False
        if isinstance(data, dict):
            data = [data]
            single_record = True
        
        if not isinstance(data, list):
            return ProcessingResult(
                success=False,
                error="Data must be a list of records or a single record"
            )
        
        logger.info(f"Transforming {len(data)} records with {len(operations)} operations")
        
        original_count = len(data)
        changes_made = []
        
        # Apply operations in sequence
        for i, operation in enumerate(operations, 1):
            op_type = operation.get('type')
            logger.debug(f"Operation {i}/{len(operations)}: {op_type}")
            
            try:
                data, change = await self._apply_operation(data, operation)
                if change:
                    changes_made.append(change)
            except Exception as e:
                logger.error(f"Operation {op_type} failed: {e}")
                return ProcessingResult(
                    success=False,
                    error=f"Operation {op_type} failed: {str(e)}"
                )
        
        # Convert back to single record if needed
        if single_record and data:
            data = data[0]
        
        logger.info(f"✓ Transformed data | Output: {len(data) if isinstance(data, list) else 1} records")
        
        return ProcessingResult(
            success=True,
            data=data,
            rows_processed=original_count,
            rows_cleaned=len(data) if isinstance(data, list) else 1,
            changes_made=changes_made
        )
    
    async def _apply_operation(
        self,
        data: List[Dict[str, Any]],
        operation: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Apply single operation"""
        
        op_type = operation.get('type')
        
        if op_type == 'filter':
            conditions = operation.get('conditions', {})
            match_all = operation.get('match_all', True)
            before = len(data)
            data = FilterEngine.filter(data, conditions, match_all)
            after = len(data)
            return data, f"Filtered: {before} → {after} records"
        
        elif op_type == 'sort':
            columns = operation.get('columns', [])
            if isinstance(columns, str):
                columns = [columns]
            ascending = operation.get('ascending', True)
            data = sort_data(data, columns, ascending)
            return data, f"Sorted by {', '.join(columns)}"
        
        elif op_type == 'aggregate':
            aggregations = operation.get('aggregations', {})
            group_by = operation.get('group_by')
            data = Aggregator.aggregate(data, aggregations, group_by)
            return data, f"Aggregated with {len(aggregations)} functions"
        
        elif op_type == 'group_by':
            column = operation.get('column')
            grouped = Aggregator.group_by(data, column)
            # Return as list of dicts
            result = [
                {'group': key, 'records': records}
                for key, records in grouped.items()
            ]
            return result, f"Grouped by {column}"
        
        elif op_type == 'select':
            columns = operation.get('columns', [])
            data = select_columns(data, columns)
            return data, f"Selected {len(columns)} columns"
        
        elif op_type == 'rename':
            mapping = operation.get('mapping', {})
            data = rename_columns(data, mapping)
            return data, f"Renamed {len(mapping)} columns"
        
        elif op_type == 'add_column':
            column = operation.get('column')
            value = operation.get('value')
            function = operation.get('function')
            data = add_column(data, column, value, function)
            return data, f"Added column: {column}"
        
        elif op_type == 'limit':
            limit = operation.get('limit', 10)
            offset = operation.get('offset', 0)
            data = limit_data(data, limit, offset)
            return data, f"Limited to {limit} records"
        
        elif op_type == 'sample':
            n = operation.get('n', 10)
            random_state = operation.get('random_state')
            data = sample_data(data, n, random_state)
            return data, f"Sampled {n} records"
        
        elif op_type == 'distinct':
            columns = operation.get('columns')
            before = len(data)
            data = distinct(data, columns)
            after = len(data)
            return data, f"Distinct: {before} → {after} records"
        
        elif op_type == 'join':
            right_data = operation.get('right_data', [])
            left_key = operation.get('left_key')
            right_key = operation.get('right_key')
            join_type = operation.get('join_type', 'inner')
            data = JoinOperations.join(data, right_data, left_key, right_key, join_type)
            return data, f"Joined {len(right_data)} records ({join_type})"
        
        elif op_type == 'pivot':
            index = operation.get('index')
            columns = operation.get('columns')
            values = operation.get('values')
            aggfunc = operation.get('aggfunc', 'sum')
            data = PivotOperations.pivot(data, index, columns, values, aggfunc)
            return data, f"Pivoted data"
        
        elif op_type == 'unpivot':
            id_vars = operation.get('id_vars', [])
            value_vars = operation.get('value_vars')
            var_name = operation.get('var_name', 'variable')
            value_name = operation.get('value_name', 'value')
            data = PivotOperations.unpivot(data, id_vars, value_vars, var_name, value_name)
            return data, f"Unpivoted data"
        
        else:
            logger.warning(f"Unknown operation type: {op_type}")
            return data, None
