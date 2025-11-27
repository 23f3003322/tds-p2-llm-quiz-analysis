"""
Logging Middleware
Logs all incoming requests and responses
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process each request and log details
        """
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"📥 {request.method} {request.url.path}")
        logger.debug(f"Client: {request.client.host if request.client else 'Unknown'}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"📤 Response: {response.status_code} | "
                f"Time: {execution_time:.3f}s"
            )
            
            return response
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ Request failed after {execution_time:.3f}s: {str(e)}",
                exc_info=True
            )
            raise
