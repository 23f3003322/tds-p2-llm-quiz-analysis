"""
Security and Authentication
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


def verify_secret(secret: str) -> bool:
    """
    Verify if provided secret is valid
    
    Args:
        secret: Secret from request
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Get expected secret from config/env
    expected_secret = settings.API_SECRET
    
    # Simple comparison (use constant-time comparison in production)
    is_valid = secret == expected_secret
    
    if not is_valid:
        logger.warning(f"❌ Invalid secret attempt")
    
    return is_valid


def verify_authentication(secret: str) -> bool:
    """
    Verify request authentication
    
    Args:
        secret: Secret from request
        
    Returns:
        bool: True if authenticated
        
    Raises:
        AuthenticationError: If authentication fails (HTTP 403)
    """
    if not verify_secret(secret):
        raise AuthenticationError("Invalid secret. Authentication failed.")
    
    return True
