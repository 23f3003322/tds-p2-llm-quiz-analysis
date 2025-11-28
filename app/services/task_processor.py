"""
Task Processing Service
Complete orchestration using OrchestratorEngine (Steps 1-8)
"""

from typing import Dict, Any

from app.models.request import TaskRequest
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError
from app.orchestrator.orchestrator_engine import OrchestratorEngine
from app.modules.registry import ModuleRegistry
from app.modules.mock_modules import register_mock_modules

logger = get_logger(__name__)


class TaskProcessor:
    """
    Service class for processing tasks
    Uses complete orchestration engine (Steps 1-8)
    """
    
    def __init__(
        self,
        enable_decomposition: bool = True,
        enable_actions: bool = True,
        auto_register_modules: bool = True
    ):
        """
        Initialize task processor
        
        Args:
            enable_decomposition: Enable complex task decomposition
            enable_actions: Enable action execution (downloads, transcription, OCR)
            auto_register_modules: Auto-register mock modules
        """
        logger.info("🚀 Initializing TaskProcessor with OrchestratorEngine")
        
        # Setup module registry
        self.registry = ModuleRegistry()
        
        if auto_register_modules:
            logger.info("📦 Registering mock modules...")
            register_mock_modules(self.registry)
            logger.info(f"✓ Registered {len(self.registry.get_all_modules())} modules")
        
        # Initialize orchestrator engine (Steps 1-8)
        self.orchestrator = OrchestratorEngine(
            module_registry=self.registry,
            enable_decomposition=enable_decomposition,
            enable_actions=enable_actions
        )
        
        logger.info("✅ TaskProcessor initialized with complete orchestration")
    
    async def process(self, task_data: TaskRequest) -> Dict[str, Any]:
        """
        Process a task based on the provided data
        Uses complete orchestration pipeline (Steps 1-8)
        
        Args:
            task_data: Validated task request
            
        Returns:
            Dict containing complete task results
            
        Raises:
            TaskProcessingError: If processing fails
        """
        logger.info(f"🔄 Processing task for: {task_data.email}")
        logger.info(f"📋 Task URL: {task_data.url}")
        
        try:
            # Execute complete orchestration
            logger.info("=" * 80)
            logger.info("EXECUTING COMPLETE ORCHESTRATION PIPELINE (Steps 1-8)")
            logger.info("=" * 80)
            
            orchestration_result = await self.orchestrator.execute_task(
                task_input=str(task_data.url),
                task_url=str(task_data.url),
                context={'email': task_data.email}
            )
            
            # Build response
            result = self._build_response(
                task_data=task_data,
                orchestration_result=orchestration_result
            )
            
            logger.info("=" * 80)
            logger.info(f"✅ Task processing completed | Duration: {orchestration_result['duration']:.2f}s")
            logger.info("=" * 80)
            
            return result
        
        except TaskProcessingError:
            # Re-raise task processing errors
            raise
        
        except Exception as e:
            logger.error(f"❌ Task processing failed: {str(e)}", exc_info=True)
            raise TaskProcessingError(f"Failed to process task: {str(e)}")
    
    def _build_response(
        self,
        task_data: TaskRequest,
        orchestration_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build API response from orchestration result
        
        Args:
            task_data: Original task request
            orchestration_result: Result from orchestrator
            
        Returns:
            Dict: Formatted response
        """
        # Extract key information from orchestration
        classification = orchestration_result.get('execution_details', {}).get('classification')
        parameters = orchestration_result.get('execution_details', {}).get('parameters')
        
        # Base response
        response = {
            'status': 'completed' if orchestration_result['success'] else 'failed',
            'email': task_data.email,
            'task_url': str(task_data.url),
            'task_id': orchestration_result['task_id'],
            'execution_id': orchestration_result['execution_id'],
            'duration': orchestration_result['duration'],
            'strategy': orchestration_result.get('strategy', 'unknown'),
            'success': orchestration_result['success']
        }
        
        # Add execution details
        if orchestration_result['success']:
            response['result'] = {
                'data': orchestration_result.get('data'),
                'execution_details': orchestration_result.get('execution_details', {}),
                'steps_completed': orchestration_result.get('steps', {})
            }
            
            # Add classification if available
            if classification:
                response['classification'] = self._format_classification(classification)
            
            # Add parameters if available
            if parameters:
                response['parameters'] = self._format_parameters(parameters)
            
            response['message'] = 'Task executed successfully through complete orchestration pipeline'
        
        else:
            response['error'] = orchestration_result.get('error', 'Unknown error')
            response['message'] = 'Task execution failed'
        
        # Add execution log
        response['execution_log'] = orchestration_result.get('execution_log', [])
        
        return response
    
    def _format_classification(self, classification: Any) -> Dict[str, Any]:
        """Format classification for API response"""
        try:
            return {
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
            }
        except Exception as e:
            logger.warning(f"Could not format classification: {e}")
            return {'error': 'Classification format error'}
    
    def _format_parameters(self, parameters: Any) -> Dict[str, Any]:
        """Format parameters for API response"""
        try:
            return {
                'data_sources': [
                    {
                        'type': ds.type,
                        'location': ds.location,
                        'format': ds.format,
                        'description': ds.description
                    }
                    for ds in parameters.data_sources
                ],
                'filters': [
                    {
                        'field': f.field,
                        'operator': f.operator,
                        'value': f.value,
                        'description': f.description
                    }
                    for f in parameters.filters
                ],
                'columns': [col.name for col in parameters.columns],
                'aggregations': len(parameters.aggregations),
                'visualizations': len(parameters.visualizations),
                'output_format': parameters.output.format if parameters.output else None,
                'confidence': parameters.confidence,
                'complexity_score': parameters.complexity_score
            }
        except Exception as e:
            logger.warning(f"Could not format parameters: {e}")
            return {'error': 'Parameters format error'}
    
    def get_registry(self) -> ModuleRegistry:
        """Get module registry for adding/removing modules"""
        return self.registry
    
    def get_orchestrator(self) -> OrchestratorEngine:
        """Get orchestrator engine for advanced usage"""
        return self.orchestrator
    
    def cleanup(self):
        """Clean up resources"""
        self.orchestrator.cleanup()
        logger.info("TaskProcessor cleanup complete")
