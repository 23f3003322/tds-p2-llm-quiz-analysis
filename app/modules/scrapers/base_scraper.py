"""
Base Scraper Interface
All scrapers inherit from this
"""

from typing import Dict, Any, List, Optional
from abc import abstractmethod
from pydantic import BaseModel, Field

from app.modules.base import BaseModule, ModuleType, ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class ScraperResult(BaseModel):
    """Result from web scraping"""
    
    success: bool
    url: str
    data: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    rows_extracted: int = 0
    content_type: str = "html"
    encoding: str = "utf-8"
    response_time: float = 0.0
    status_code: int = 200
    raw_html: Optional[str] = None
    
    # Scraping details
    selectors_used: List[str] = Field(default_factory=list)
    columns_extracted: List[str] = Field(default_factory=list)
    
    # Errors and warnings
    error: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    
    def __post_init__(self):
        if self.data is None:
            self.data = []
        if self.columns_extracted is None:
            self.columns_extracted = []
        if self.selectors_used is None:
            self.selectors_used = []
    
    class Config:
        arbitrary_types_allowed = True


class BaseScraper(BaseModule):
    """
    Base class for all web scrapers
    Provides common functionality
    """
    
    def __init__(self, name: str):
        super().__init__(name=name, module_type=ModuleType.SCRAPER)
        self.session = None
    
    @abstractmethod
    async def scrape_url(
        self,
        url: str,
        selectors: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> ScraperResult:
        """
        Scrape a URL
        
        Args:
            url: URL to scrape
            selectors: CSS selectors for data extraction
            **kwargs: Additional scraping options
            
        Returns:
            ScraperResult: Scraping result
        """
        pass
    
    @abstractmethod
    async def scrape_multiple(
        self,
        urls: List[str],
        selectors: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[ScraperResult]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            selectors: CSS selectors for data extraction
            **kwargs: Additional scraping options
            
        Returns:
            List[ScraperResult]: List of results
        """
        pass
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        import re
        
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        
        return bool(url_pattern.match(url))
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL (add http if missing)"""
        if not url.startswith(('http://', 'https://')):
            return f'https://{url}'
        return url
