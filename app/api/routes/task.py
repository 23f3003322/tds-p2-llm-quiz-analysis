"""
Task Processing Routes
Main API endpoint for handling task requests
"""

from datetime import datetime
from fastapi import APIRouter, Request, status

from app.models.request import TaskRequest
from app.models.response import TaskResponse
from app.api.dependencies import verify_authentication
from app.services.task_processor import TaskProcessor
from app.core.logging import get_logger

import requests

logger = get_logger(__name__)

router = APIRouter()
task_processor = TaskProcessor()


@router.post("/task", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def handle_task(request: Request):
    """
    Main API endpoint for handling task requests
    
    - Validates request format (HTTP 400 if invalid)
    - Verifies secret (HTTP 403 if invalid)
    - Processes task and returns results (HTTP 200 if successful)
    """
    start_time = datetime.now()
    
    logger.info("📥 Task request received")
    
    # Parse and validate request body with Pydantic
    body = await request.json()
    task_data = TaskRequest(**body)
    
    logger.info(f"✅ Request validated for: {task_data.email}")
    
    # Verify authentication
    logger.info("🔐 Verifying authentication")
    verify_authentication(task_data.secret)
    logger.info("✅ Authentication successful")
    
    # Process the task
    logger.info("🚀 Starting task execution")
    result_data = await task_processor.process(task_data)
    
    # Calculate execution time
    execution_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"⏱️  Task completed in {execution_time:.3f}s")
    
    # Prepare response
    response = TaskResponse(
        success=True,
        message="Task completed successfully",
        data=result_data,
        email=task_data.email,
        task_url=str(task_data.url),
        execution_time=execution_time
    )
    
    logger.info("✅ Response prepared successfully")
    return response
