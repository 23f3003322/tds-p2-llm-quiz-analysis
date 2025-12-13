"""
Application Configuration Management
"""

import os
import json
import base64
import tempfile
from typing import List,Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
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
    USER_EMAIL: str = Field(default="", env="USER_EMAIL")
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_DIR: str = Field(default="logs", env="LOG_DIR")
    
    # Google Cloud Logging
    GOOGLE_CLOUD_PROJECT: str = Field(default="", env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_CREDENTIALS_BASE64: str = Field(
        default="",
        env="GOOGLE_CREDENTIALS_BASE64",
        description="Base64-encoded service account JSON"
    )

    ENABLE_CLOUD_LOGGING: bool = Field(default=True, env="ENABLE_CLOUD_LOGGING")

    # LLM Configuration (AIPipe)
    AIPIPE_TOKEN: str = Field(
        default="",
        env="AIPIPE_TOKEN",
        description="AIPipe authentication token"
    )
    AIPIPE_BASE_URL: str = Field(
        default="https://aipipe.org/openrouter/v1",
        env="AIPIPE_BASE_URL",
        description="AIPipe base URL (openrouter or openai)"
    )
    LLM_DEFAULT_MODEL: str = Field(
        default="google/gemini-2.0-flash-lite-001",
        env="LLM_DEFAULT_MODEL",
        description="Default LLM model to use"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        env="LLM_TEMPERATURE",
        description="LLM temperature for generation"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2000,
        env="LLM_MAX_TOKENS",
        description="Maximum tokens in LLM response"
    )
    LLM_TIMEOUT: int = Field(
        default=60,
        env="LLM_TIMEOUT",
        description="LLM request timeout in seconds"
    )
    
    USE_PYDANTIC_AI: bool = Field(
        default=True,
        env="USE_PYDANTIC_AI",
        description="Use Pydantic AI for structured outputs"
    )
    
    
    # Task Processing
    TASK_TIMEOUT: int = Field(default=300, env="TASK_TIMEOUT")
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    
    # External APIs
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(default="", env="ANTHROPIC_API_KEY")

    # Internal (set automatically)
    _credentials_path: Optional[str] = None
    
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
    
    def is_llm_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return bool(self.AIPIPE_TOKEN and self.AIPIPE_TOKEN.strip())
    
    def is_cloud_logging_enabled(self) -> bool:
        """Check if Google Cloud Logging is properly configured"""
        return (
            self.ENABLE_CLOUD_LOGGING and
            bool(self.GOOGLE_CLOUD_PROJECT) and
            bool(self.GOOGLE_CREDENTIALS_BASE64)
        )
    
    def get_credentials_path(self) -> Optional[str]:
        """
        Get the path to Google Cloud credentials file
        Decodes base64 credentials and writes to temp file
        
        Returns:
            str: Path to credentials file or None
        """
        # Return cached path if already set
        if self._credentials_path and os.path.exists(self._credentials_path):
            return self._credentials_path
        
        if not self.GOOGLE_CREDENTIALS_BASE64:
            return None
        
        try:
            # Decode base64 credentials
            credentials_json = base64.b64decode(
                self.GOOGLE_CREDENTIALS_BASE64
            ).decode('utf-8')
            
            # Verify it's valid JSON
            json.loads(credentials_json)
            
            # Write to temporary file
            temp_dir = tempfile.gettempdir()
            creds_path = os.path.join(temp_dir, 'gcp-credentials.json')
            
            with open(creds_path, 'w') as f:
                f.write(credentials_json)
            
            # Set environment variable for Google Cloud libraries
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
            
            # Cache the path
            self._credentials_path = creds_path
            
            print(f"✓ Google credentials decoded: {creds_path}")
            return creds_path
            
        except base64.binascii.Error:
            print("✗ Invalid base64 encoding in GOOGLE_CREDENTIALS_BASE64")
            return None
        except json.JSONDecodeError:
            print("✗ Invalid JSON in decoded credentials")
            return None
        except Exception as e:
            print(f"✗ Failed to setup Google credentials: {e}")
            return None


# Global settings instance
settings = Settings()

# Setup credentials immediately when config is loaded
if settings.GOOGLE_CREDENTIALS_BASE64:
    settings.get_credentials_path()
