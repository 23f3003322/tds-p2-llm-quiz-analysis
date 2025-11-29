"""
Base API Client
Abstract base for all API clients
"""

from typing import Dict, Any, Optional, List
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class APIResponse(BaseModel):
    """Response from API call"""
    
    success: bool
    status_code: int = 200
    data: Any = None
    
    # Metadata
    url: str
    method: str = "GET"
    headers: Dict[str, str] = Field(default_factory=dict)
    response_time: float = 0.0
    
    # Pagination
    total_pages: Optional[int] = None
    current_page: Optional[int] = None
    has_next_page: bool = False
    
    # Error handling
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class BaseAPIClient(BaseModule):
    """
    Base class for all API clients
    Provides common functionality
    """
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.DATA_SOURCE)
    
    @abstractmethod
    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> APIResponse:
        """
        Make API request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            data: Request body
            headers: Custom headers
            **kwargs: Additional options
            
        Returns:
            APIResponse: API response
        """
        pass
    
    @abstractmethod
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """GET request"""
        pass
    
    @abstractmethod
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """POST request"""
        pass
