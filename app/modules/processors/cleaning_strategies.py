"""
Cleaning Strategies
Different strategies for handling data quality issues
"""

from enum import Enum
from typing import Any, Optional


class MissingValueStrategy(str, Enum):
    """Strategies for handling missing values"""
    DROP = "drop"              # Remove rows with missing values
    FILL_ZERO = "fill_zero"    # Fill with 0
    FILL_MEAN = "fill_mean"    # Fill with mean (numeric)
    FILL_MEDIAN = "fill_median"  # Fill with median (numeric)
    FILL_MODE = "fill_mode"    # Fill with mode (most common)
    FILL_FORWARD = "fill_forward"  # Forward fill
    FILL_BACKWARD = "fill_backward"  # Backward fill
    FILL_CUSTOM = "fill_custom"  # Fill with custom value


class DuplicateStrategy(str, Enum):
    """Strategies for handling duplicates"""
    DROP_FIRST = "drop_first"    # Keep last occurrence
    DROP_LAST = "drop_last"      # Keep first occurrence
    DROP_ALL = "drop_all"        # Remove all duplicates
    KEEP_ALL = "keep_all"        # Keep all (no deduplication)


class OutlierStrategy(str, Enum):
    """Strategies for handling outliers"""
    REMOVE = "remove"            # Remove outliers
    CAP = "cap"                  # Cap at threshold
    KEEP = "keep"                # Keep outliers
    REPLACE_MEAN = "replace_mean"  # Replace with mean
    REPLACE_MEDIAN = "replace_median"  # Replace with median


class TextCleaningStrategy(str, Enum):
    """Text cleaning strategies"""
    TRIM = "trim"                # Remove whitespace
    LOWERCASE = "lowercase"      # Convert to lowercase
    UPPERCASE = "uppercase"      # Convert to uppercase
    TITLE_CASE = "title_case"    # Title Case
    REMOVE_SPECIAL = "remove_special"  # Remove special characters
    NORMALIZE = "normalize"      # Normalize (trim + lowercase)


class CleaningStrategy:
    """Combined cleaning strategy configuration"""
    
    def __init__(
        self,
        missing_values: MissingValueStrategy = MissingValueStrategy.DROP,
        duplicates: DuplicateStrategy = DuplicateStrategy.DROP_FIRST,
        outliers: OutlierStrategy = OutlierStrategy.KEEP,
        text_cleaning: TextCleaningStrategy = TextCleaningStrategy.TRIM,
        fill_value: Optional[Any] = None,
        outlier_threshold: float = 3.0  # Z-score threshold
    ):
        self.missing_values = missing_values
        self.duplicates = duplicates
        self.outliers = outliers
        self.text_cleaning = text_cleaning
        self.fill_value = fill_value
        self.outlier_threshold = outlier_threshold


# Default strategies
DEFAULT_STRATEGY = CleaningStrategy()

AGGRESSIVE_CLEANING = CleaningStrategy(
    missing_values=MissingValueStrategy.DROP,
    duplicates=DuplicateStrategy.DROP_ALL,
    outliers=OutlierStrategy.REMOVE,
    text_cleaning=TextCleaningStrategy.NORMALIZE
)

GENTLE_CLEANING = CleaningStrategy(
    missing_values=MissingValueStrategy.FILL_MEAN,
    duplicates=DuplicateStrategy.DROP_FIRST,
    outliers=OutlierStrategy.KEEP,
    text_cleaning=TextCleaningStrategy.TRIM
)
