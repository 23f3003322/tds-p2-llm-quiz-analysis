"""
Request Models (Pydantic Schemas)
Defines the structure of incoming requests
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, validator


class ManualTriggeredRequestBody(BaseModel):
    """Request body format for quiz submission"""
    url: str



class TaskRequest(BaseModel):
    """
    Schema for task request validation
    """
    email: EmailStr = Field(
        ...,
        description="Student email ID",
        examples=["student@ds.study.iitm.ac.in"]
    )
    
    secret: str = Field(
        ...,
        min_length=1,
        description="Student-provided secret for authentication",
        examples=["my-secret-key-123"]
    )
    
    url: HttpUrl = Field(
        ...,
        description="Unique task URL containing the quiz question",
        examples=["https://example.com/quiz-834"]
    )
    
    task_description: Optional[str] = Field(
        None,
        description="Optional description of the task to perform"
    )
    
    additional_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional parameters for task execution"
    )
    
    @validator('secret')
    def secret_not_empty(cls, v):
        """Ensure secret is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('Secret cannot be empty or whitespace')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@ds.study.iitm.ac.in",
                "secret": "your-secret-key",
                "url": "https://example.com/quiz-834",
                "task_description": "Scrape the webpage and analyze data"
            }
        }
