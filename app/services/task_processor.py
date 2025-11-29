"""
Task Processing Service
Simplified with unified LLM analysis in task_fetcher
"""

from typing import Dict, Any, Optional
from app.models.request import TaskRequest
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.orchestrator.orchestrator_engine import OrchestratorEngine
from app.modules.registry import ModuleRegistry
from app.modules.mock_modules import register_mock_modules
from app.services.task_fetcher import TaskFetcher
# from app.orchestrator.answer_submitter import AnswerSubmitter  # ✅ Fixed: uncommented

logger = get_logger(__name__)


class TaskProcessor:
    """
    Service class for processing TDS quiz tasks
    Uses unified LLM analysis from task_fetcher
    """
    
    def __init__(
        self,
        enable_decomposition: bool = True,
        enable_actions: bool = True,
        auto_register_modules: bool = True
    ):
        """Initialize task processor"""
        logger.info("🚀 Initializing TaskProcessor")
        
        # Setup components
        self.registry = ModuleRegistry()
        # self.answer_submitter = AnswerSubmitter()  # ✅ Fixed: using this
        
        if auto_register_modules:
            logger.info("📦 Registering modules...")
            register_mock_modules(self.registry)
            logger.info(f"✓ Registered {len(self.registry.get_all_modules())} modules")
        
        # Initialize orchestrator engine
        self.orchestrator = OrchestratorEngine(
            module_registry=self.registry,
            enable_decomposition=enable_decomposition,
            enable_actions=enable_actions
        )
        
        logger.info("✅ TaskProcessor initialized")
    
    async def process(self, task_data: TaskRequest) -> Dict[str, Any]:
        """
        Process TDS quiz task
        
        Flow:
        1. Fetch and analyze Request URL (unified LLM call in task_fetcher)
        2. If redirect, fetch Question URL (unified LLM call in task_fetcher)
        3. Execute orchestration
        4. Extract answer
        5. Submit to TDS
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
            # STEP 1: FETCH AND ANALYZE REQUEST URL (UNIFIED LLM CALL)
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 1: FETCHING & ANALYZING REQUEST URL")
            logger.info("=" * 80)
            
            async with TaskFetcher() as fetcher:
                analysis = await fetcher.fetch_and_analyze(url=request_url)
            
            logger.info(f"✓ Request URL analyzed")
            logger.info(f"  Is Redirect: {analysis['is_redirect']}")
            logger.info(f"  Complexity: {analysis['complexity']}")
            
            # ===================================================================
            # STEP 2: IF REDIRECT, FETCH QUESTION URL (UNIFIED LLM CALL)
            # ===================================================================
            if analysis['is_redirect'] and analysis['question_url']:
                logger.info("\n" + "=" * 80)
                logger.info("STEP 2: FETCHING & ANALYZING QUESTION URL")
                logger.info("=" * 80)
                
                question_url = analysis['question_url']
                logger.info(f"🔗 Detected redirect to: {question_url}")
                
                async with TaskFetcher() as fetcher:
                    analysis = await fetcher.fetch_and_analyze(
                        url=question_url,
                        base_url=request_url  # For resolving relative URLs
                    )
                
                logger.info(f"✓ Question URL analyzed")
                logger.info(f"  Task: {analysis['task_description'][:100]}...")
            else:
                question_url = request_url
                logger.info(f"✓ Request URL contains actual task (no redirect)")
            
            # Extract key information
            task_description = analysis['task_description']
            submission_url = analysis.get('submission_url') 
            instructions = analysis.get('instructions', [])
            
            # Log URL hierarchy
            logger.info("\n📍 URL Hierarchy:")
            logger.info(f"   Request URL:    {request_url}")
            logger.info(f"   Question URL:   {question_url}")
            logger.info(f"   Submission URL: {submission_url}")
            logger.info(f"   Instructions:   {len(instructions)} steps")
            
            # ===================================================================
            # STEP 3: EXECUTE ORCHESTRATION
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 3: EXECUTING ORCHESTRATION")
            logger.info("=" * 80)
            
            orchestration_result = await self.orchestrator.execute_task(
                task_input=task_description,
                task_url=question_url,
                context={
                    'email': task_data.email,
                    'request_url': request_url,
                    'question_url': question_url,
                    'submission_url': submission_url,
                    'instructions': instructions,
                    'complexity': analysis['complexity'],
                    'overall_goal': analysis['overall_goal']
                }
            )
            
            logger.info(f"✓ Orchestration completed")
            logger.info(f"  Success: {orchestration_result['success']}")
            logger.info(f"  Duration: {orchestration_result['duration']:.2f}s")
            
            # ===================================================================
            # STEP 4: EXTRACT ANSWER
            # ===================================================================
            logger.info("\n" + "=" * 80)
            logger.info("STEP 4: EXTRACTING ANSWER")
            logger.info("=" * 80)
            
            answer = self._extract_answer(orchestration_result)
            logger.info(f"✓ Answer extracted: {str(answer)[:200]}")
            
            # # ===================================================================
            # # STEP 5: SUBMIT ANSWER TO TDS
            # # ===================================================================
            # logger.info("\n" + "=" * 80)
            # logger.info("STEP 5: SUBMITTING ANSWER TO TDS")
            # logger.info("=" * 80)
            
            # submission_result = await self.answer_submitter.submit_answer(
            #     email=task_data.email,
            #     secret=task_data.secret,
            #     url=question_url,  # ✅ Use Question URL, not Request URL
            #     answer=answer,
            #     submission_url=submission_url
            # )
            
            # logger.info(f"✓ Submission completed")
            # logger.info(f"  Success: {submission_result['success']}")
            # logger.info(f"  Status Code: {submission_result.get('status_code')}")
            
            # if submission_result.get('response'):
            #     logger.info(f"  Response: {submission_result['response']}")
            
            # # ===================================================================
            # # STEP 6: BUILD RESPONSE
            # # ===================================================================
            # result = self._build_response(
            #     task_data=task_data,
            #     request_url=request_url,
            #     question_url=question_url,
            #     submission_url=submission_url,
            #     analysis=analysis,  # ✅ Fixed: pass analysis, not task_content
            #     orchestration_result=orchestration_result,
            #     submission_result=submission_result,
            #     answer=answer
            # )
            
            # logger.info("\n" + "=" * 80)
            # logger.info(f"✅ TASK COMPLETED SUCCESSFULLY")
            # logger.info(f"   Total Duration: {orchestration_result['duration']:.2f}s")
            # logger.info(f"   Answer Submitted: {submission_result['success']}")
            # logger.info("=" * 80)
            
            # return result  # ✅ Fixed: actually return the result
            return
        except TaskProcessingError:
            # Re-raise task processing errors
            raise
        
        except Exception as e:
            logger.error(f"❌ Task processing failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to process task: {str(e)}")
    
    def _extract_answer(self, orchestration_result: Dict[str, Any]) -> Any:
        """
        Extract final answer from orchestration result
        
        Tries multiple field names and strategies to find the answer
        """
        logger.debug("Extracting answer from orchestration result")
        
        if not orchestration_result.get('success'):
            logger.warning("Orchestration was not successful")
            return None
        
        data = orchestration_result.get('data', {})
        
        # If data is not a dict, return it directly
        if not isinstance(data, dict):
            logger.debug(f"Data is {type(data).__name__}, returning as-is")
            return data
        
        # Try common answer field names
        result_fields = [
            'answer', 'result', 'output', 'value', 'computed_value',
            'extracted_data', 'scraped_data', 'secret_code',
            'code', 'secret', 'solution', 'response'
        ]
        
        for field in result_fields:
            if field in data:
                logger.debug(f"Found answer in '{field}' field")
                return data[field]
        
        # If only one key, return its value
        if len(data) == 1:
            key = list(data.keys())[0]
            logger.debug(f"Single key '{key}' in data, using its value")
            return data[key]
        
        # Return entire data dict as last resort
        logger.debug("No specific answer field found, returning entire data")
        return data
    
    def _build_response(
        self,
        task_data: TaskRequest,
        request_url: str,
        question_url: str,
        submission_url: str,
        analysis: Dict[str, Any],  # ✅ Fixed: renamed from task_content
        orchestration_result: Dict[str, Any],
        submission_result: Dict[str, Any],
        answer: Any
    ) -> Dict[str, Any]:
        """
        Build comprehensive API response
        
        Args:
            task_data: Original task request
            request_url: Original URL from API request
            question_url: URL where actual task was found
            submission_url: URL where answer was submitted
            analysis: Unified analysis from task_fetcher
            orchestration_result: Result from orchestrator
            submission_result: Result from TDS submission
            answer: Extracted answer
            
        Returns:
            Formatted response dict
        """
        overall_success = (
            orchestration_result['success'] and 
            submission_result['success']
        )
        
        return {
            # Status
            'success': overall_success,
            'status': 'completed' if overall_success else 'failed',
            
            # Request info
            'email': task_data.email,
            
            # URL hierarchy
            'urls': {
                'request_url': request_url,
                'question_url': question_url,
                'submission_url': submission_url
            },
            
            # IDs and timing
            'task_id': orchestration_result.get('task_id'),
            'execution_id': orchestration_result.get('execution_id'),
            'duration': orchestration_result.get('duration'),
            'timestamp': orchestration_result.get('timestamp'),
            
            # Answer
            'answer': answer,
            
            # Submission details
            'submission': {
                'success': submission_result['success'],
                'status_code': submission_result.get('status_code'),
                'submitted_to': submission_url,
                'submitted_url': question_url,  # URL included in payload
                'response': submission_result.get('response')
            },
            
            # Task details
            'task_details': {
                'task_description': analysis['task_description'][:500],  # Truncate
                'complexity': analysis.get('complexity'),
                'overall_goal': analysis.get('overall_goal'),
                'instructions_count': len(analysis.get('instructions', [])),
                'was_redirect': analysis.get('is_redirect', False)
            },
            
            # Orchestration details
            'orchestration': {
                'success': orchestration_result['success'],
                'strategy': orchestration_result.get('strategy'),
                'steps_completed': list(orchestration_result.get('steps', {}).keys())
            },
            
            # LLM analysis metadata
            'llm_analysis': analysis.get('llm_analysis', {}),
            
            # Message
            'message': self._build_message(overall_success, orchestration_result, submission_result)
        }
    
    def _build_message(
        self,
        overall_success: bool,
        orchestration_result: Dict[str, Any],
        submission_result: Dict[str, Any]
    ) -> str:
        """Build human-readable status message"""
        if overall_success:
            return "Task completed successfully and answer submitted to TDS"
        
        if not orchestration_result['success']:
            error = orchestration_result.get('error', 'Unknown error')
            return f"Task execution failed: {error}"
        
        if not submission_result['success']:
            error = submission_result.get('error', 'Unknown error')
            return f"Task completed but submission failed: {error}"
        
        return "Task failed for unknown reason"
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_registry(self) -> ModuleRegistry:
        """Get module registry for adding/removing modules"""
        return self.registry
    
    def get_orchestrator(self) -> OrchestratorEngine:
        """Get orchestrator engine for advanced usage"""
        return self.orchestrator
    
    # def get_answer_submitter(self) -> AnswerSubmitter:
    #     """Get answer submitter for testing"""
    #     return self.answer_submitter
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.orchestrator.cleanup()
            logger.info("✓ Orchestrator cleanup complete")
        except Exception as e:
            logger.warning(f"Orchestrator cleanup error: {e}")
        
        logger.info("✅ TaskProcessor cleanup complete")
