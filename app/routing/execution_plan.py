"""
Execution Plan Models
Defines how tasks will be executed
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum

from app.modules.base import BaseModule, ModuleResult


class StepStatus(str, Enum):
    """Execution step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStep(BaseModel):
    """
    Single step in execution plan
    Represents one module execution
    """
    
    step_number: int = Field(description="Step number in sequence")
    module_name: str = Field(description="Name of module to execute")
    description: str = Field(description="Human-readable step description")
    
    # Module configuration
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters for module execution"
    )
    
    # Dependencies
    depends_on: List[int] = Field(
        default_factory=list,
        description="Step numbers this step depends on"
    )
    
    # Execution state
    status: StepStatus = Field(
        default=StepStatus.PENDING,
        description="Current execution status"
    )
    
    result: Optional[ModuleResult] = Field(
        None,
        description="Result after execution"
    )
    
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        arbitrary_types_allowed = True


class ExecutionPlan(BaseModel):
    """
    Complete execution plan for a task
    Defines sequence of module executions
    """
    
    task_id: str = Field(description="Unique task identifier")
    description: str = Field(description="Task description")
    
    steps: List[ExecutionStep] = Field(
        default_factory=list,
        description="Ordered list of execution steps"
    )
    
    estimated_duration: int = Field(
        60,
        description="Estimated execution time in seconds"
    )
    
    complexity: str = Field(
        "medium",
        description="Plan complexity (simple, medium, complex)"
    )
    
    def get_next_step(self) -> Optional[ExecutionStep]:
        """
        Get next pending step that has all dependencies completed
        
        Returns:
            ExecutionStep or None if no step is ready
        """
        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            if self._dependencies_completed(step):
                return step
        
        return None
    
    def _dependencies_completed(self, step: ExecutionStep) -> bool:
        """Check if all dependencies for a step are completed"""
        if not step.depends_on:
            return True
        
        for dep_step_num in step.depends_on:
            dep_step = self.get_step(dep_step_num)
            if not dep_step or dep_step.status != StepStatus.COMPLETED:
                return False
        
        return True
    
    def get_step(self, step_number: int) -> Optional[ExecutionStep]:
        """Get step by number"""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def is_completed(self) -> bool:
        """Check if all steps are completed"""
        return all(
            step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
            for step in self.steps
        )
    
    def has_failed(self) -> bool:
        """Check if any step has failed"""
        return any(step.status == StepStatus.FAILED for step in self.steps)
    
    def get_progress(self) -> float:
        """Get completion progress (0.0 to 1.0)"""
        if not self.steps:
            return 1.0
        
        completed = sum(
            1 for step in self.steps
            if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
        )
        
        return completed / len(self.steps)


class ExecutionResult(BaseModel):
    """
    Final result of task execution
    """
    
    task_id: str = Field(description="Task identifier")
    success: bool = Field(description="Whether execution succeeded")
    
    # Final data
    data: Any = Field(None, description="Final output data")
    
    # Execution metadata
    steps_completed: int = Field(0, description="Number of steps completed")
    total_steps: int = Field(0, description="Total number of steps")
    execution_time: float = Field(0.0, description="Total execution time in seconds")
    
    # Step results
    step_results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Results from each step"
    )
    
    # Errors and warnings
    errors: List[str] = Field(default_factory=list, description="Errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        arbitrary_types_allowed = True
