"""
Processing Modules Package
Module registry and base interfaces
"""

from app.modules.base import BaseModule, ModuleCapability, ModuleResult
from app.modules.registry import ModuleRegistry, ModuleSelector
from app.modules.capabilities import (
    ScrapingCapability,
    ProcessingCapability,
    VisualizationCapability,
    OutputCapability
)

__all__ = [
    "BaseModule",
    "ModuleCapability",
    "ModuleResult",
    "ModuleRegistry",
    "ModuleSelector",
    "ScrapingCapability",
    "ProcessingCapability",
    "VisualizationCapability",
    "OutputCapability"
]
