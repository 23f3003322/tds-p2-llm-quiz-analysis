"""
Decomposition Strategies
Different strategies for decomposing tasks
"""

from typing import List, Dict, Any
from abc import ABC, abstractmethod

from app.decomposition.subtask_models import Subtask, SubtaskType
from app.orchestrator.models import TaskClassification, TaskType, ComplexityLevel, OutputFormat
from app.orchestrator.parameter_models import ExtractedParameters, DataSource
from app.core.logging import get_logger

logger = get_logger(__name__)


class DecompositionStrategy(ABC):
    """Base class for decomposition strategies"""
    
    @abstractmethod
    def decompose(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> List[Subtask]:
        """
        Decompose task into subtasks
        
        Args:
            classification: Task classification
            parameters: Extracted parameters
            task_description: Task description
            
        Returns:
            List[Subtask]: Decomposed subtasks
        """
        pass


class SequentialStrategy(DecompositionStrategy):
    """
    Sequential decomposition strategy
    Each subtask depends on previous one
    """
    
    def decompose(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> List[Subtask]:
        """Decompose into sequential subtasks"""
        
        logger.info("Using sequential decomposition strategy")
        
        subtasks = []
        subtask_counter = 1
        
        # Subtask 1: Data fetching
        if parameters.data_sources:
            subtask = self._create_fetch_subtask(
                subtask_counter,
                classification,
                parameters
            )
            subtasks.append(subtask)
            subtask_counter += 1
        
        # Subtask 2: Data processing (if filters/transformations)
        if parameters.filters or parameters.aggregations or parameters.sorting:
            prev_id = subtasks[-1].id if subtasks else None
            subtask = self._create_process_subtask(
                subtask_counter,
                classification,
                parameters,
                depends_on=[prev_id] if prev_id else []
            )
            subtasks.append(subtask)
            subtask_counter += 1
        
        # Subtask 3: Visualization (if needed)
        if parameters.visualizations:
            prev_id = subtasks[-1].id if subtasks else None
            subtask = self._create_visualization_subtask(
                subtask_counter,
                classification,
                parameters,
                depends_on=[prev_id] if prev_id else []
            )
            subtasks.append(subtask)
            subtask_counter += 1
        
        # Subtask 4: Export (if output specified)
        if parameters.output:
            prev_id = subtasks[-1].id if subtasks else None
            subtask = self._create_export_subtask(
                subtask_counter,
                classification,
                parameters,
                depends_on=[prev_id] if prev_id else []
            )
            subtasks.append(subtask)
        
        return subtasks
    
    def _create_fetch_subtask(
        self,
        counter: int,
        classification: TaskClassification,
        parameters: ExtractedParameters
    ) -> Subtask:
        """Create data fetching subtask"""
        
        data_source = parameters.data_sources[0]
        
        return Subtask(
            id=f"fetch_{counter}",
            name="Data Fetching",
            type=SubtaskType.DATA_FETCH,
            description=f"Fetch data from {data_source.location}",
            classification=TaskClassification(
                primary_task=TaskType.WEB_SCRAPING if data_source.type == 'url' else TaskType.FILE_PROCESSING,
                secondary_tasks=[],
                complexity=ComplexityLevel.SIMPLE,
                estimated_steps=1,
                requires_javascript=classification.requires_javascript,
                output_format=OutputFormat.JSON,
                confidence=0.9,
                reasoning="Data fetching subtask"
            ),
            parameters=ExtractedParameters(
                data_sources=[data_source]
            ),
            priority=counter,
            estimated_duration=20
        )
    
    def _create_process_subtask(
        self,
        counter: int,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        depends_on: List[str]
    ) -> Subtask:
        """Create data processing subtask"""
        
        return Subtask(
            id=f"process_{counter}",
            name="Data Processing",
            type=SubtaskType.DATA_PROCESS,
            description="Filter, transform, and aggregate data",
            classification=TaskClassification(
                primary_task=TaskType.ML_ANALYSIS,
                secondary_tasks=[],
                complexity=ComplexityLevel.MEDIUM,
                estimated_steps=1,
                output_format=OutputFormat.JSON,
                confidence=0.9,
                reasoning="Data processing subtask"
            ),
            parameters=ExtractedParameters(
                filters=parameters.filters,
                aggregations=parameters.aggregations,
                sorting=parameters.sorting,
                columns=parameters.columns
            ),
            depends_on=depends_on,
            priority=counter,
            estimated_duration=15
        )
    
    def _create_visualization_subtask(
        self,
        counter: int,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        depends_on: List[str]
    ) -> Subtask:
        """Create visualization subtask"""
        
        return Subtask(
            id=f"visualize_{counter}",
            name="Visualization",
            type=SubtaskType.VISUALIZATION,
            description="Create charts and visualizations",
            classification=TaskClassification(
                primary_task=TaskType.VISUALIZATION,
                secondary_tasks=[],
                complexity=ComplexityLevel.SIMPLE,
                estimated_steps=1,
                output_format=OutputFormat.FILE,
                confidence=0.9,
                reasoning="Visualization subtask"
            ),
            parameters=ExtractedParameters(
                visualizations=parameters.visualizations
            ),
            depends_on=depends_on,
            priority=counter,
            estimated_duration=10
        )
    
    def _create_export_subtask(
        self,
        counter: int,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        depends_on: List[str]
    ) -> Subtask:
        """Create export subtask"""
        
        return Subtask(
            id=f"export_{counter}",
            name="Export Results",
            type=SubtaskType.EXPORT,
            description=f"Export results as {parameters.output.format}",
            classification=TaskClassification(
                primary_task=TaskType.FILE_PROCESSING,
                secondary_tasks=[],
                complexity=ComplexityLevel.SIMPLE,
                estimated_steps=1,
                output_format=classification.output_format,
                confidence=0.9,
                reasoning="Export subtask"
            ),
            parameters=ExtractedParameters(
                output=parameters.output
            ),
            depends_on=depends_on,
            priority=counter,
            estimated_duration=5
        )


class ParallelStrategy(DecompositionStrategy):
    """
    Parallel decomposition strategy
    Independent subtasks can run in parallel
    """
    
    def decompose(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> List[Subtask]:
        """Decompose with parallel execution where possible"""
        
        logger.info("Using parallel decomposition strategy")
        
        subtasks = []
        
        # If multiple data sources, fetch them in parallel
        if len(parameters.data_sources) > 1:
            for i, data_source in enumerate(parameters.data_sources, 1):
                subtask = Subtask(
                    id=f"fetch_parallel_{i}",
                    name=f"Fetch Data Source {i}",
                    type=SubtaskType.DATA_FETCH,
                    description=f"Fetch from {data_source.location}",
                    classification=TaskClassification(
                        primary_task=TaskType.WEB_SCRAPING,
                        secondary_tasks=[],
                        complexity=ComplexityLevel.SIMPLE,
                        estimated_steps=1,
                        output_format=OutputFormat.JSON,
                        confidence=0.9,
                        reasoning=f"Parallel fetch {i}"
                    ),
                    parameters=ExtractedParameters(
                        data_sources=[data_source]
                    ),
                    can_run_parallel=True,
                    priority=1,
                    estimated_duration=20
                )
                subtasks.append(subtask)
            
            # Merge subtask (depends on all fetches)
            merge_subtask = Subtask(
                id="merge_results",
                name="Merge Results",
                type=SubtaskType.DATA_TRANSFORM,
                description="Merge data from all sources",
                classification=TaskClassification(
                    primary_task=TaskType.ML_ANALYSIS,
                    secondary_tasks=[],
                    complexity=ComplexityLevel.SIMPLE,
                    estimated_steps=1,
                    output_format=OutputFormat.JSON,
                    confidence=0.9,
                    reasoning="Merge parallel results"
                ),
                parameters=ExtractedParameters(),
                depends_on=[st.id for st in subtasks],
                priority=2,
                estimated_duration=10
            )
            subtasks.append(merge_subtask)
        
        else:
            # Single source, use sequential
            sequential = SequentialStrategy()
            return sequential.decompose(classification, parameters, task_description)
        
        return subtasks


class ConditionalStrategy(DecompositionStrategy):
    """
    Conditional decomposition strategy
    Some subtasks execute based on conditions
    """
    
    def decompose(
        self,
        classification: TaskClassification,
        parameters: ExtractedParameters,
        task_description: str
    ) -> List[Subtask]:
        """Decompose with conditional logic"""
        
        logger.info("Using conditional decomposition strategy")
        
        # For now, use sequential as base
        # Can be extended for complex conditional logic
        sequential = SequentialStrategy()
        return sequential.decompose(classification, parameters, task_description)
