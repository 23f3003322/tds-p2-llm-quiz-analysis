"""
Parameter Models
Pydantic models for structured parameter extraction
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, HttpUrl


class URLParameter(BaseModel):
    """URL parameter with metadata"""
    url: str
    purpose: str = Field(description="What this URL is for")
    requires_javascript: bool = False
    requires_authentication: bool = False


class DataSource(BaseModel):
    """Data source specification"""
    type: Literal['url', 'file', 'api', 'database', 'local'] = Field(
        description="Type of data source"
    )
    location: str = Field(description="URL, file path, or identifier")
    format: Optional[str] = Field(None, description="Data format (csv, json, xml, etc)")
    description: str = Field(description="What data this contains")


class FilterCondition(BaseModel):
    """Filter or condition to apply to data"""
    field: str = Field(description="Field/column to filter on")
    operator: Literal['equals', 'not_equals', 'greater_than', 'less_than', 
                      'contains', 'not_contains', 'in', 'not_in', 
                      'between', 'starts_with', 'ends_with'] = Field(
        description="Comparison operator"
    )
    value: Any = Field(description="Value to compare against")
    description: str = Field(description="Human-readable filter description")


class ColumnSelection(BaseModel):
    """Column or field selection"""
    name: str = Field(description="Column/field name")
    alias: Optional[str] = Field(None, description="Alternative name or alias")
    required: bool = Field(True, description="Is this column required")
    description: str = Field(description="What this column contains")


class TimeRange(BaseModel):
    """Time range specification"""
    start: Optional[str] = Field(None, description="Start date/time")
    end: Optional[str] = Field(None, description="End date/time")
    relative: Optional[str] = Field(None, description="Relative time (e.g., 'last 7 days')")
    field: str = Field(description="Date/time field to filter on")
    description: str = Field(description="Human-readable time range")


class NumericalConstraint(BaseModel):
    """Numerical constraint or limit"""
    type: Literal['limit', 'offset', 'top_n', 'bottom_n', 'threshold', 'range'] = Field(
        description="Type of numerical constraint"
    )
    value: float = Field(description="Numerical value")
    field: Optional[str] = Field(None, description="Field this applies to")
    description: str = Field(description="What this constraint does")


class GeographicFilter(BaseModel):
    """Geographic/location filter"""
    type: Literal['country', 'region', 'city', 'coordinates', 'radius'] = Field(
        description="Type of geographic filter"
    )
    value: str = Field(description="Location value")
    field: str = Field(description="Location field name")
    description: str = Field(description="Geographic constraint")


class AggregationSpec(BaseModel):
    """Aggregation specification"""
    function: Literal['sum', 'avg', 'count', 'min', 'max', 'median', 'std', 'variance'] = Field(
        description="Aggregation function"
    )
    field: str = Field(description="Field to aggregate")
    group_by: Optional[List[str]] = Field(None, description="Fields to group by")
    description: str = Field(description="What this aggregation computes")


class SortingSpec(BaseModel):
    """Sorting specification"""
    field: str = Field(description="Field to sort by")
    order: Literal['ascending', 'descending'] = Field(description="Sort order")
    description: str = Field(description="Sort description")


class VisualizationRequirement(BaseModel):
    """Visualization requirements"""
    type: Literal['chart', 'graph', 'map', 'table', 'dashboard', 'plot'] = Field(
        description="Type of visualization"
    )
    chart_type: Optional[Literal['bar', 'line', 'pie', 'scatter', 'heatmap', 
                                  'histogram', 'box', 'area']] = Field(
        None, description="Specific chart type"
    )
    x_axis: Optional[str] = Field(None, description="X-axis field")
    y_axis: Optional[str] = Field(None, description="Y-axis field")
    title: Optional[str] = Field(None, description="Visualization title")
    description: str = Field(description="What should be visualized")


class OutputRequirement(BaseModel):
    """Output format and requirements"""
    format: Literal['csv', 'json', 'excel', 'pdf', 'image', 'html', 'text'] = Field(
        description="Output format"
    )
    filename: Optional[str] = Field(None, description="Suggested filename")
    includes_visualization: bool = Field(False, description="Should include charts/graphs")
    description: str = Field(description="Output requirements")


class ExtractedParameters(BaseModel):
    """
    Complete set of extracted parameters from task description
    Main output model for parameter extraction
    """
    
    # Data sources
    data_sources: List[DataSource] = Field(
        default_factory=list,
        description="All data sources identified"
    )
    
    # URLs
    urls: List[URLParameter] = Field(
        default_factory=list,
        description="All URLs mentioned in task"
    )
    
    # Filters and conditions
    filters: List[FilterCondition] = Field(
        default_factory=list,
        description="Filter conditions to apply"
    )
    
    # Column selections
    columns: List[ColumnSelection] = Field(
        default_factory=list,
        description="Columns or fields to extract/use"
    )
    
    # Time ranges
    time_ranges: List[TimeRange] = Field(
        default_factory=list,
        description="Time range filters"
    )
    
    # Numerical constraints
    numerical_constraints: List[NumericalConstraint] = Field(
        default_factory=list,
        description="Numerical limits and thresholds"
    )
    
    # Geographic filters
    geographic_filters: List[GeographicFilter] = Field(
        default_factory=list,
        description="Geographic location filters"
    )
    
    # Aggregations
    aggregations: List[AggregationSpec] = Field(
        default_factory=list,
        description="Aggregation operations"
    )
    
    # Sorting
    sorting: List[SortingSpec] = Field(
        default_factory=list,
        description="Sorting specifications"
    )
    
    # Visualizations
    visualizations: List[VisualizationRequirement] = Field(
        default_factory=list,
        description="Visualization requirements"
    )
    
    # Output
    output: Optional[OutputRequirement] = Field(
        None,
        description="Output format requirements"
    )
    
    # Additional metadata
    requires_api_keys: List[str] = Field(
        default_factory=list,
        description="API keys or credentials needed"
    )
    
    complexity_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Estimated complexity (0-1)"
    )
    
    estimated_execution_time: int = Field(
        60,
        description="Estimated execution time in seconds"
    )
    
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in parameter extraction"
    )
    
    notes: List[str] = Field(
        default_factory=list,
        description="Additional notes or warnings"
    )


class ParameterExtractionResult(BaseModel):
    """
    Result wrapper for parameter extraction
    """
    parameters: ExtractedParameters
    raw_task: str = Field(description="Original task description")
    extraction_method: Literal['llm', 'rule_based', 'hybrid'] = Field(
        description="Method used for extraction"
    )
    success: bool = Field(description="Whether extraction was successful")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
