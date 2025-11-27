"""
Main FastAPI Application Entry Point
Initializes the FastAPI app with all configurations, middleware, and routes
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers
from app.middleware.logging import LoggingMiddleware
from app.api.routes import task, health
from app.core.logging import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with log flushing"""
    # Startup
    logger.info("=" * 80)
    logger.info("🚀 Starting LLM Analysis Quiz API")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("=" * 80)
    

    yield
    
    # Shutdown
    logger.info("=" * 80)
    logger.info("🛑 Shutting down - flushing logs")
    logger.info("=" * 80)
    
def create_application() -> FastAPI:
    """
    Application factory pattern for creating FastAPI instance
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(LoggingMiddleware)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(task.router, tags=["Tasks"])
    
    return app


# Initialize logging
setup_logging()

# Create app instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level="info"
    )
