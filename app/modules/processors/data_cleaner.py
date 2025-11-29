"""
Data Cleaner
Main data cleaning implementation
"""

from typing import Dict, Any, List, Optional
import time

from app.modules.processors.base_processor import BaseProcessor, ProcessingResult
from app.modules.processors.cleaning_strategies import (
    CleaningStrategy,
    DEFAULT_STRATEGY,
    MissingValueStrategy,
    DuplicateStrategy,
    OutlierStrategy,
    TextCleaningStrategy
)
from app.modules.processors.type_converters import (
    to_number,
    to_boolean,
    to_date,
    parse_special_value,
    clean_text
)
from app.modules.processors.validators import (
    is_valid_email,
    is_valid_url,
    detect_outlier_zscore,
    detect_outlier_iqr
)
from app.modules.processors.cleaning_utils import (
    remove_duplicates,
    calculate_statistics,
    get_mode,
    is_missing
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import ProcessingCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class DataCleaner(BaseProcessor):
    """
    Data cleaning module
    Handles missing values, duplicates, type conversion, validation
    """
    
    def __init__(self, strategy: Optional[CleaningStrategy] = None):
        super().__init__(name="data_cleaner")
        self.strategy = strategy or DEFAULT_STRATEGY
        logger.debug("DataCleaner initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return ProcessingCapability.TRANSFORM
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute data cleaning
        
        Args:
            parameters: Cleaning parameters
                - data: Data to clean (required)
                - strategy: Cleaning strategy (optional)
                - columns: Specific columns to clean (optional)
                - type_conversions: Column type conversions (optional)
            context: Execution context
            
        Returns:
            ModuleResult: Cleaning result
        """
        data = parameters.get('data')
        
        if not data:
            return ModuleResult(
                success=False,
                error="Data parameter is required"
            )
        
        logger.info("[DATA CLEANER] Starting data cleaning")
        
        start_time = time.time()
        
        # Use custom strategy if provided
        if 'strategy' in parameters:
            strategy = parameters['strategy']
            if isinstance(strategy, dict):
                strategy = CleaningStrategy(**strategy)
        else:
            strategy = self.strategy
        
        # Clean data
        result = await self.process(
            data=data,
            options={
                'strategy': strategy,
                'columns': parameters.get('columns'),
                'type_conversions': parameters.get('type_conversions', {})
            }
        )
        
        execution_time = time.time() - start_time
        
        if result.success:
            return ModuleResult(
                success=True,
                data=result.data,
                metadata={
                    'rows_processed': result.rows_processed,
                    'rows_cleaned': result.rows_cleaned,
                    'rows_removed': result.rows_removed,
                    'rows_modified': result.rows_modified,
                    'changes_made': result.changes_made,
                    'warnings': result.warnings
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
        Process and clean data
        
        Args:
            data: Data to clean (list of dicts or dict)
            options: Processing options
            
        Returns:
            ProcessingResult: Processing result
        """
        options = options or {}
        strategy = options.get('strategy', self.strategy)
        
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
        
        if not data:
            return ProcessingResult(
                success=True,
                data=[],
                rows_processed=0
            )
        
        logger.info(f"Cleaning {len(data)} records")
        
        original_count = len(data)
        changes_made = []
        warnings = []
        
        # Step 1: Clean text fields FIRST (so duplicates can be detected properly)
        data = self._clean_text_fields(data, strategy)
        
        # Step 2: Handle duplicates (after text cleaning)
        if strategy.duplicates != DuplicateStrategy.KEEP_ALL:
            before = len(data)
            data = remove_duplicates(data, strategy=strategy.duplicates.value)
            after = len(data)
            
            if before != after:
                removed = before - after
                changes_made.append(f"Removed {removed} duplicate records")
                logger.info(f"Removed {removed} duplicates")
        
        # Step 3: Type conversions
        type_conversions = options.get('type_conversions', {})
        if type_conversions:
            data = self._convert_types(data, type_conversions)
            changes_made.append(f"Converted types for {len(type_conversions)} columns")
        
        # Step 4: Handle missing values
        data, missing_changes = self._handle_missing_values(data, strategy)
        if missing_changes:
            changes_made.extend(missing_changes)
        
        # Step 5: Handle outliers
        data, outlier_changes = self._handle_outliers(data, strategy)
        if outlier_changes:
            changes_made.extend(outlier_changes)
        
        # Step 6: Validate data
        validation_warnings = self._validate_data(data)
        warnings.extend(validation_warnings)
        
        # Calculate statistics
        rows_removed = original_count - len(data)
        rows_cleaned = len(data)
        rows_modified = rows_cleaned  # Assume all cleaned rows were modified
        
        # Convert back to single record if needed
        if single_record and data:
            data = data[0]
        
        logger.info(f"✓ Cleaned {rows_cleaned} records | Removed: {rows_removed}")
        
        return ProcessingResult(
            success=True,
            data=data,
            rows_processed=original_count,
            rows_cleaned=rows_cleaned,
            rows_removed=rows_removed,
            rows_modified=rows_modified,
            changes_made=changes_made,
            warnings=warnings
        )

    def _convert_types(
        self,
        data: List[Dict[str, Any]],
        conversions: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Convert column types
        
        Args:
            data: Data records
            conversions: Column -> type mappings
            
        Returns:
            Data with converted types
        """
        for record in data:
            for column, target_type in conversions.items():
                if column not in record:
                    continue
                
                value = record[column]
                
                if target_type == 'number':
                    record[column] = to_number(value)
                
                elif target_type == 'boolean':
                    record[column] = to_boolean(value)
                
                elif target_type == 'date':
                    record[column] = to_date(value)
                
                elif target_type == 'string':
                    record[column] = str(value) if value is not None else None
        
        return data
    
    def _clean_text_fields(
        self,
        data: List[Dict[str, Any]],
        strategy: CleaningStrategy
    ) -> List[Dict[str, Any]]:
        """Clean text fields"""
        
        for record in data:
            for key, value in record.items():
                if isinstance(value, str):
                    # Parse special values (N/A, null, etc.)
                    parsed = parse_special_value(value)
                    
                    if parsed is None:
                        record[key] = None
                    else:
                        # Clean text
                        record[key] = clean_text(value, strategy.text_cleaning.value)
        
        return data
    
    def _handle_missing_values(
        self,
        data: List[Dict[str, Any]],
        strategy: CleaningStrategy
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Handle missing values"""
        
        changes = []
        
        if strategy.missing_values == MissingValueStrategy.DROP:
            # Remove records with any missing values
            before = len(data)
            data = [r for r in data if not any(is_missing(v) for v in r.values())]
            after = len(data)
            
            if before != after:
                changes.append(f"Dropped {before - after} records with missing values")
        
        else:
            # Fill missing values
            # Calculate fill values per column
            fill_values = {}
            
            if strategy.missing_values in [
                MissingValueStrategy.FILL_MEAN,
                MissingValueStrategy.FILL_MEDIAN,
                MissingValueStrategy.FILL_MODE
            ]:
                # Get all columns
                if data:
                    columns = set()
                    for record in data:
                        columns.update(record.keys())
                    
                    for column in columns:
                        values = [r.get(column) for r in data if not is_missing(r.get(column))]
                        
                        if not values:
                            continue
                        
                        # Try numeric
                        numeric_values = [to_number(v) for v in values]
                        numeric_values = [v for v in numeric_values if v is not None]
                        
                        if numeric_values:
                            if strategy.missing_values == MissingValueStrategy.FILL_MEAN:
                                stats = calculate_statistics(numeric_values)
                                fill_values[column] = stats['mean']
                            
                            elif strategy.missing_values == MissingValueStrategy.FILL_MEDIAN:
                                stats = calculate_statistics(numeric_values)
                                fill_values[column] = stats['median']
                        
                        # Mode works for any type
                        if strategy.missing_values == MissingValueStrategy.FILL_MODE:
                            fill_values[column] = get_mode(values)
            
            # Apply fill values
            filled_count = 0
            
            for record in data:
                for key, value in record.items():
                    if is_missing(value):
                        if strategy.missing_values == MissingValueStrategy.FILL_ZERO:
                            record[key] = 0
                            filled_count += 1
                        
                        elif strategy.missing_values == MissingValueStrategy.FILL_CUSTOM:
                            record[key] = strategy.fill_value
                            filled_count += 1
                        
                        elif key in fill_values:
                            record[key] = fill_values[key]
                            filled_count += 1
            
            if filled_count > 0:
                changes.append(f"Filled {filled_count} missing values")
        
        return data, changes
    
    def _handle_outliers(
        self,
        data: List[Dict[str, Any]],
        strategy: CleaningStrategy
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Handle outliers"""
        
        changes = []
        
        if strategy.outliers == OutlierStrategy.KEEP:
            return data, changes
        
        if not data:
            return data, changes
        
        # Find numeric columns
        columns = set()
        for record in data:
            columns.update(record.keys())
        
        for column in columns:
            values = [r.get(column) for r in data]
            numeric_values = [to_number(v) for v in values if v is not None]
            numeric_values = [v for v in numeric_values if v is not None]
            
            if len(numeric_values) < 4:
                continue
            
            # Calculate statistics
            stats = calculate_statistics(numeric_values)
            
            # Detect outliers
            outlier_indices = set()
            
            for i, record in enumerate(data):
                value = to_number(record.get(column))
                
                if value is None:
                    continue
                
                is_outlier = detect_outlier_zscore(
                    value,
                    stats['mean'],
                    stats['std'],
                    strategy.outlier_threshold
                )
                
                if is_outlier:
                    outlier_indices.add(i)
                    
                    if strategy.outliers == OutlierStrategy.CAP:
                        # Cap at mean +/- threshold * std
                        if value > stats['mean']:
                            record[column] = stats['mean'] + strategy.outlier_threshold * stats['std']
                        else:
                            record[column] = stats['mean'] - strategy.outlier_threshold * stats['std']
                    
                    elif strategy.outliers == OutlierStrategy.REPLACE_MEAN:
                        record[column] = stats['mean']
                    
                    elif strategy.outliers == OutlierStrategy.REPLACE_MEDIAN:
                        record[column] = stats['median']
            
            if outlier_indices:
                if strategy.outliers == OutlierStrategy.REMOVE:
                    data = [r for i, r in enumerate(data) if i not in outlier_indices]
                    changes.append(f"Removed {len(outlier_indices)} outliers from {column}")
                else:
                    changes.append(f"Adjusted {len(outlier_indices)} outliers in {column}")
        
        return data, changes
    
    def _validate_data(self, data: List[Dict[str, Any]]) -> List[str]:
        """Validate data quality"""
        
        warnings = []
        
        for i, record in enumerate(data):
            for key, value in record.items():
                if value is None or value == "":
                    continue
                
                # Email validation
                if 'email' in key.lower():
                    if not is_valid_email(value):
                        warnings.append(f"Row {i}: Invalid email in {key}: {value}")
                
                # URL validation
                if 'url' in key.lower() or 'link' in key.lower():
                    if not is_valid_url(value):
                        warnings.append(f"Row {i}: Invalid URL in {key}: {value}")
        
        return warnings
