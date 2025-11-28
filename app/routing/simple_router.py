"""
Simple Router
Routes tasks to appropriate modules and executes them
Handles single-step and simple multi-step tasks
"""

from typing import List, Dict, Any, Optional
import time
import uuid

from app.routing.execution_plan import (
    ExecutionPlan,
    ExecutionStep,
    ExecutionResult,
    StepStatus
)
from app.routing.module_executor import ModuleExecutor
from app.modules.base import BaseModule
from app.modules.registry import ModuleRegistry, ModuleSelector
from app.orchestrator.models import TaskClassification
from app.orchestrator.parameter_models import ExtractedParameters
from app.core.logging import get_logger
from app.core.exceptions import TaskProcessingError

logger = get_logger(__name__)


class SimpleRouter:
    """
    Simple task router for single-step and linear multi-step tasks
    Does NOT handle complex branching or parallel execution
    """
    
    def __init__(
        self,
        module_registry: Optional[ModuleRegistry] = None,
        module_selector: Optional[ModuleSelector] = None
    ):
        """
        Initialize simple router
        
        Args:
            module_registry: Module registry (creates new if None)
            module_selector: Module selector (creates new if None)
        """
        self.registry = module_registry or ModuleRegistry()
        self.selector = module_selector or ModuleSelector(self.registry)
        self.executor = ModuleExecutor()
        
        logger.info("SimpleRouter initialized")
    
    async def route_and_execute(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> ExecutionResult:
        """
        Route task and execute
        Main entry point for simple routing
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            task_description: Original task description
            
        Returns:
            ExecutionResult: Final execution result
        """
        task_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🚀 Starting task routing | Task ID: {task_id}")
        logger.info(f"Task type: {classification.primary_task.value}")
        logger.info(f"Complexity: {classification.complexity.value}")
        
        start_time = time.time()
        
        try:
            # Step 1: Select modules
            logger.info("📋 Step 1: Module selection")
            selected_modules = self.selector.select_modules(classification, parameters)
            
            if not selected_modules:
                logger.warning("No modules selected for task")
                return ExecutionResult(
                    task_id=task_id,
                    success=False,
                    total_steps=0,
                    errors=["No modules available to execute this task"]
                )
            
            logger.info(f"✓ Selected {len(selected_modules)} modules")
            
            # Step 2: Create execution plan
            logger.info("📋 Step 2: Creating execution plan")
            plan = self._create_execution_plan(
                task_id=task_id,
                modules=selected_modules,
                parameters=parameters,
                task_description=task_description
            )
            
            logger.info(f"✓ Execution plan created with {len(plan.steps)} steps")
            
            # Step 3: Execute plan
            logger.info("📋 Step 3: Executing plan")
            result = await self._execute_plan(plan, selected_modules)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            logger.info(
                f"✅ Task execution complete | "
                f"Success: {result.success} | "
                f"Time: {execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"❌ Task execution failed: {str(e)}", exc_info=True)
            
            return ExecutionResult(
                task_id=task_id,
                success=False,
                errors=[str(e)],
                execution_time=execution_time
            )
    
    def _create_execution_plan(
        self,
        task_id: str,
        modules: List[BaseModule],
        parameters: ExtractedParameters,
        task_description: str
    ) -> ExecutionPlan:
        """
        Create execution plan from selected modules
        
        Args:
            task_id: Task identifier
            modules: Selected modules
            parameters: Extracted parameters
            task_description: Task description
            
        Returns:
            ExecutionPlan: Execution plan
        """
        steps = []
        
        for i, module in enumerate(modules, 1):
            # Configure module parameters
            module_params = self._configure_module_parameters(
                module=module,
                parameters=parameters,
                step_number=i
            )
            
            # Create step
            step = ExecutionStep(
                step_number=i,
                module_name=module.name,
                description=self._generate_step_description(module, i, len(modules)),
                parameters=module_params,
                depends_on=[i - 1] if i > 1 else []  # Linear dependency
            )
            
            steps.append(step)
        
        # Estimate duration
        estimated_duration = sum(
            module.estimate_cost(step.parameters) * 10
            for module, step in zip(modules, steps)
        )
        
        plan = ExecutionPlan(
            task_id=task_id,
            description=task_description[:100],
            steps=steps,
            estimated_duration=int(estimated_duration),
            complexity=self._assess_plan_complexity(modules)
        )
        
        return plan
    
    def _configure_module_parameters(
        self,
        module: BaseModule,
        parameters: ExtractedParameters,
        step_number: int
    ) -> Dict[str, Any]:
        """
        Configure parameters for specific module
        
        Args:
            module: Module to configure
            parameters: Extracted parameters
            step_number: Step number
            
        Returns:
            Dict: Configured parameters for module
        """
        config = {}
        
        # Data source (for scrapers/API clients)
        if parameters.data_sources and step_number == 1:
            data_source = parameters.data_sources[0]
            config['url'] = data_source.location
            config['format'] = data_source.format
        
        # Filters (for processors)
        if parameters.filters:
            config['filters'] = [
                {
                    'field': f.field,
                    'operator': f.operator,
                    'value': f.value
                }
                for f in parameters.filters
            ]
        
        # Columns (for data extraction)
        if parameters.columns:
            config['columns'] = [col.name for col in parameters.columns]
        
        # Aggregations (for processors)
        if parameters.aggregations:
            config['aggregations'] = [
                {
                    'function': agg.function,
                    'field': agg.field,
                    'group_by': agg.group_by
                }
                for agg in parameters.aggregations
            ]
        
        # Sorting (for processors)
        if parameters.sorting:
            config['sorting'] = [
                {
                    'field': sort.field,
                    'order': sort.order
                }
                for sort in parameters.sorting
            ]
        
        # Visualizations (for visualizers)
        if parameters.visualizations:
            viz = parameters.visualizations[0]
            config['chart_type'] = viz.chart_type
            config['title'] = viz.title
        
        # Output format (for exporters)
        if parameters.output:
            config['format'] = parameters.output.format
            config['filename'] = parameters.output.filename
        
        return config
    
    def _generate_step_description(
        self,
        module: BaseModule,
        step_num: int,
        total_steps: int
    ) -> str:
        """Generate human-readable step description"""
        
        descriptions = {
            'static_scraper': f'Step {step_num}/{total_steps}: Scrape data from website',
            'dynamic_scraper': f'Step {step_num}/{total_steps}: Scrape dynamic content (JavaScript)',
            'api_client': f'Step {step_num}/{total_steps}: Fetch data from API',
            'data_processor': f'Step {step_num}/{total_steps}: Process and filter data',
            'chart_creator': f'Step {step_num}/{total_steps}: Create visualization',
            'csv_exporter': f'Step {step_num}/{total_steps}: Export to CSV',
        }
        
        return descriptions.get(
            module.name,
            f'Step {step_num}/{total_steps}: Execute {module.name}'
        )
    
    def _assess_plan_complexity(self, modules: List[BaseModule]) -> str:
        """Assess plan complexity"""
        if len(modules) == 1:
            return "simple"
        elif len(modules) <= 3:
            return "medium"
        else:
            return "complex"
    
    async def _execute_plan(
        self,
        plan: ExecutionPlan,
        modules: List[BaseModule]
    ) -> ExecutionResult:
        """
        Execute the plan
        
        Args:
            plan: Execution plan
            modules: Modules to execute
            
        Returns:
            ExecutionResult: Execution result
        """
        logger.info(f"Executing plan with {len(plan.steps)} steps")
        
        step_results = []
        final_data = None
        
        for step in plan.steps:
            logger.info(f"📍 {step.description}")
            
            # Get module
            module = next(m for m in modules if m.name == step.module_name)
            
            # Update status
            step.status = StepStatus.RUNNING
            
            # Execute
            try:
                result = await self.executor.execute_module(
                    module=module,
                    parameters=step.parameters,
                    context=self.executor.get_context()
                )
                
                # Update step
                step.result = result
                
                if result.success:
                    step.status = StepStatus.COMPLETED
                    final_data = result.data
                    
                    step_results.append({
                        'step': step.step_number,
                        'module': step.module_name,
                        'success': True,
                        'execution_time': result.execution_time
                    })
                else:
                    step.status = StepStatus.FAILED
                    step.error = result.error
                    
                    step_results.append({
                        'step': step.step_number,
                        'module': step.module_name,
                        'success': False,
                        'error': result.error
                    })
                    
                    # Stop on first failure
                    logger.error(f"Step {step.step_number} failed, stopping execution")
                    break
                    
            except Exception as e:
                step.status = StepStatus.FAILED
                step.error = str(e)
                
                step_results.append({
                    'step': step.step_number,
                    'module': step.module_name,
                    'success': False,
                    'error': str(e)
                })
                
                logger.error(f"Step {step.step_number} exception: {e}")
                break
        
        # Create result
        completed_steps = sum(
            1 for step in plan.steps
            if step.status == StepStatus.COMPLETED
        )
        
        success = plan.is_completed() and not plan.has_failed()
        
        errors = [
            f"Step {step.step_number} ({step.module_name}): {step.error}"
            for step in plan.steps
            if step.error
        ]
        
        result = ExecutionResult(
            task_id=plan.task_id,
            success=success,
            data=final_data,
            steps_completed=completed_steps,
            total_steps=len(plan.steps),
            step_results=step_results,
            errors=errors,
            metadata={
                'plan_complexity': plan.complexity,
                'estimated_duration': plan.estimated_duration
            }
        )
        
        return result
    
    def cleanup(self):
        """Clean up resources"""
        self.executor.clear_context()
        logger.debug("SimpleRouter cleanup complete")
