"""
Base Analyzer Interface
Abstract base for all analyzers
"""

from typing import Dict, Any, List, Optional
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalysisResult(BaseModel):
    """Result from data analysis"""
    
    success: bool
    
    # Statistical results
    statistics: Dict[str, Any] = Field(default_factory=dict)
    
    # LLM-generated insights
    insights: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    rows_analyzed: int = 0
    analysis_type: str = "general"
    
    # Error handling
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class BaseAnalyzer(BaseModule):
    """
    Base class for all analyzers
    Provides common functionality
    """
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.PROCESSOR)
    
    @abstractmethod
    async def analyze(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Analyze data
        
        Args:
            data: Data to analyze
            options: Analysis options
            
        Returns:
            AnalysisResult: Analysis result
        """
        pass
