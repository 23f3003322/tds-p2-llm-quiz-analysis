"""
Scraper Configuration
Settings and options for web scraping
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ScraperConfig(BaseModel):
    """Configuration for web scraping"""
    
    # Request settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries")
    
    # Headers
    user_agent: str = Field(
        default="Mozilla/5.0 (compatible; TDS-Scraper/1.0)",
        description="User agent string"
    )
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers"
    )
    
    # Rate limiting
    rate_limit_delay: float = Field(
        default=1.0,
        description="Delay between requests (seconds)"
    )
    max_concurrent_requests: int = Field(
        default=5,
        description="Maximum concurrent requests"
    )
    
    # Parsing
    parser: str = Field(
        default="html.parser",
        description="BeautifulSoup parser (html.parser, lxml, html5lib)"
    )
    encoding: Optional[str] = Field(
        None,
        description="Force specific encoding"
    )
    
    # Data extraction
    default_selectors: Dict[str, str] = Field(
        default_factory=dict,
        description="Default CSS selectors"
    )
    max_results: Optional[int] = Field(
        None,
        description="Maximum results to extract"
    )
    
    # Error handling
    raise_on_error: bool = Field(
        default=False,
        description="Raise exception on scraping errors"
    )
    skip_ssl_verify: bool = Field(
        default=False,
        description="Skip SSL certificate verification"
    )


# Default configuration
DEFAULT_CONFIG = ScraperConfig()
