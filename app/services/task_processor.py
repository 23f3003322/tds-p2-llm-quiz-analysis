"""
Task Processing Service
Updated to use Task Classifier
"""

from typing import Dict, Any

from app.models.request import TaskRequest
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.services.task_fetcher import TaskFetcher
from app.orchestrator.classifier import TaskClassifier
from app.orchestrator.actions.action_executor import ActionExecutor

logger = get_logger(__name__)


class TaskProcessor:
    """
    Service class for processing tasks
    Coordinates task fetching, classification, and execution
    """
    
    def __init__(self):
        self.classifier = TaskClassifier()
        self.action_executor = ActionExecutor()
        logger.debug("TaskProcessor initialized with classifier")
    
    async def process(self, task_data: TaskRequest) -> Dict[str, Any]:
        """
        Process a task based on the provided data
        Now includes classification
        
        Args:
            task_data: Validated task request
            
        Returns:
            Dict containing task results with classification
            
        Raises:
            TaskProcessingError: If processing fails
        """
        logger.info(f"🔄 Processing task for: {task_data.email}")
        logger.info(f"📋 Task URL: {task_data.url}")
        
        try:
            # Step 1: Fetch task description from URL
            logger.info("=" * 60)
            logger.info("STEP 1: Fetching Task")
            logger.info("=" * 60)
            
            async with TaskFetcher() as fetcher:
                task_info = await fetcher.fetch_task(str(task_data.url))
            
            logger.info(
                f"✅ Task fetched | Type: {task_info['content_type']} | "
                f"Needs LLM: {task_info.get('needs_llm_analysis', False)}"
            )
            
            # Step 2: Classify task (includes content analysis if needed)
            logger.info("=" * 60)
            logger.info("STEP 2: Classifying Task")
            logger.info("=" * 60)
            
            content_analysis, classification = await self.classifier.classify_with_content_check(
                task_info
            )
            
            logger.info(
                f"✅ Classification complete | "
                f"Primary: {classification.primary_task.value} | "
                f"Complexity: {classification.complexity.value}"
            )
            
        # Step 3: Execute actions if needed
            task_description = task_info['task_description']
            
            if content_analysis and not content_analysis.is_direct_task:
                logger.info("=" * 60)
                logger.info("STEP 3: Executing Actions")
                logger.info("=" * 60)
                
                task_description = await self.action_executor.execute_actions(
                    content_analysis,
                    task_description
                )
                
                logger.info(f"✅ Actions executed | Task description length: {len(task_description)} chars")
            else:
                logger.info("Step 3: No actions required, task is direct")
            
            # TODO: Step 4 - Execute task based on classification
            # For now, return classification results
            
            result = {
                'status': 'classified',
                'email': task_data.email,
                'task_url': str(task_data.url),
                'task_description': task_description,
                'original_content_type': task_info['content_type'],
                'classification': {
                    'primary_task': classification.primary_task.value,
                    'secondary_tasks': [t.value for t in classification.secondary_tasks],
                    'complexity': classification.complexity.value,
                    'estimated_steps': classification.estimated_steps,
                    'requires_javascript': classification.requires_javascript,
                    'requires_authentication': classification.requires_authentication,
                    'requires_external_data': classification.requires_external_data,
                    'output_format': classification.output_format.value,
                    'confidence': classification.confidence,
                    'reasoning': classification.reasoning,
                    'key_entities': classification.key_entities,
                    'suggested_tools': classification.suggested_tools
                },
                'metadata': task_info.get('metadata', {}),
                'message': 'Task fetched, classified, and actions executed. Task execution pending (Step 4+).'
            }
            
            # Add content analysis if performed
            if content_analysis:
                result['content_analysis'] = {
                    'is_direct_task': content_analysis.is_direct_task,
                    'requires_download': content_analysis.requires_download,
                    'requires_transcription': content_analysis.requires_transcription,
                    'requires_ocr': content_analysis.requires_ocr,
                    'requires_navigation': content_analysis.requires_navigation,
                    'confidence': content_analysis.confidence,
                    'reasoning': content_analysis.reasoning,
                    'actions_executed': not content_analysis.is_direct_task
                }
            
            logger.info("=" * 60)
            logger.info("✅ Task processing completed (fetch + classify + actions stages)")
            logger.info("=" * 60)
            
            # Cleanup
            self.action_executor.cleanup()
            
            return result
        
        except TaskProcessingError:
            # Re-raise task processing errors
            raise
        
        except Exception as e:
            logger.error(f"❌ Task processing failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to process task: {str(e)}")
