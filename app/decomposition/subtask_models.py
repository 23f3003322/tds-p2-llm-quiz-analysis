"""
Subtask Models
Data models for task decomposition
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field
from enum import Enum

from app.orchestrator.models import TaskClassification
from app.orchestrator.parameter_models import ExtractedParameters


class SubtaskType(str, Enum):
    """Types of subtasks"""
    DATA_FETCH = "data_fetch"
    DATA_PROCESS = "data_process"
    DATA_TRANSFORM = "data_transform"
    DATA_AGGREGATE = "data_aggregate"
    DATA_FILTER = "data_filter"
    VISUALIZATION = "visualization"
    EXPORT = "export"
    VALIDATION = "validation"


class SubtaskDependency(BaseModel):
    """Dependency between subtasks"""
    subtask_id: str = Field(description="ID of dependent subtask")
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of subtasks this depends on"
    )
    dependency_type: str = Field(
        default="sequential",
        description="Type of dependency (sequential, parallel, conditional)"
    )


class Subtask(BaseModel):
    """
    Individual subtask in decomposed task
    """
    
    id: str = Field(description="Unique subtask identifier")
    name: str = Field(description="Human-readable subtask name")
    type: SubtaskType = Field(description="Type of subtask")
    description: str = Field(description="Detailed subtask description")
    
    # Classification and parameters for this subtask
    classification: TaskClassification = Field(
        description="Classification for this subtask"
    )
    parameters: ExtractedParameters = Field(
        description="Parameters for this subtask"
    )
    
    # Dependencies
    depends_on: List[str] = Field(
        default_factory=list,
        description="IDs of subtasks this depends on"
    )
    
    # Execution metadata
    priority: int = Field(
        default=0,
        description="Execution priority (higher = earlier)"
    )
    
    can_run_parallel: bool = Field(
        default=False,
        description="Can this run in parallel with others"
    )
    
    estimated_duration: int = Field(
        default=30,
        description="Estimated duration in seconds"
    )
    
    # Status tracking
    status: str = Field(
        default="pending",
        description="Execution status"
    )
    
    result: Optional[Any] = Field(
        None,
        description="Result after execution"
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if failed"
    )
    
    class Config:
        arbitrary_types_allowed = True


class DecompositionResult(BaseModel):
    """
    Result of task decomposition
    """
    
    task_id: str = Field(description="Original task ID")
    
    subtasks: List[Subtask] = Field(
        default_factory=list,
        description="List of decomposed subtasks"
    )
    
    dependencies: List[SubtaskDependency] = Field(
        default_factory=list,
        description="Subtask dependencies"
    )
    
    execution_strategy: str = Field(
        description="Recommended execution strategy"
    )
    
    estimated_total_duration: int = Field(
        description="Estimated total duration in seconds"
    )
    
    complexity_score: float = Field(
        description="Decomposition complexity (0-1)"
    )
    
    can_parallelize: bool = Field(
        default=False,
        description="Can subtasks run in parallel"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def get_subtask(self, subtask_id: str) -> Optional[Subtask]:
        """Get subtask by ID"""
        for subtask in self.subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None
    
    def get_ready_subtasks(self) -> List[Subtask]:
        """
        Get subtasks that are ready to execute
        (pending status and all dependencies completed)
        """
        ready = []
        
        for subtask in self.subtasks:
            if subtask.status != "pending":
                continue
            
            # Check dependencies
            if self._dependencies_completed(subtask):
                ready.append(subtask)
        
        return ready
    
    def _dependencies_completed(self, subtask: Subtask) -> bool:
        """Check if all dependencies are completed"""
        if not subtask.depends_on:
            return True
        
        for dep_id in subtask.depends_on:
            dep_subtask = self.get_subtask(dep_id)
            if not dep_subtask or dep_subtask.status != "completed":
                return False
        
        return True
    
    def get_execution_order(self) -> List[List[str]]:
        """
        Get execution order as list of batches
        Each batch can run in parallel
        """
        batches = []
        completed = set()
        
        while len(completed) < len(self.subtasks):
            batch = []
            
            for subtask in self.subtasks:
                if subtask.id in completed:
                    continue
                
                # Check if dependencies are completed
                if all(dep_id in completed for dep_id in subtask.depends_on):
                    batch.append(subtask.id)
            
            if not batch:
                break  # Circular dependency or error
            
            batches.append(batch)
            completed.update(batch)
        
        return batches
