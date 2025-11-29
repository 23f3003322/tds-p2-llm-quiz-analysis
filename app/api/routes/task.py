"""
Task API Routes
Handles task submission and processing
"""

from fastapi import APIRouter, Request, status, BackgroundTasks, HTTPException
from datetime import datetime
from typing import Dict, Any

from app.models.request import TaskRequest
from app.models.response import TaskResponse, ImmediateResponse
from app.core.logging import get_logger
from app.core.security import verify_authentication, AuthenticationError
from app.core.exceptions import TaskProcessingError
from app.services.task_processor import TaskProcessor

logger = get_logger(__name__)

router = APIRouter()

# Initialize task processor (singleton)
task_processor = TaskProcessor()


@router.post(
    "/task",
    response_model=ImmediateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Request accepted and processing started"},
        400: {"description": "Invalid JSON format or request data"},
        403: {"description": "Invalid secret - authentication failed"}
    }
)
async def handle_task(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Main API endpoint for handling task requests
    
    Flow:
    1. Validate JSON format (HTTP 400 if invalid)
    2. Verify secret (HTTP 403 if invalid)
    3. Respond immediately with HTTP 200
    4. Process task in background
    
    Returns:
        Immediate HTTP 200 response with task accepted message
    """
    start_time = datetime.now()
    
    logger.info("📥 Task request received")
    
    try:
        # ================================================================
        # STEP 1: PARSE AND VALIDATE JSON (HTTP 400 if invalid)
        # ================================================================
        try:
            body = await request.json()
            task_data = TaskRequest(**body)
        except ValueError as e:
            logger.error(f"❌ Invalid JSON format: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON format: {str(e)}"
            )
        except Exception as e:
            logger.error(f"❌ Request validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request data: {str(e)}"
            )
        
        logger.info(f"✅ Request validated for: {task_data.email}")
        
        # ================================================================
        # STEP 2: VERIFY AUTHENTICATION (HTTP 403 if invalid)
        # ================================================================
        logger.info("🔐 Verifying authentication")
        try:
            verify_authentication(task_data.secret)
        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid secret. Authentication failed."
            )
        
        logger.info("✅ Authentication successful")
        
        # ================================================================
        # STEP 3: RESPOND IMMEDIATELY WITH HTTP 200
        # ================================================================
        logger.info("✅ Request accepted - processing in background")
        
        # Add task processing to background
        background_tasks.add_task(
            process_task_background,
            task_data=task_data,
            start_time=start_time
        )
        
        # Immediate response
        response = ImmediateResponse(
            success=True,
            message="Task accepted and processing started",
            email=task_data.email,
            task_url=str(task_data.url),
            status="processing",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"📤 Sent immediate response to client")
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions (400, 403)
        raise
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


async def process_task_background(
    task_data: TaskRequest,
    start_time: datetime
):
    """
    Process task in background after sending immediate response
    
    This runs asynchronously after the HTTP 200 response is sent.
    Results are logged but not returned to client.
    
    Args:
        task_data: Validated task request
        start_time: Request start time for metrics
    """
    logger.info("=" * 80)
    logger.info("🔄 BACKGROUND TASK PROCESSING STARTED")
    logger.info("=" * 80)
    logger.info(f"🔗 URL: {task_data.url}")
    
    try:
        # Process the task
        result_data = await task_processor.process(task_data)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        
        
        # Optional: Store result in database/cache for later retrieval
        # await store_result(task_data.email, result_data)
        
    except TaskProcessingError as e:
        logger.error("=" * 80)
        logger.error("❌ BACKGROUND TASK FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 80)
        
        # Optional: Store error for later retrieval or send notification
        # await store_error(task_data.email, str(e))
    
    except Exception as e:
        logger.error("=" * 80)
        logger.error("❌ BACKGROUND TASK UNEXPECTED ERROR")
        logger.error("=" * 80)
        logger.error(f"Error: {str(e)}", exc_info=True)
        logger.error("=" * 80)
