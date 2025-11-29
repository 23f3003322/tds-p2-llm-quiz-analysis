"""
Base Processor Interface
Abstract base for all data processors
"""

from typing import Dict, Any, List, Optional
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ProcessingResult(BaseModel):
    """Result from data processing"""
    
    success: bool
    data: Any = None
    
    # Statistics
    rows_processed: int = 0
    rows_cleaned: int = 0
    rows_removed: int = 0
    rows_modified: int = 0
    
    # Changes made
    changes_made: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Error handling
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class BaseProcessor(BaseModule):
    """
    Base class for all data processors
    Provides common functionality
    """
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.PROCESSOR)
    
    @abstractmethod
    async def process(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process data
        
        Args:
            data: Data to process
            options: Processing options
            
        Returns:
            ProcessingResult: Processing result
        """
        pass
