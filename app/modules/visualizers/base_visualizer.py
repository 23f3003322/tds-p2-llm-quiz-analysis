"""
Base Visualizer Interface
"""

from typing import Dict, Any, Optional, List
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class VisualizationResult(BaseModel):
    """Result from visualization"""
    
    success: bool
    chart_created: bool = False
    chart_type: Optional[str] = None
    chart_path: Optional[str] = None
    chart_base64: Optional[str] = None
    
    # Metadata
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Error handling
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class BaseVisualizer(BaseModule):
    """Base class for visualizers"""
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.VISUALIZER)
    
    @abstractmethod
    async def visualize(
        self,
        data: Any,
        options: Optional[Dict[str, Any]] = None
    ) -> VisualizationResult:
        """
        Create visualization
        
        Args:
            data: Data to visualize
            options: Visualization options
            
        Returns:
            VisualizationResult
        """
        pass
