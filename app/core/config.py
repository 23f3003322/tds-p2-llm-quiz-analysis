"""
Application Configuration Management
Centralizes all environment variables and settings
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import  Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Application
    APP_NAME: str = "LLM Analysis Quiz API"
    APP_DESCRIPTION: str = "API endpoint for handling dynamic data analysis tasks"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    API_SECRET: str = Field(default="", env="API_SECRET")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["*"],
        env="ALLOWED_ORIGINS"
    )
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    # Cloud Logging
    LOGTAIL_SOURCE_TOKEN: str = Field(default="", env="LOGTAIL_SOURCE_TOKEN")

    
    # Task Processing
    TASK_TIMEOUT: int = Field(default=300, env="TASK_TIMEOUT")  # 5 minutes
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    
    # External APIs (to be added as needed)
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")
    
    # Database (for future use)
    DATABASE_URL: str = Field(default="", env="DATABASE_URL")
    
    # Redis (for caching, future use)
    REDIS_URL: str = Field(default="", env="REDIS_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def is_secret_configured(self) -> bool:
        """Check if API secret is configured"""
        return bool(self.API_SECRET and self.API_SECRET.strip())
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT.lower() == "development"


# Global settings instance
settings = Settings()
