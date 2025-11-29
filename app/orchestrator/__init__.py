"""
Orchestrator Package
Intelligent task routing and execution
"""

from app.orchestrator.classifier import TaskClassifier
from app.orchestrator.actions.action_executor import ActionExecutor
from app.orchestrator.parameter_extractor import ParameterExtractor 
from app.orchestrator.models import (
    TaskClassification,
    ContentAnalysis,
    TaskType,
    ComplexityLevel,
    OutputFormat
)
from app.orchestrator.parameter_models import (  
    ExtractedParameters,
    ParameterExtractionResult,
    DataSource,
    FilterCondition,
    VisualizationRequirement
)
# Remove direct import - causes circular dependency
# from app.orchestrator.orchestrator_engine import OrchestratorEngine
from app.orchestrator.execution_context import ExecutionContext 


__all__ = [
    "TaskClassifier",
    "ActionExecutor",
    "ParameterExtractor",  
    "TaskClassification",
    "ContentAnalysis",
    "TaskType",
    "ComplexityLevel",
    "OutputFormat",
    "ExtractedParameters",  
    "ParameterExtractionResult",  
    "DataSource",  
    "FilterCondition",  
    "VisualizationRequirement",  
    "OrchestratorEngine",  # Keep in __all__ for documentation
    "ExecutionContext", 
]


# Lazy import to avoid circular dependency
def __getattr__(name):
    """Lazy import for OrchestratorEngine to break circular dependency"""
    if name == "OrchestratorEngine":
        from app.orchestrator.orchestrator_engine import OrchestratorEngine
        return OrchestratorEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
