"""
API Configuration
Settings and authentication types
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class AuthType(str, Enum):
    """Authentication types"""
    NONE = "none"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"
    OAUTH2 = "oauth2"
    CUSTOM_HEADER = "custom_header"


class APIConfig(BaseModel):
    """Configuration for API clients"""
    
    # Request settings
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries (seconds)")
    
    # Authentication
    auth_type: AuthType = Field(default=AuthType.NONE, description="Authentication type")
    api_key: Optional[str] = Field(None, description="API key")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key")
    bearer_token: Optional[str] = Field(None, description="Bearer token")
    username: Optional[str] = Field(None, description="Username for basic auth")
    password: Optional[str] = Field(None, description="Password for basic auth")
    
    # Custom headers
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom HTTP headers"
    )
    
    # Rate limiting
    rate_limit_calls: Optional[int] = Field(
        None,
        description="Maximum calls per period"
    )
    rate_limit_period: float = Field(
        default=60.0,
        description="Rate limit period in seconds"
    )
    
    # Pagination
    max_pages: Optional[int] = Field(
        None,
        description="Maximum pages to fetch (None = unlimited)"
    )
    page_size: int = Field(default=100, description="Items per page")
    
    # Response handling
    parse_json: bool = Field(default=True, description="Automatically parse JSON")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    follow_redirects: bool = Field(default=True, description="Follow redirects")
    
    # User agent
    user_agent: str = Field(
        default="TDS-API-Client/1.0",
        description="User agent string"
    )


# Default configuration
DEFAULT_API_CONFIG = APIConfig()
    