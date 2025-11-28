"""
Task Decomposition Package
Breaks complex tasks into manageable subtasks
"""

from app.decomposition.task_decomposer import TaskDecomposer
from app.decomposition.subtask_models import (
    Subtask,
    SubtaskType,
    SubtaskDependency,
    DecompositionResult
)
from app.decomposition.decomposition_strategies import (
    SequentialStrategy,
    ParallelStrategy,
    ConditionalStrategy
)

__all__ = [
    "TaskDecomposer",
    "Subtask",
    "SubtaskType",
    "SubtaskDependency",
    "DecompositionResult",
    "SequentialStrategy",
    "ParallelStrategy",
    "ConditionalStrategy"
]
