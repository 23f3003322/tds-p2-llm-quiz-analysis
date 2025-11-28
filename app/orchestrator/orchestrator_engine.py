"""
Orchestrator Engine - Main Orchestration Logic
The brain that coordinates all components
"""

from typing import Dict, Any, Optional
import time

from app.orchestrator.execution_context import ExecutionContext
from app.orchestrator.classifier import TaskClassifier
from app.orchestrator.actions.action_executor import ActionExecutor
from app.orchestrator.parameter_extractor import ParameterExtractor
from app.modules.registry import ModuleRegistry, ModuleSelector
from app.routing.simple_router import SimpleRouter
from app.decomposition.task_decomposer import TaskDecomposer
from app.services.task_fetcher import TaskFetcher
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class OrchestratorEngine:
    """
    Main orchestrator engine
    Coordinates all components to execute tasks end-to-end
    """
    
    def __init__(
        self,
        module_registry: Optional[ModuleRegistry] = None,
        enable_decomposition: bool = True,
        enable_actions: bool = True
    ):
        """
        Initialize orchestrator engine
        
        Args:
            module_registry: Module registry (creates new if None)
            enable_decomposition: Enable task decomposition for complex tasks
            enable_actions: Enable action execution (downloads, transcription, etc.)
        """
        # Core components
        self.task_fetcher = TaskFetcher()
        self.classifier = TaskClassifier()
        self.parameter_extractor = ParameterExtractor()
        self.action_executor = ActionExecutor() if enable_actions else None
        
        # Module management
        self.registry = module_registry or ModuleRegistry()
        self.module_selector = ModuleSelector(self.registry)
        
        # Routing and decomposition
        self.simple_router = SimpleRouter(
            module_registry=self.registry,
            module_selector=self.module_selector
        )
        self.task_decomposer = TaskDecomposer() if enable_decomposition else None
        
        # Configuration
        self.enable_decomposition = enable_decomposition
        self.enable_actions = enable_actions
        
        logger.info("🚀 OrchestratorEngine initialized")
        logger.info(f"   Decomposition: {'enabled' if enable_decomposition else 'disabled'}")
        logger.info(f"   Actions: {'enabled' if enable_actions else 'disabled'}")
        logger.info(f"   Registered modules: {len(self.registry.get_all_modules())}")
    
    async def execute_task(
        self,
        task_input: str,
        task_url: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute task end-to-end
        Main entry point for task execution
        
        Args:
            task_input: Task description or URL
            task_url: Explicit task URL (if different from description)
            context: Optional execution context
            
        Returns:
            Dict: Execution result with all metadata
        """
        # Create execution context
        exec_context = ExecutionContext(
            original_task=task_input,
            task_url=task_url,
            metadata=context or {}
        )
        
        exec_context.log_event("Starting orchestration")
        
        logger.info("=" * 80)
        logger.info("🎯 ORCHESTRATOR ENGINE - Starting Task Execution")
        logger.info(f"Task ID: {exec_context.task_id}")
        logger.info(f"Execution ID: {exec_context.execution_id}")
        logger.info("=" * 80)
        
        try:
            # STEP 1: Fetch task details
            task_info = await self._step_1_fetch_task(task_input, exec_context)
            
            # STEP 2: Classify task
            classification = await self._step_2_classify_task(task_info, exec_context)
            
            # STEP 3: Execute actions (if needed)
            task_description = await self._step_3_execute_actions(
                classification,
                task_info,
                exec_context
            )
            
            # STEP 4: Extract parameters
            parameters = await self._step_4_extract_parameters(
                task_description,
                classification,
                exec_context
            )
            
            # STEP 5: Decide execution strategy
            execution_strategy = self._step_5_decide_strategy(
                classification,
                parameters,
                exec_context
            )
            
            # STEP 6: Execute based on strategy
            result = await self._step_6_execute(
                strategy=execution_strategy,
                classification=classification,
                parameters=parameters,
                task_description=task_description,
                exec_context=exec_context
            )
            
            # Mark completion
            exec_context.mark_completed()
            
            # Build final result
            final_result = self._build_final_result(result, exec_context)
            
            logger.info("=" * 80)
            logger.info(f"✅ ORCHESTRATION COMPLETE | Duration: {exec_context.get_duration():.2f}s")
            logger.info("=" * 80)
            
            return final_result
            
        except Exception as e:
            exec_context.mark_failed(str(e))
            logger.error(f"❌ Orchestration failed: {str(e)}", exc_info=True)
            
            return {
                'success': False,
                'error': str(e),
                'task_id': exec_context.task_id,
                'execution_id': exec_context.execution_id,
                'duration': exec_context.get_duration(),
                'execution_log': exec_context.execution_log
            }
    
    async def _step_1_fetch_task(
        self,
        task_input: str,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Step 1: Fetch task details"""
        
        logger.info("📥 Step 1: Fetching task details")
        context.log_event("Step 1: Fetch task - started")
        
        start_time = time.time()
        
        # Check if it's a URL or direct description
        if task_input.startswith(('http://', 'https://')):
            logger.info(f"Fetching task from URL: {task_input}")
            async with self.task_fetcher as fetcher:
                task_info = await fetcher.fetch_task(task_input)
        else:
            logger.info("Using direct task description")
            task_info = {
                'task_description': task_input,
                'source': 'direct_input',
                'url': None
            }
        
        duration = time.time() - start_time
        context.set_step_result('task_fetch', task_info)
        
        logger.info(f"✓ Task fetched | Duration: {duration:.2f}s")
        logger.debug(f"Task description length: {len(task_info['task_description'])} chars")
        
        return task_info
    
    async def _step_2_classify_task(
        self,
        task_info: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:  # TaskClassification
        """Step 2: Classify task"""
        
        logger.info("🔍 Step 2: Classifying task")
        context.log_event("Step 2: Classify task - started")
        
        start_time = time.time()
        
        classification = await self.classifier.classify_task(
            task_description=task_info['task_description']
        )
        
        duration = time.time() - start_time
        context.set_step_result('classification', classification)
        
        logger.info(f"✓ Task classified | Duration: {duration:.2f}s")
        logger.info(f"  Type: {classification.primary_task.value}")
        logger.info(f"  Complexity: {classification.complexity.value}")
        logger.info(f"  Confidence: {classification.confidence:.2f}")
        
        return classification
    
    async def _step_3_execute_actions(
    self,
    classification: Any,
    task_info: Dict[str, Any],
    context: ExecutionContext
) -> str:
        """Step 3: Execute actions (downloads, transcription, etc.)"""
        
        if not self.enable_actions:
            logger.info("⏭️  Step 3: Actions disabled, skipping")
            return task_info['task_description']
        
        logger.info("⚙️  Step 3: Executing actions")
        context.log_event("Step 3: Execute actions - started")
        
        start_time = time.time()
        
        # Check if actions are needed based on classification
        # Actions are needed if:
        # 1. Task requires external data
        # 2. Task has embedded content (URLs, files, media)
        # 3. Task is not direct/simple
        
        needs_actions = (
            classification.requires_external_data or
            classification.complexity.value != 'simple' or
            any(keyword in task_info['task_description'].lower() 
                for keyword in ['http://', 'https://', 'download', 'scrape', 'fetch', 
                            'transcribe', '.pdf', '.csv', '.mp4', '.mp3'])
        )
        
        if needs_actions:
            logger.info("Actions may be required, performing content analysis...")
            
            # Perform content analysis
            from app.orchestrator.models import ContentAnalysis
            
            # Simple content analysis based on task description
            content_analysis = self._analyze_content(
                task_info['task_description'],
                classification
            )
            
            if not content_analysis.is_direct_task:
                logger.info("Executing actions...")
                
                final_description = await self.action_executor.execute_actions(
                    content_analysis=content_analysis,
                    original_task_description=task_info['task_description']
                )
                
                duration = time.time() - start_time
                context.set_step_result('actions', {
                    'executed': True,
                    'final_description': final_description,
                    'content_analysis': content_analysis.dict()
                })
                
                logger.info(f"✓ Actions executed | Duration: {duration:.2f}s")
                return final_description
        
        logger.info("No actions required")
        context.set_step_result('actions', {'executed': False})
        return task_info['task_description']

    def _analyze_content(
        self,
        task_description: str,
        classification: Any
    ) -> Any:  # ContentAnalysis
        """
        Analyze content to determine if actions are needed
        
        Args:
            task_description: Task description
            classification: Task classification
            
        Returns:
            ContentAnalysis: Content analysis result
        """
        from app.orchestrator.models import ContentAnalysis
        import re
        
        # Extract URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, task_description)
        
        # Check for file references
        file_extensions = ['.pdf', '.csv', '.xlsx', '.json', '.xml', '.txt', 
                        '.mp4', '.mp3', '.wav', '.jpg', '.png']
        has_files = any(ext in task_description.lower() for ext in file_extensions)
        
        # Check for media
        media_keywords = ['video', 'audio', 'transcribe', 'image', 'screenshot']
        has_media = any(keyword in task_description.lower() for keyword in media_keywords)
        
        # Check for downloads
        download_keywords = ['download', 'fetch', 'get', 'retrieve']
        needs_download = has_files or any(
            kw in task_description.lower() for kw in download_keywords
        )
        
        # Determine if it's a direct task
        is_direct = not (urls or has_files or has_media or needs_download)
        
        # Determine content type
        if has_media and any(kw in task_description.lower() for kw in ['video', '.mp4']):
            content_type = 'video'
        elif has_media and any(kw in task_description.lower() for kw in ['audio', '.mp3', '.wav']):
            content_type = 'audio'
        elif any(kw in task_description.lower() for kw in ['image', '.jpg', '.png']):
            content_type = 'image'
        elif has_files:
            content_type = 'file'
        elif urls:
            content_type = 'html'
        else:
            content_type = 'text'
        
        # Build content analysis
        content_analysis = ContentAnalysis(
            content_type=content_type,
            is_direct_task=is_direct,
            requires_download=needs_download and has_files,
            requires_transcription=has_media and any(
                kw in task_description.lower() for kw in ['transcribe', 'audio', 'video']
            ),
            requires_ocr='ocr' in task_description.lower() or 
                        'extract text' in task_description.lower(),
            requires_navigation=bool(urls) and not has_files and not has_media,
            action_urls=urls if urls else [],
            task_description=task_description[:500],  # First 500 chars
            confidence=0.8,
            reasoning="Content analysis based on URL and keyword detection"
        )
        
        logger.debug(
            f"Content analysis: type={content_type}, is_direct={is_direct}, "
            f"urls={len(urls)}, needs_download={needs_download}"
        )
        
        return content_analysis


    async def _step_4_extract_parameters(
        self,
        task_description: str,
        classification: Any,
        context: ExecutionContext
    ) -> Any:  # ExtractedParameters
        """Step 4: Extract parameters"""
        
        logger.info("🔧 Step 4: Extracting parameters")
        context.log_event("Step 4: Extract parameters - started")
        
        start_time = time.time()
        
        result = await self.parameter_extractor.extract_parameters(
            task_description=task_description,
            context={'classification': classification.dict()}
        )
        
        duration = time.time() - start_time
        context.set_step_result('parameters', result.parameters)
        
        logger.info(f"✓ Parameters extracted | Duration: {duration:.2f}s")
        logger.info(f"  Data sources: {len(result.parameters.data_sources)}")
        logger.info(f"  Filters: {len(result.parameters.filters)}")
        logger.info(f"  Confidence: {result.parameters.confidence:.2f}")
        
        return result.parameters
    
    def _step_5_decide_strategy(
        self,
        classification: Any,
        parameters: Any,
        context: ExecutionContext
    ) -> str:
        """Step 5: Decide execution strategy"""
        
        logger.info("🎯 Step 5: Deciding execution strategy")
        context.log_event("Step 5: Decide strategy - started")
        
        # Check if decomposition is needed
        if self.enable_decomposition and self.task_decomposer:
            needs_decomposition = self.task_decomposer._needs_decomposition(
                classification,
                parameters
            )
            
            if needs_decomposition:
                logger.info("✓ Strategy: DECOMPOSE (complex task)")
                context.set_step_result('strategy', 'decompose')
                return 'decompose'
        
        logger.info("✓ Strategy: SIMPLE_ROUTE (simple task)")
        context.set_step_result('strategy', 'simple_route')
        return 'simple_route'
    
    async def _step_6_execute(
        self,
        strategy: str,
        classification: Any,
        parameters: Any,
        task_description: str,
        exec_context: ExecutionContext
    ) -> Dict[str, Any]:
        """Step 6: Execute based on strategy"""
        
        logger.info(f"🚀 Step 6: Executing with strategy: {strategy}")
        exec_context.log_event(f"Step 6: Execute ({strategy}) - started")
        
        start_time = time.time()
        
        if strategy == 'decompose':
            result = await self._execute_with_decomposition(
                classification,
                parameters,
                task_description,
                exec_context
            )
        else:
            result = await self._execute_simple_route(
                classification,
                parameters,
                task_description,
                exec_context
            )
        
        duration = time.time() - start_time
        exec_context.set_step_result('execution', result)
        
        logger.info(f"✓ Execution complete | Duration: {duration:.2f}s")
        
        return result
    
    async def _execute_simple_route(
        self,
        classification: Any,
        parameters: Any,
        task_description: str,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute using simple router"""
        
        logger.info("Executing via SimpleRouter")
        
        result = await self.simple_router.route_and_execute(
            classification=classification,
            parameters=parameters,
            task_description=task_description
        )
        
        return {
            'strategy': 'simple_route',
            'success': result.success,
            'data': result.data,
            'steps_completed': result.steps_completed,
            'total_steps': result.total_steps,
            'step_results': result.step_results,
            'errors': result.errors
        }
    
    async def _execute_with_decomposition(
        self,
        classification: Any,
        parameters: Any,
        task_description: str,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute complex task with decomposition"""
        
        logger.info("Executing via TaskDecomposer + SimpleRouter")
        
        # Decompose task
        logger.info("Decomposing task into subtasks...")
        decomposition = self.task_decomposer.decompose(
            classification=classification,
            parameters=parameters,
            task_description=task_description
        )
        
        logger.info(f"Task decomposed into {len(decomposition.subtasks)} subtasks")
        
        # Execute each subtask
        subtask_results = []
        
        for i, subtask in enumerate(decomposition.subtasks, 1):
            logger.info(f"Executing subtask {i}/{len(decomposition.subtasks)}: {subtask.name}")
            
            # Check if subtask can execute (dependencies met)
            ready_subtasks = decomposition.get_ready_subtasks()
            if subtask not in ready_subtasks:
                logger.warning(f"Subtask {subtask.id} dependencies not met, skipping")
                continue
            
            # Execute subtask using simple router
            subtask.status = "running"
            
            try:
                result = await self.simple_router.route_and_execute(
                    classification=subtask.classification,
                    parameters=subtask.parameters,
                    task_description=subtask.description
                )
                
                subtask.status = "completed"
                subtask.result = result.data
                
                subtask_results.append({
                    'subtask_id': subtask.id,
                    'name': subtask.name,
                    'success': result.success,
                    'data': result.data
                })
                
                logger.info(f"✓ Subtask {i} completed")
                
            except Exception as e:
                subtask.status = "failed"
                subtask.error = str(e)
                logger.error(f"✗ Subtask {i} failed: {e}")
        
        # Combine results
        final_data = subtask_results[-1]['data'] if subtask_results else None
        
        return {
            'strategy': 'decompose',
            'success': all(r['success'] for r in subtask_results),
            'data': final_data,
            'subtasks_completed': len(subtask_results),
            'total_subtasks': len(decomposition.subtasks),
            'subtask_results': subtask_results,
            'decomposition': {
                'execution_strategy': decomposition.execution_strategy,
                'complexity_score': decomposition.complexity_score,
                'can_parallelize': decomposition.can_parallelize
            }
        }
    
    def _build_final_result(
        self,
        execution_result: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Build final result dictionary"""
        
        return {
            'success': execution_result.get('success', False),
            'task_id': context.task_id,
            'execution_id': context.execution_id,
            'data': execution_result.get('data'),
            'strategy': execution_result.get('strategy'),
            'duration': context.get_duration(),
            'steps': {
                'task_fetch': context.get_step_result('task_fetch') is not None,
                'classification': context.get_step_result('classification') is not None,
                'actions': context.get_step_result('actions') is not None,
                'parameters': context.get_step_result('parameters') is not None,
                'execution': context.get_step_result('execution') is not None
            },
            'execution_details': execution_result,
            'execution_log': context.execution_log,
            'metadata': context.metadata
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.action_executor:
            self.action_executor.cleanup()
        self.simple_router.cleanup()
        logger.info("OrchestratorEngine cleanup complete")
