"""
Processing Modules Package
Module registry and base interfaces
"""

from app.modules.base import BaseModule, ModuleCapability, ModuleResult

# Lazy imports to avoid circular dependency
__all__ = [
    "BaseModule",
    "ModuleCapability",
    "ModuleResult",
    "ModuleRegistry",
    "ModuleSelector",
    "ScrapingCapability",
    "ProcessingCapability",
    "VisualizationCapability",
    "DataSourceCapability",
    "OutputCapability"
]

def __getattr__(name):
    if name == "ModuleRegistry":
        from app.modules.registry import ModuleRegistry
        return ModuleRegistry
    elif name == "ModuleSelector":
        from app.modules.registry import ModuleSelector
        return ModuleSelector
    elif name == "DataSourceCapability":  # ← Add this
        from app.modules.capabilities import DataSourceCapability
        return DataSourceCapability
    elif name == "ScrapingCapability":
        from app.modules.capabilities import ScrapingCapability
        return ScrapingCapability
    elif name == "ProcessingCapability":
        from app.modules.capabilities import ProcessingCapability
        return ProcessingCapability
    elif name == "VisualizationCapability":
        from app.modules.capabilities import VisualizationCapability
        return VisualizationCapability
    elif name == "OutputCapability":
        from app.modules.capabilities import OutputCapability
        return OutputCapability
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
