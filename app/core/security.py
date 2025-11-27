"""
Security Utilities
Handles authentication and authorization
"""

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def verify_secret(provided_secret: str) -> bool:
    """
    Verify the provided secret against environment configuration
    
    Args:
        provided_secret: Secret from request
        
    Returns:
        bool: True if secret matches, False otherwise
    """
    if not settings.is_secret_configured():
        logger.error("⚠️  API_SECRET not configured in environment")
        return False
    
    is_valid = provided_secret == settings.API_SECRET
    
    if is_valid:
        logger.info("✅ Secret verification successful")
    else:
        logger.warning("🚫 Secret verification failed")
        logger.debug(
            f"Expected length: {len(settings.API_SECRET)}, "
            f"Got length: {len(provided_secret)}"
        )
    
    return is_valid


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask secret for logging purposes
    
    Args:
        secret: Secret to mask
        visible_chars: Number of characters to show at the end
        
    Returns:
        str: Masked secret
    """
    if not secret:
        return ""
    
    if len(secret) <= visible_chars:
        return "*" * len(secret)
    
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]
