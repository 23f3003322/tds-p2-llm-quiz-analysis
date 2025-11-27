"""
Production Logging with Better Stack (Logtail)
Persistent cloud logging for evaluation and debugging
"""

import os
import sys
import logging
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """
    Configure logging with cloud persistence via Better Stack
    """
    
    # Base formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    root_logger.handlers.clear()
    
    # Console handler (for HF Spaces logs viewer)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Better Stack handler for persistent logging
    if settings.LOGTAIL_SOURCE_TOKEN:
        try:
            from logtail import LogtailHandler
            
            logtail_handler = LogtailHandler(source_token=settings.LOGTAIL_SOURCE_TOKEN)
            logtail_handler.setLevel(logging.INFO)
            logtail_handler.setFormatter(formatter)
            root_logger.addHandler(logtail_handler)
            
            logger = logging.getLogger(__name__)
            logger.info("✅ Better Stack logging enabled - logs will persist")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️  Failed to initialize Better Stack: {e}")
    else:
        logger = logging.getLogger(__name__)
        logger.warning("⚠️  LOGTAIL_SOURCE_TOKEN not set - logs will not persist")
    
    # Reduce third-party noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging initialized for %s", settings.ENVIRONMENT)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
