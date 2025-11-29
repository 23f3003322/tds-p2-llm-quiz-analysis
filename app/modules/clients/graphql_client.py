"""
GraphQL Client
GraphQL API implementation
"""

from typing import Dict, Any, Optional
import time

from app.modules.clients.rest_client import RESTClient
from app.modules.clients.base_client import APIResponse
from app.modules.clients.api_config import APIConfig
from app.modules.base import ModuleResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class GraphQLClient(RESTClient):
    """
    GraphQL API client
    Extends REST client for GraphQL queries
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        super().__init__(config)
        self.name = "graphql_client"
        logger.debug("GraphQLClient initialized")
    
    async def query(
        self,
        url: str,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> APIResponse:
        """
        Execute GraphQL query
        
        Args:
            url: GraphQL endpoint
            query: GraphQL query string
            variables: Query variables
            operation_name: Operation name
            
        Returns:
            APIResponse: Query response
        """
        logger.info(f"[GRAPHQL] Executing query at {url}")
        
        payload = {
            'query': query
        }
        
        if variables:
            payload['variables'] = variables
        
        if operation_name:
            payload['operationName'] = operation_name
        
        response = await self.post(url, data=payload)
        
        # Extract data from GraphQL response
        if response.success and isinstance(response.data, dict):
            if 'data' in response.data:
                response.data = response.data['data']
            
            # Check for GraphQL errors
            if 'errors' in response.data:
                errors = response.data['errors']
                error_messages = [e.get('message', str(e)) for e in errors]
                response.success = False
                response.error = '; '.join(error_messages)
        
        return response
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ModuleResult:
        """
        Execute GraphQL query via module interface
        
        Args:
            parameters: Query parameters
                - url: GraphQL endpoint (required)
                - query: GraphQL query (required)
                - variables: Query variables (optional)
                - operation_name: Operation name (optional)
            context: Execution context
            
        Returns:
            ModuleResult: Query response
        """
        url = parameters.get('url')
        query = parameters.get('query')
        
        if not url or not query:
            return ModuleResult(
                success=False,
                error="Both 'url' and 'query' parameters are required"
            )
        
        logger.info(f"[GRAPHQL CLIENT] Executing query")
        
        start_time = time.time()
        
        await self.initialize()
        
        response = await self.query(
            url=url,
            query=query,
            variables=parameters.get('variables'),
            operation_name=parameters.get('operation_name')
        )
        
        execution_time = time.time() - start_time
        
        if response.success:
            return ModuleResult(
                success=True,
                data=response.data,
                metadata={
                    'url': url,
                    'method': 'GraphQL',
                    'status_code': response.status_code
                },
                execution_time=execution_time
            )
        else:
            return ModuleResult(
                success=False,
                error=response.error,
                execution_time=execution_time
            )
