"""
Pydantic Models for Orchestrator
Structured outputs for task classification and planning
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Enumeration of possible task types"""
    WEB_SCRAPING = "web_scraping"
    API_CALL = "api_call"
    DATA_CLEANING = "data_cleaning"
    DATA_TRANSFORMATION = "data_transformation"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    ML_ANALYSIS = "ml_analysis"
    TEXT_PROCESSING = "text_processing"
    IMAGE_PROCESSING = "image_processing"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_PROCESSING = "video_processing"
    GEOSPATIAL_ANALYSIS = "geospatial_analysis"
    NETWORK_ANALYSIS = "network_analysis"
    VISUALIZATION = "visualization"
    FILE_PROCESSING = "file_processing"
    UNKNOWN = "unknown"


class ComplexityLevel(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class OutputFormat(str, Enum):
    """Expected output formats"""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"
    IMAGE = "image"
    CHART = "chart"
    HTML = "html"
    PDF = "pdf"
    UNKNOWN = "unknown"


class TaskClassification(BaseModel):
    """
    Structured output for task classification
    Used by Pydantic AI for automatic validation
    """
    primary_task: TaskType = Field(
        description="Main task type that best describes this task"
    )
    
    secondary_tasks: List[TaskType] = Field(
        default_factory=list,
        description="Additional task types involved in completing this task"
    )
    
    complexity: ComplexityLevel = Field(
        description="Estimated complexity level of the task"
    )
    
    estimated_steps: int = Field(
        ge=1,
        le=20,
        description="Estimated number of steps required (1-20)"
    )
    
    requires_javascript: bool = Field(
        default=False,
        description="Whether JavaScript rendering is needed for web scraping"
    )
    
    requires_authentication: bool = Field(
        default=False,
        description="Whether authentication/API keys are needed"
    )
    
    requires_external_data: bool = Field(
        default=False,
        description="Whether external data sources need to be accessed"
    )
    
    output_format: OutputFormat = Field(
        description="Expected output format"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in this classification (0.0-1.0)"
    )
    
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Brief explanation of the classification decision"
    )
    
    key_entities: List[str] = Field(
        default_factory=list,
        description="Key entities mentioned (URLs, APIs, datasets, etc.)"
    )
    
    suggested_tools: List[str] = Field(
        default_factory=list,
        description="Suggested tools/libraries for this task"
    )


class ContentAnalysis(BaseModel):
    """
    Structured output for content analysis
    Determines if fetched content is the task or requires further action
    """
    content_type: str = Field(
        description="Type: 'direct_task' or 'requires_action'"
    )
    
    is_direct_task: bool = Field(
        description="True if content is ready-to-use task description"
    )
    
    task_description: Optional[str] = Field(
        None,
        description="Extracted task if direct_task, None otherwise"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in analysis (0.0-1.0)"
    )
    
    requires_download: bool = Field(
        default=False,
        description="Whether files need to be downloaded"
    )
    
    requires_transcription: bool = Field(
        default=False,
        description="Whether audio/video needs transcription"
    )
    
    requires_ocr: bool = Field(
        default=False,
        description="Whether images need OCR"
    )
    
    requires_navigation: bool = Field(
        default=False,
        description="Whether additional pages need to be visited"
    )
    
    action_urls: List[str] = Field(
        default_factory=list,
        description="URLs that need to be processed"
    )
    
    reasoning: str = Field(
        min_length=10,
        description="Explanation of the analysis"
    )
