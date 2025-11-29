"""
Authentication Handler
Handles different authentication methods
"""

from typing import Dict, Optional
import base64

from app.modules.clients.api_config import APIConfig, AuthType
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthHandler:
    """
    Handles API authentication
    Supports multiple auth types
    """
    
    def __init__(self, config: APIConfig):
        """
        Initialize auth handler
        
        Args:
            config: API configuration
        """
        self.config = config
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers
        
        Returns:
            Dict: Authentication headers
        """
        headers = {}
        
        if self.config.auth_type == AuthType.API_KEY:
            if self.config.api_key:
                headers[self.config.api_key_header] = self.config.api_key
                logger.debug(f"Added API key header: {self.config.api_key_header}")
        
        elif self.config.auth_type == AuthType.BEARER_TOKEN:
            if self.config.bearer_token:
                headers["Authorization"] = f"Bearer {self.config.bearer_token}"
                logger.debug("Added Bearer token")
        
        elif self.config.auth_type == AuthType.BASIC_AUTH:
            if self.config.username and self.config.password:
                credentials = f"{self.config.username}:{self.config.password}"
                encoded = base64.b64encode(credentials.encode()).decode()
                headers["Authorization"] = f"Basic {encoded}"
                logger.debug("Added Basic auth")
        
        elif self.config.auth_type == AuthType.CUSTOM_HEADER:
            headers.update(self.config.custom_headers)
            logger.debug(f"Added custom headers: {list(self.config.custom_headers.keys())}")
        
        return headers
    
    def add_auth_params(self, params: Dict[str, str]) -> Dict[str, str]:
        """
        Add authentication parameters to URL params
        
        Args:
            params: Existing parameters
            
        Returns:
            Dict: Parameters with auth added
        """
        if self.config.auth_type == AuthType.API_KEY:
            # Some APIs use query parameter instead of header
            if 'api_key' not in params and self.config.api_key:
                params['api_key'] = self.config.api_key
        
        return params
