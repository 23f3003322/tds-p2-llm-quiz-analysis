"""
Answer Submission Utility
Handles answer submission and chained quiz processing
"""

from datetime import datetime
from fastapi import HTTPException, BackgroundTasks
from app.core.logging import get_logger
from app.models.request import ManualTriggeredRequestBody
logger = get_logger(__name__)
import requests


def submit_answer(submit_url: str, req_url: str ,answer:str, background_tasks: BackgroundTasks = None) -> dict:
    """
    Submits an answer to the provided submit_url and triggers next quiz if URL is returned.
    
    Args:
        submit_url: The URL endpoint to submit the answer to
        body: Dictionary containing email, secret, url, and answer
        background_tasks: FastAPI BackgroundTasks for chained processing
        
    Returns:
        The response from the server containing correct status, reason, url, and delay
        
    Raises:
        HTTPException on request failure
    """
    try:
        logger.info(f"Submitting answer to {submit_url}")
        
        # Get email and secret from environment
        from app.core.config import settings
        
        answer_body = {
            "email": settings.USER_EMAIL,
            "secret": settings.API_SECRET,
            "url": req_url,
            "answer": answer
        }
        response = requests.post(submit_url, json=answer_body, timeout=15)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Submission response: {result}")
        
        print(f"[submit_answer] Response from {submit_url}:")

        print ("="* 8)
        print("answer")
        print(result.get("correct"))
        print(result)
        print ("="* 8)
        
        # If response contains a url, process it as the next quiz in background
        if result.get("url"):
            next_url = result["url"]
            logger.info(f"🔗 Chained quiz detected: {next_url}")
            print(f"\n[submit_answer] Adding next quiz to background tasks: {next_url}")
            
            # If background_tasks available (from FastAPI), use it
            if background_tasks:
                background_tasks.add_task(
                    process_next_quiz,
                    next_url=next_url,
                    email=answer_body.get("email"),
                    start_time=datetime.now()
                )
            else:
                # Fallback: run in background thread
                import threading
                thread = threading.Thread(
                    target=process_next_quiz,
                    args=(next_url, answer_body.get("email"), datetime.now()),
                    daemon=True
                )
                thread.start()
                logger.info(f"✓ Started background thread for chained quiz")
        
        return result
        
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to submit answer to {submit_url}: {exc}")
        raise HTTPException(status_code=400, detail=f"Submission failed: {exc}")


def process_next_quiz(next_url: str, email: str, start_time: datetime):
    """
    Process the next quiz in the chain as a background task.
    
    Args:
        next_url: URL of the next quiz to process
        email: User's email address
        start_time: Start time for tracking
    """
    try:
        logger.info(f"🔄 Processing chained quiz: {next_url}")
        
        # Import here to avoid circular dependency
        from app.services.task_processor import TaskProcessor
        
        # Create task data for next quiz
        task_data = ManualTriggeredRequestBody(url=next_url)
        
        # Process the next quiz
        processor = TaskProcessor()
        import asyncio
        result = asyncio.run(processor.process(task_data))
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Chained quiz completed in {elapsed:.2f}s")
        
    except Exception as e:
        logger.error(f"❌ Failed to process chained quiz: {e}", exc_info=True)
