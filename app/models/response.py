"""
Response Models (Pydantic Schemas)
Defines the structure of API responses
"""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class SubmissionBody(BaseModel):
    """Request body format for quiz submission"""
    email: str
    secret: str
    url: str
    answer: int


class ImmediateResponse(BaseModel):
    """
    Immediate response sent after validation
    HTTP 200 response before task processing
    """
    success: bool = Field(
        description="Whether request was accepted"
    )
    
    message: str = Field(
        description="Status message"
    )

    
    task_url: str = Field(
        description="Task URL from request"
    )
    
    status: str = Field(
        description="Processing status: processing, completed, failed"
    )
    
    timestamp: str = Field(
        description="Response timestamp (ISO format)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Task accepted and processing started",
                "email": "student@ds.study.iitm.ac.in",
                "task_url": "https://example.com/quiz-834",
                "status": "processing",
                "timestamp": "2025-11-29T12:00:00"
            }
        }


class TaskResponse(BaseModel):
    """
    Schema for successful task responses
    """
    success: bool = Field(
        ...,
        description="Whether the task completed successfully"
    )
    
    message: str = Field(
        ...,
        description="Status message"
    )
    
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Task result data"
    )
    
    email: Optional[str] = Field(
        None,
        description="Email from request"
    )
    
    task_url: Optional[str] = Field(
        None,
        description="Task URL processed"
    )
    
    execution_time: Optional[float] = Field(
        None,
        description="Execution time in seconds"
    )
    
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Response timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Task completed successfully",
                "data": {"result": "Analysis complete"},
                "email": "student@example.com",
                "task_url": "https://example.com/quiz-834",
                "execution_time": 2.34,
                "timestamp": "2025-11-27T23:48:00"
            }
        }


class HealthResponse(BaseModel):
    """
    Schema for health check responses
    """
    status: str = Field(..., description="Service status")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    environment: Optional[str] = Field(None)
    version: Optional[str] = Field(None)
    secret_configured: Optional[bool] = Field(None)
