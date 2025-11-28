"""
Execution Context Manager
Manages shared state and data flow between components
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from pydantic import BaseModel, Field
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExecutionContext(BaseModel):
    """
    Execution context shared across all orchestration steps
    Contains state, intermediate results, and metadata
    """
    
    # Identification
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Task information
    original_task: str = Field(description="Original task description")
    task_url: Optional[str] = Field(None, description="Task URL if applicable")
    
    # Execution state
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = Field(default="initialized", description="Execution status")
    
    # Intermediate results from each step
    step_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from each orchestration step"
    )
    
    # Shared data between modules
    shared_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Data shared between execution modules"
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    # Execution log
    execution_log: List[str] = Field(
        default_factory=list,
        description="Execution event log"
    )
    
    class Config:
        arbitrary_types_allowed = True
    
    def log_event(self, event: str):
        """Log an execution event"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {event}"
        self.execution_log.append(log_entry)
        logger.debug(log_entry)
    
    def set_step_result(self, step_name: str, result: Any):
        """Store result from a step"""
        self.step_results[step_name] = result
        self.log_event(f"Step '{step_name}' completed")
    
    def get_step_result(self, step_name: str) -> Optional[Any]:
        """Get result from a step"""
        return self.step_results.get(step_name)
    
    def set_shared_data(self, key: str, value: Any):
        """Set shared data"""
        self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """Get shared data"""
        return self.shared_data.get(key, default)
    
    def mark_completed(self):
        """Mark execution as completed"""
        self.completed_at = datetime.now()
        self.status = "completed"
        self.log_event("Execution completed")
    
    def mark_failed(self, error: str):
        """Mark execution as failed"""
        self.completed_at = datetime.now()
        self.status = "failed"
        self.log_event(f"Execution failed: {error}")
    
    def get_duration(self) -> float:
        """Get execution duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()
