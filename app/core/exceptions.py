"""
Custom Exceptions and Exception Handlers
Centralizes error handling logic
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskProcessingError(Exception):
    """Raised when task processing fails"""
    pass

class AnswerGenerationError(Exception):
    """Raised when answer generation fails"""
    pass


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


def create_error_response(
    error_type: str,
    message: str,
    status_code: int,
    details: Any = None
) -> JSONResponse:
    """
    Create a standardized error response
    
    Args:
        error_type: Type of error
        message: Error message
        status_code: HTTP status code
        details: Optional additional details
        
    Returns:
        JSONResponse: Formatted error response
    """
    content = {
        "success": False,
        "error": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        content["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


def register_exception_handlers(app: FastAPI):
    """
    Register all exception handlers with the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ):
        """Handle Pydantic validation errors (HTTP 400)"""
        error_details = exc.errors()
        logger.error(f"❌ Validation Error: {error_details}")
        
        # Extract readable error messages
        error_messages = []
        for error in error_details:
            field = " -> ".join(str(loc) for loc in error['loc'])
            message = error['msg']
            error_messages.append(f"{field}: {message}")
        
        return create_error_response(
            error_type="ValidationError",
            message="Invalid request format. " + "; ".join(error_messages),
            status_code=status.HTTP_400_BAD_REQUEST,
            details=error_details
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions"""
        logger.error(f"❌ HTTP {exc.status_code}: {exc.detail}")
        
        return create_error_response(
            error_type=f"HTTP{exc.status_code}",
            message=exc.detail,
            status_code=exc.status_code
        )
    
    @app.exception_handler(TaskProcessingError)
    async def task_processing_exception_handler(
        request: Request,
        exc: TaskProcessingError
    ):
        """Handle task processing errors"""
        logger.error(f"❌ Task Processing Error: {str(exc)}", exc_info=True)
        
        return create_error_response(
            error_type="TaskProcessingError",
            message=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(
        request: Request,
        exc: AuthenticationError
    ):
        """Handle authentication errors"""
        logger.warning(f"🚫 Authentication Error: {str(exc)}")
        
        return create_error_response(
            error_type="AuthenticationError",
            message=str(exc),
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Catch-all handler for unexpected exceptions"""
        logger.error(
            f"❌ Unhandled Exception: {str(exc)}",
            exc_info=True
        )
        
        return create_error_response(
            error_type="InternalServerError",
            message="An unexpected error occurred while processing your request",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
