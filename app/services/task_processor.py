"""
Task Processing Service
Simplified with unified LLM analysis in task_fetcher + AnswerSubmitter integration
"""

from typing import Dict, Any, Optional
import asyncio
from app.models.request import TaskRequest
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.orchestrator.orchestrator_engine import OrchestratorEngine
from app.modules import get_fully_loaded_registry  # ✅ AUTO-REGISTRATION
from app.services.task_fetcher import TaskFetcher
from app.modules.submitters.answer_submitter import AnswerSubmitter  # ✅ NEW

logger = get_logger(__name__)

class TaskProcessor:
    """
    Service class for processing TDS quiz tasks
    Uses unified LLM analysis from task_fetcher + AnswerSubmitter
    """
    
    def __init__(self):
        """Initialize task processor with auto-registration"""
        logger.info("🚀 Initializing TaskProcessor")
        
        # ✅ AUTO-REGISTER ALL MODULES
        self.registry = get_fully_loaded_registry()
        self.answer_submitter = AnswerSubmitter()
        
        # Initialize orchestrator engine
        self.orchestrator = OrchestratorEngine(self.registry)
        
        logger.info(f"✅ TaskProcessor initialized with {len(self.registry.modules)} modules")
    
    async def process(self, task_data: TaskRequest) -> Dict[str, Any]:
        """
        Process TDS quiz task - COMPLETE END-TO-END FLOW
        
        Flow:
        1. Fetch and analyze Request URL 
        2. Execute orchestration (scrape → extract → answer)
        3. Extract answer
        4. Submit to TDS ✅ NEW
        5. Handle chained quizzes ✅ NEW
        6. Build response
        """
        logger.info("=" * 80)
        logger.info(f"🔄 Processing task for: {task_data.email}")
        logger.info(f"📋 Request URL: {task_data.url}")
        logger.info("=" * 80)
        
        request_url = str(task_data.url)
        question_url = None
        submission_url = None
        
        try:
            # ===================================================================
            # STEP 1: FETCH AND ANALYZE REQUEST URL
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: FETCHING & ANALYZING REQUEST URL")
            logger.info("=" * 80)
            
            # ✅ FIXED: Use proper async context manager pattern
            async with TaskFetcher() as fetcher:
                analysis = await fetcher.fetch_and_analyze(url=request_url)
            
            logger.info(f"✓ Request URL analyzed")
            logger.info(f"  Submission URL: {analysis.get('submission_url')}")
            
            # Extract key information
            task_description = analysis['task_description']
            submission_url = analysis.get('submission_url') 
            instructions = analysis.get('instructions', [])
            question_url = request_url  # Default to request URL
            
            logger.info(f"📍 Submission URL: {submission_url}")
            logger.info(f"📋 Instructions: {len(instructions)} steps")
            
            # ===================================================================
            # STEP 2: EXECUTE ORCHESTRATION (Scrape → Extract → Answer)
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: EXECUTING ORCHESTRATION")
            logger.info("=" * 80)
            
            orchestration_result = await self.orchestrator.execute_task(
                task_input=task_description,
                task_url=question_url,
                context={
                    'email': task_data.email,
                    'request_url': request_url,
                    'question_url': question_url,
                    'submission_url': submission_url,
                    'instructions': instructions
                }
            )
            
            logger.info(f"✓ Orchestration completed")
            logger.info(f"  Success: {orchestration_result['success']}")
            
            # ===================================================================
            # STEP 3: EXTRACT ANSWER
            # ===================================================================
            answer = self._extract_answer(orchestration_result)
            logger.info(f"✓ Answer extracted: {str(answer)[:100]}")

            if not answer or answer == "No answer found":
                logger.warning("⚠️ No valid answer extracted")
                return self._build_response(
                    task_data, request_url, question_url, submission_url, 
                    analysis, orchestration_result, None, answer
                )

            # ===================================================================
            # STEP 4: SUBMIT ANSWER & HANDLE CHAINING
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: SUBMITTING & CHAINING")
            logger.info("=" * 80)

            submission_result = await self.answer_submitter.execute({
                'submission_url': submission_url,
                'email': task_data.email,
                'secret': str(answer),
                'quiz_url': question_url,
                'answer': answer
            })

            logger.info(f"✓ Submission completed: {getattr(submission_result, 'success', False)}")

            # ✅ ALWAYS check for new URL first
            if (hasattr(submission_result, 'data') and 
                submission_result.data and 
                (next_url := submission_result.data.get('next_quiz_url'))):
                
                logger.info(f"🔄 NEW QUIZ DETECTED: {next_url}")

                # ✅ FIXED: Proper background task handling with reference tracking
                background_tasks = set()
                task = asyncio.create_task(self._process_chained_quiz(task_data.email, next_url, submission_url))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

                return {
                    'success': True,
                    'status': 'chained',
                    'message': f'Submitted & chained to next quiz: {next_url}',
                    'next_url': next_url,
                    'correct': submission_result.data.get('correct', False)
                }

            # ✅ No new URL = SUCCESS (whether correct or not)
            logger.info("✅ No new quiz - Task completed successfully")
            return {
                'success': True,
                'status': 'completed',
                'message': 'Answer submitted successfully to TDS',
                'correct': getattr(submission_result, 'data', {}).get('correct', False)
            }
            
        except Exception as e:
            logger.error(f"❌ Task processing failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to process task: {str(e)}")
    
    async def _process_chained_quiz(self, email: str, next_url: str, submission_url: str) -> Dict:
        """Process chained quiz in background"""
        try:
            logger.info(f"🔄 Processing chained quiz: {next_url}")
            
            async with TaskFetcher() as fetcher:
                analysis = await fetcher.fetch_and_analyze(url=next_url)
            
            orchestration_result = await self.orchestrator.execute_task(
                task_input=analysis['task_description'],
                task_url=next_url,
                context={'email': email, 'submission_url': submission_url}
            )
            
            answer = self._extract_answer(orchestration_result)
            submission_result = await self.answer_submitter.execute({
                'submission_url': submission_url,
                'email': email,
                'secret': str(answer),
                'quiz_url': next_url,
                'answer': answer
            })
            
            logger.info(f"✅ Chained quiz {next_url} completed: {submission_result.success}")
            return {
                'next_url': next_url,
                'success': getattr(submission_result, 'success', False),
                'answer': answer,
                'correct': getattr(submission_result, 'data', {}).get('correct')
            }
        except Exception as e:
            logger.error(f"❌ Chained quiz failed: {next_url} - {e}", exc_info=True)
            return {'next_url': next_url, 'success': False, 'error': str(e)}
    
    def _extract_answer(self, orchestration_result: Dict[str, Any]) -> Any:
        """Extract final answer from orchestration result"""
        if not orchestration_result.get('success'):
            return None
        
        data = orchestration_result.get('data', {})
        if not isinstance(data, dict):
            return data
        
        # Priority extraction fields
        priority_fields = ['secret_code', 'answer', 'extracted', 'result', 'secret']
        for field in priority_fields:
            if field in data:
                return data[field]
            if f'{field}s' in data:
                values = data.get(f'{field}s', {})
                if values:
                    return list(values.values())[-1]
        
        if data.get('extracted_values'):
            extracted = data['extracted_values']
            return list(extracted.values())[-1] if extracted else data
        
        return data
    
    def _build_response(
        self, 
        task_data: TaskRequest, 
        request_url: str, 
        question_url: str, 
        submission_url: str, 
        analysis: Dict, 
        orchestration_result: Dict, 
        submission_result: Optional[Dict], 
        answer: Any
    ) -> Dict[str, Any]:
        """Build comprehensive API response"""
        overall_success = (
            orchestration_result.get('success', False) and 
            (submission_result.get('success', False) if submission_result else False)
        )
        
        return {
            'success': overall_success,
            'status': 'completed' if overall_success else 'failed',
            'email': task_data.email,
            'urls': {
                'request_url': request_url,
                'question_url': question_url,
                'submission_url': submission_url
            },
            'task_id': orchestration_result.get('task_id'),
            'execution_id': orchestration_result.get('execution_id'),
            'duration': orchestration_result.get('duration'),
            'answer': answer,
            'submission': getattr(submission_result, 'data', None),
            'orchestration': {
                'success': orchestration_result.get('success'),
                'modules_used': orchestration_result.get('modules_used', []),
                'strategy': orchestration_result.get('strategy')
            },
            'task_details': {
                'description': analysis.get('task_description', '')[:200],
                'instructions': len(analysis.get('instructions', []))
            }
        }
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.orchestrator.cleanup()
            await self.answer_submitter.cleanup()
            logger.info("✅ TaskProcessor cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

