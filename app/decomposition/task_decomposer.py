"""
Task Decomposer
Main logic for decomposing complex tasks into subtasks
"""

from typing import Optional, List
import uuid

from app.decomposition.subtask_models import (
    Subtask,
    SubtaskDependency,
    DecompositionResult
)
from app.decomposition.decomposition_strategies import (
    DecompositionStrategy,
    SequentialStrategy,
    ParallelStrategy,
    ConditionalStrategy
)
from app.orchestrator.models import TaskClassification, ComplexityLevel
from app.orchestrator.parameter_models import ExtractedParameters
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskDecomposer:
    """
    Decomposes complex tasks into manageable subtasks
    Uses different strategies based on task complexity
    """
    
    def __init__(self):
        """Initialize task decomposer"""
        self.strategies = {
            'sequential': SequentialStrategy(),
            'parallel': ParallelStrategy(),
            'conditional': ConditionalStrategy()
        }
        
        logger.info("TaskDecomposer initialized")
    
    def decompose(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str,
        strategy: Optional[str] = None
    ) -> DecompositionResult:
        """
        Decompose task into subtasks
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            task_description: Task description
            strategy: Strategy to use (auto-selected if None)
            
        Returns:
            DecompositionResult: Decomposition result with subtasks
        """
        task_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🔨 Decomposing task | Task ID: {task_id}")
        logger.info(f"Task type: {classification.primary_task.value}")
        logger.info(f"Complexity: {classification.complexity.value}")
        logger.info(f"Estimated steps: {classification.estimated_steps}")
        
        # Check if decomposition is needed
        if not self._needs_decomposition(classification, parameters):
            logger.info("✓ Task is simple, no decomposition needed")
            return self._create_single_subtask_result(
                task_id,
                classification,
                parameters,
                task_description
            )
        
        # Select strategy
        if strategy is None:
            strategy = self._select_strategy(classification, parameters)
        
        logger.info(f"Using decomposition strategy: {strategy}")
        
        # Get strategy instance
        strategy_instance = self.strategies.get(strategy, SequentialStrategy())
        
        # Decompose
        subtasks = strategy_instance.decompose(
            classification,
            parameters,
            task_description
        )
        
        # Build dependencies
        dependencies = self._build_dependencies(subtasks)
        
        # Calculate metadata
        estimated_duration = sum(st.estimated_duration for st in subtasks)
        complexity_score = self._calculate_complexity(subtasks)
        can_parallelize = any(st.can_run_parallel for st in subtasks)
        
        result = DecompositionResult(
            task_id=task_id,
            subtasks=subtasks,
            dependencies=dependencies,
            execution_strategy=strategy,
            estimated_total_duration=estimated_duration,
            complexity_score=complexity_score,
            can_parallelize=can_parallelize,
            metadata={
                'original_task': task_description[:100],
                'subtask_count': len(subtasks),
                'has_visualizations': bool(parameters.visualizations),
                'has_filters': bool(parameters.filters)
            }
        )
        
        logger.info(
            f"✅ Decomposition complete | "
            f"Subtasks: {len(subtasks)} | "
            f"Strategy: {strategy} | "
            f"Est. duration: {estimated_duration}s"
        )
        
        return result
    
    def _needs_decomposition(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> bool:
        """
        Check if task needs decomposition
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            
        Returns:
            bool: True if decomposition needed
        """
        # Complex tasks always need decomposition
        if classification.complexity == ComplexityLevel.COMPLEX:
            return True
        
        # Multiple steps suggested by classifier
        if classification.estimated_steps > 2:
            return True
        
        # Multiple data sources
        if len(parameters.data_sources) > 1:
            return True
        
        # Has both processing and visualization
        if (parameters.filters or parameters.aggregations) and parameters.visualizations:
            return True
        
        # Has secondary tasks
        if classification.secondary_tasks:
            return True
        
        return False
    
    def _select_strategy(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> str:
        """
        Auto-select decomposition strategy
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            
        Returns:
            str: Strategy name
        """
        # Multiple independent data sources → parallel
        if len(parameters.data_sources) > 1:
            logger.debug("Multiple data sources detected, using parallel strategy")
            return 'parallel'
        
        # Complex with conditions → conditional
        # (For now, we'll use sequential for most cases)
        
        # Default to sequential
        logger.debug("Using sequential strategy")
        return 'sequential'
    
    def _create_single_subtask_result(
        self,
        task_id: str,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> DecompositionResult:
        """
        Create result with single subtask (no decomposition)
        
        Args:
            task_id: Task ID
            classification: Task classification
            parameters: Extracted parameters
            task_description: Task description
            
        Returns:
            DecompositionResult: Result with single subtask
        """
        subtask = Subtask(
            id="main_task",
            name="Main Task",
            type="data_fetch",
            description=task_description[:100],
            classification=classification,
            parameters=parameters,
            priority=1,
            estimated_duration=classification.estimated_steps * 20
        )
        
        return DecompositionResult(
            task_id=task_id,
            subtasks=[subtask],
            dependencies=[],
            execution_strategy='single',
            estimated_total_duration=subtask.estimated_duration,
            complexity_score=0.2,
            can_parallelize=False,
            metadata={'decomposed': False}
        )
    
    def _build_dependencies(self, subtasks: List[Subtask]) -> List[SubtaskDependency]:
        """
        Build dependency list from subtasks
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            List[SubtaskDependency]: Dependencies
        """
        dependencies = []
        
        for subtask in subtasks:
            if subtask.depends_on:
                dep = SubtaskDependency(
                    subtask_id=subtask.id,
                    depends_on=subtask.depends_on,
                    dependency_type='sequential' if not subtask.can_run_parallel else 'parallel'
                )
                dependencies.append(dep)
        
        return dependencies
    
    def _calculate_complexity(self, subtasks: List[Subtask]) -> float:
        """
        Calculate decomposition complexity score
        
        Args:
            subtasks: List of subtasks
            
        Returns:
            float: Complexity score (0-1)
        """
        if not subtasks:
            return 0.0
        
        # Base complexity on subtask count and dependencies
        count_score = min(1.0, len(subtasks) / 10.0)
        
        dependency_count = sum(len(st.depends_on) for st in subtasks)
        dependency_score = min(1.0, dependency_count / 20.0)
        
        # Average
        complexity = (count_score + dependency_score) / 2.0
        
        return round(complexity, 2)
