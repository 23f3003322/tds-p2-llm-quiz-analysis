"""
Base Generator Interface
"""

from typing import Dict, Any, Optional
from abc import abstractmethod
from pydantic import BaseModel, Field
from enum import Enum

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class OutputFormat(str, Enum):
    """Output format types"""
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"


class ReportResult(BaseModel):
    """Result from report generation"""
    
    success: bool
    
    # Answer content
    answer: str = ""
    formatted_answer: Dict[str, str] = Field(default_factory=dict)
    
    # Components
    has_statistics: bool = False
    has_insights: bool = False
    has_chart: bool = False
    
    # Metadata
    format: OutputFormat = OutputFormat.TEXT
    word_count: int = 0
    
    # Error handling
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class BaseGenerator(BaseModule):
    """Base class for report generators"""
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.EXPORTER)
    
    @abstractmethod
    async def generate(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> ReportResult:
        """
        Generate report
        
        Args:
            data: Data to generate report from
            options: Generation options
            
        Returns:
            ReportResult
        """
        pass
