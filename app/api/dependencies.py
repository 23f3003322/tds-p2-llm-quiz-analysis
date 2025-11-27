"""
API Dependencies
Reusable dependency injection functions
"""

from fastapi import Request, HTTPException, status

from app.core.security import verify_secret
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)


async def get_request_body(request: Request) -> dict:
    """
    Extract and validate JSON body from request
    
    Args:
        request: FastAPI Request object
        
    Returns:
        dict: Parsed JSON body
        
    Raises:
        HTTPException: If JSON parsing fails
    """
    try:
        body = await request.json()
        logger.debug(f"Request body received: {list(body.keys())}")
        return body
    except Exception as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format in request body"
        )


def verify_authentication(secret: str) -> bool:
    """
    Verify request authentication
    
    Args:
        secret: Secret from request
        
    Returns:
        bool: True if authenticated
        
    Raises:
        AuthenticationError: If authentication fails
    """
    if not verify_secret(secret):
        raise AuthenticationError("Invalid secret. Authentication failed.")
    
    return True
