"""
REST API Client
HTTP REST API implementation
"""

from typing import Dict, Any, Optional, List
import time
import asyncio

import httpx

from app.modules.clients.base_client import BaseAPIClient, APIResponse
from app.modules.clients.api_config import APIConfig, DEFAULT_API_CONFIG
from app.modules.clients.auth_handler import AuthHandler
from app.modules.clients.rate_limiter import RateLimiter
from app.modules.clients.api_utils import (
    build_url,
    extract_pagination_info,
    parse_error_response,
    flatten_nested_response
)
from app.modules.base import ModuleCapability, ModuleResult
from app.modules.capabilities import DataSourceCapability
from app.core.logging import get_logger

logger = get_logger(__name__)


class RESTClient(BaseAPIClient):
    """
    REST API client
    Handles GET, POST, PUT, DELETE requests
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        super().__init__(name="rest_client")
        self.config = config or DEFAULT_API_CONFIG
        self.auth_handler = AuthHandler(self.config)
        self.rate_limiter = RateLimiter(
            calls=self.config.rate_limit_calls,
            period=self.config.rate_limit_period
        )
        self.client = None
        
        logger.debug("RESTClient initialized")
    
    def get_capabilities(self) -> ModuleCapability:
        """Get module capabilities"""
        return DataSourceCapability.API
    
    async def initialize(self):
        """Initialize HTTP client"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
                headers={
                    'User-Agent': self.config.user_agent,
                    **self.config.custom_headers
                }
            )
            logger.debug("HTTP client initialized")
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute API request
        
        Args:
            parameters: Request parameters
                - url: API endpoint (required)
                - method: HTTP method (default: GET)
                - params: Query parameters
                - data: Request body
                - paginate: Fetch all pages (default: False)
            context: Execution context
            
        Returns:
            ModuleResult: API response
        """
        url = parameters.get('url')
        if not url:
            return ModuleResult(
                success=False,
                error="URL parameter is required"
            )
        
        logger.info(f"[REST CLIENT] {parameters.get('method', 'GET')} {url}")
        
        start_time = time.time()
        
        # Initialize client
        await self.initialize()
        
        # Handle pagination
        if parameters.get('paginate', False):
            result = await self._fetch_all_pages(
                url=url,
                method=parameters.get('method', 'GET'),
                params=parameters.get('params'),
                data=parameters.get('data')
            )
        else:
            result = await self.request(
                method=parameters.get('method', 'GET'),
                url=url,
                params=parameters.get('params'),
                data=parameters.get('data')
            )
        
        execution_time = time.time() - start_time
        
        if result.success:
            # Flatten nested response
            data = flatten_nested_response(result.data)
            
            return ModuleResult(
                success=True,
                data=data,
                metadata={
                    'url': url,
                    'method': result.method,
                    'status_code': result.status_code,
                    'records': len(data) if isinstance(data, list) else 1
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=result.error,
                execution_time=execution_time
            )
    
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
        Make API request with retries
        
        Args:
            method: HTTP method
            url: Request URL
            params: Query parameters
            data: Request body
            headers: Custom headers
            
        Returns:
            APIResponse: API response
        """
        # Initialize if needed
        if self.client is None:
            await self.initialize()
        
        # Prepare headers
        request_headers = self.auth_handler.get_auth_headers()
        if headers:
            request_headers.update(headers)
        
        # Add auth to params if needed
        if params:
            params = self.auth_handler.add_auth_params(params)
        
        # Retry logic
        for attempt in range(self.config.max_retries):
            try:
                # Rate limiting
                await self.rate_limiter.acquire()
                
                # Make request
                start_time = time.time()
                
                response = await self.client.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers
                )
                
                response_time = time.time() - start_time
                
                # Parse response
                if self.config.parse_json:
                    try:
                        response_data = response.json()
                    except:
                        response_data = response.text
                else:
                    response_data = response.text
                
                # Check for errors
                if response.status_code >= 400:
                    error_info = parse_error_response(response.status_code, response_data)
                    
                    return APIResponse(
                        success=False,
                        status_code=response.status_code,
                        url=str(response.url),
                        method=method,
                        error=error_info['message'],
                        error_code=error_info['code'],
                        response_time=response_time
                    )
                
                # Extract pagination info
                pagination = extract_pagination_info(
                    response_data,
                    dict(response.headers)
                )
                
                logger.info(f"✓ {method} {url} | Status: {response.status_code} | Time: {response_time:.2f}s")
                
                return APIResponse(
                    success=True,
                    status_code=response.status_code,
                    data=response_data,
                    url=str(response.url),
                    method=method,
                    headers=dict(response.headers),
                    response_time=response_time,
                    has_next_page=pagination['has_next']
                )
                
            except httpx.RequestError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    return APIResponse(
                        success=False,
                        url=url,
                        method=method,
                        error=str(e)
                    )
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """GET request"""
        return await self.request('GET', url, params=params, **kwargs)
    
    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """POST request"""
        return await self.request('POST', url, data=data, **kwargs)
    
    async def put(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> APIResponse:
        """PUT request"""
        return await self.request('PUT', url, data=data, **kwargs)
    
    async def delete(
        self,
        url: str,
        **kwargs
    ) -> APIResponse:
        """DELETE request"""
        return await self.request('DELETE', url, **kwargs)
    
    async def _fetch_all_pages(
        self,
        url: str,
        method: str = 'GET',
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> APIResponse:
        """
        Fetch all pages from paginated API
        
        Args:
            url: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body
            
        Returns:
            APIResponse: Combined response with all pages
        """
        logger.info(f"Fetching all pages from {url}")
        
        all_data = []
        current_url = url
        current_params = params or {}
        page = 1
        
        while True:
            # Check max pages limit
            if self.config.max_pages and page > self.config.max_pages:
                logger.info(f"Reached max pages limit: {self.config.max_pages}")
                break
            
            # Fetch page
            logger.info(f"Fetching page {page}...")
            response = await self.request(
                method=method,
                url=current_url,
                params=current_params,
                data=data
            )
            
            if not response.success:
                logger.error(f"Failed to fetch page {page}: {response.error}")
                break
            
            # Extract data
            page_data = flatten_nested_response(response.data)
            all_data.extend(page_data)
            
            logger.info(f"Page {page}: {len(page_data)} items (Total: {len(all_data)})")
            
            # Check for next page
            if not response.has_next_page:
                logger.info("No more pages")
                break
            
            # Prepare next page request
            page += 1
            current_params['page'] = page
        
        logger.info(f"✓ Fetched {len(all_data)} total items across {page} pages")
        
        return APIResponse(
            success=True,
            data=all_data,
            url=url,
            method=method,
            total_pages=page
        )
    
    async def cleanup(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.debug("HTTP client closed")
