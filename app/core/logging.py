"""
Production Logging with Google Cloud Logging
Uses base64-encoded credentials only
"""

import os
import sys
import logging
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """
    Configure logging with Google Cloud Logging
    Credentials are decoded from base64 in config.py
    """
    
    # Base formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.handlers.clear()
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Google Cloud Logging handler
    if settings.is_cloud_logging_enabled():
        try:
            # Get credentials path (triggers decode if needed)
            creds_path = settings.get_credentials_path()
            
            if not creds_path:
                raise Exception("Failed to decode Google credentials from base64")
            
            import google.cloud.logging
            from google.cloud.logging_v2.handlers import CloudLoggingHandler
            
            # Initialize client (uses GOOGLE_APPLICATION_CREDENTIALS env var)
            client = google.cloud.logging.Client(
                project=settings.GOOGLE_CLOUD_PROJECT
            )
            
            # Create cloud handler
            cloud_handler = CloudLoggingHandler(
                client,
                name="fastapi-logs"
            )
            cloud_handler.setLevel(logging.INFO)
            
            # Add to root logger
            root_logger.addHandler(cloud_handler)
            
            logger = logging.getLogger(__name__)
            logger.info("=" * 60)
            logger.info("✅ Google Cloud Logging initialized")
            logger.info(f"Project: {settings.GOOGLE_CLOUD_PROJECT}")
            logger.info(f"Environment: {settings.ENVIRONMENT}")
            logger.info("=" * 60)
            
        except ImportError:
            logger = logging.getLogger(__name__)
            logger.error("❌ google-cloud-logging not installed")
            logger.error("   Run: pip install google-cloud-logging")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to initialize Google Cloud Logging: {e}")
            logger.error(f"   Check GOOGLE_CREDENTIALS_BASE64 is valid")
    else:
        logger = logging.getLogger(__name__)
        
        if not settings.ENABLE_CLOUD_LOGGING:
            logger.info("ℹ️  Cloud logging disabled")
        elif not settings.GOOGLE_CLOUD_PROJECT:
            logger.warning("⚠️  GOOGLE_CLOUD_PROJECT not set")
        elif not settings.GOOGLE_CREDENTIALS_BASE64:
            logger.warning("⚠️  GOOGLE_CREDENTIALS_BASE64 not set")
    
    # Reduce third-party noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("google.cloud").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized for {settings.ENVIRONMENT} environment")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
