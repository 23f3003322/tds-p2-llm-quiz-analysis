"""
Base Module Interface
All processing modules inherit from this
"""

from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod
from enum import Enum
from pydantic import BaseModel, Field

from app.core.logging import get_logger

logger = get_logger(__name__)


class ModuleType(str, Enum):
    """Types of processing modules"""
    SCRAPER = "scraper"
    PROCESSOR = "processor"
    ANALYZER = "analyzer"
    VISUALIZER = "visualizer"
    EXPORTER = "exporter"
    API_CLIENT = "api_client"


class ModuleCapability(BaseModel):
    """Capability definition for a module"""
    
    # What can this module do?
    can_scrape_static: bool = False
    can_scrape_dynamic: bool = False
    can_handle_javascript: bool = False
    can_authenticate: bool = False
    can_handle_api: bool = False
    can_process_data: bool = False
    can_clean_data: bool = False
    can_transform_data: bool = False
    can_aggregate: bool = False
    can_filter: bool = False
    can_sort: bool = False
    can_visualize: bool = False
    can_create_charts: bool = False
    can_create_maps: bool = False
    can_export_csv: bool = False
    can_export_json: bool = False
    can_export_excel: bool = False
    can_export_pdf: bool = False
    
    # What data formats can it handle?
    supported_input_formats: Set[str] = Field(default_factory=set)
    supported_output_formats: Set[str] = Field(default_factory=set)
    
    # Performance characteristics
    max_concurrent_requests: int = 1
    estimated_speed: str = "medium"  # fast, medium, slow
    memory_usage: str = "medium"  # low, medium, high
    
    # Requirements
    requires_browser: bool = False
    requires_api_key: bool = False
    requires_database: bool = False


class ModuleResult(BaseModel):
    """Result from module execution"""
    
    success: bool
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True


class BaseModule(ABC):
    """
    Base class for all processing modules
    All modules must inherit from this and implement required methods
    """
    
    def __init__(self, name: str, module_type: ModuleType):
        """
        Initialize base module
        
        Args:
            name: Module name
            module_type: Type of module
        """
        self.name = name
        self.module_type = module_type
        self.logger = get_logger(f"module.{name}")
        self._is_initialized = False
    
    @abstractmethod
    def get_capabilities(self) -> ModuleCapability:
        """
        Return module capabilities
        
        Returns:
            ModuleCapability: What this module can do
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute module with given parameters
        
        Args:
            parameters: Execution parameters
            context: Optional execution context
            
        Returns:
            ModuleResult: Execution result
        """
        pass
    
    async def initialize(self) -> bool:
        """
        Initialize module (load models, connect to services, etc.)
        Override this if your module needs initialization
        
        Returns:
            bool: True if initialization successful
        """
        self._is_initialized = True
        return True
    
    async def cleanup(self):
        """
        Clean up module resources
        Override this if your module needs cleanup
        """
        self._is_initialized = False
    
    def is_initialized(self) -> bool:
        """Check if module is initialized"""
        return self._is_initialized
    
    def can_handle(self, parameters: Dict[str, Any]) -> bool:
        """
        Check if this module can handle given parameters
        Override this for custom logic
        
        Args:
            parameters: Parameters to check
            
        Returns:
            bool: True if module can handle these parameters
        """
        return True
    
    def estimate_cost(self, parameters: Dict[str, Any]) -> float:
        """
        Estimate execution cost/time for given parameters
        Used for module selection
        
        Args:
            parameters: Parameters to estimate for
            
        Returns:
            float: Estimated cost (lower is better)
        """
        return 1.0
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', type='{self.module_type}')>"
