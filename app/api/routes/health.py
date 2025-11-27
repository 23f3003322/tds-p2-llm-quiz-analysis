"""
Health Check Routes
Endpoints for monitoring application health
"""

from fastapi import APIRouter

from app.core.config import settings
from app.models.response import HealthResponse
from app.core.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def root():
    """
    Root endpoint - basic health check
    """
    logger.debug("Root endpoint accessed")

    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Detailed health check endpoint
    """
    logger.debug("Health check requested")

    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        secret_configured=settings.is_secret_configured()
    )
