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
    EXCEL = "excel"
    HTML = "html"
    PDF = "pdf"
    FILE = "file"
    UNKNOWN = "unknown"


class URLDetection(BaseModel):
    """Result of URL detection analysis"""
    
    is_redirect: bool = Field(
        description="True if content redirects to another URL for the actual task"
    )
    
    question_url: Optional[str] = Field(
        default=None,
        description="The URL to visit for the actual task (if is_redirect is True)"
    )
    
    reasoning: str = Field(
        description="Detailed explanation of why this is or isn't a redirect"
    )
    
    url_types: Dict[str, str] = Field(
        default_factory=dict,
        description="Classification of each URL found (e.g., 'question_url', 'data_url', 'submission_url')"
    )
    
    confidence: str = Field(
        default="medium",
        description="Confidence level: low, medium, high"
    )


class InstructionStep(BaseModel):
    """Single instruction step"""
    
    step_number: int = Field(
        description="Step number in sequence (1, 2, 3...)"
    )
    
    action: str = Field(
        description="Primary action: scrape, extract, calculate, submit, download, transcribe, analyze, visit"
    )
    
    description: str = Field(
        description="Clear description of what to do in this step"
    )
    
    target: Optional[str] = Field(
        default=None,
        description="Target of the action (URL, field name, file, etc.)"
    )
    
    dependencies: List[int] = Field(
        default_factory=list,
        description="Step numbers this step depends on"
    )


class UnifiedTaskAnalysis(BaseModel):
    """
    Unified analysis for task fetching
    Combines redirect detection, submission URL extraction, and instruction parsing
    """
    
    # ========================================================================
    # REDIRECT DETECTION
    # ========================================================================
    is_redirect: bool = Field(
        description="True if this content redirects to another URL for the actual task"
    )
    
    question_url: Optional[str] = Field(
        default=None,
        description="URL to visit for the actual task (if is_redirect=True)"
    )
    
    redirect_reasoning: str = Field(
        default="",
        description="Why this is or isn't a redirect"
    )
    
    # ========================================================================
    # SUBMISSION URL EXTRACTION
    # ========================================================================
    submission_url: Optional[str] = Field(
        default=None,
        description="URL where the final answer should be POSTed"
    )
    
    submission_url_is_relative: bool = Field(
        default=False,
        description="True if submission URL is relative and needs base URL resolution"
    )
    
    submission_reasoning: str = Field(
        default="",
        description="How the submission URL was identified"
    )
    
    # ========================================================================
    # INSTRUCTION PARSING
    # ========================================================================
    instructions: List[InstructionStep] = Field(
        default_factory=list,
        description="Parsed step-by-step instructions (empty if redirect)"
    )
    
    overall_goal: str = Field(
        description="High-level summary of what needs to be accomplished"
    )
    
    complexity: str = Field(
        description="Task complexity: trivial, simple, moderate, complex"
    )
    
    # ========================================================================
    # CONFIDENCE
    # ========================================================================
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall confidence (0.0-1.0)"
    )
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
