"""
Processing Modules Package
Module registry and base interfaces
"""

from app.modules.base import BaseModule, ModuleCapability, ModuleResult
from app.modules.registry import ModuleRegistry

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
    "OutputCapability",
    "ExtractionCapability",
    "CalculationCapability",
    "GenerationCapability",
    "AnalysisCapability",
    "register_all_modules",
    "get_fully_loaded_registry"
]

def __getattr__(name):
    if name == "ModuleRegistry":
        from app.modules.registry import ModuleRegistry
        return ModuleRegistry
    elif name == "ModuleSelector":
        from app.modules.registry import ModuleSelector
        return ModuleSelector
    elif name == "DataSourceCapability":
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
    elif name == "ExtractionCapability":
        from app.modules.capabilities import ExtractionCapability
        return ExtractionCapability
    elif name == "CalculationCapability":
        from app.modules.capabilities import CalculationCapability
        return CalculationCapability
    elif name == "GenerationCapability":
        from app.modules.capabilities import GenerationCapability
        return GenerationCapability
    elif name == "AnalysisCapability":
        from app.modules.capabilities import AnalysisCapability
        return AnalysisCapability
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

# =========================================================================
# AUTO-REGISTRATION (COMPLETE VERSION)
# =========================================================================

def register_all_modules(registry=None):
    """Auto-register all available modules"""
    if registry is None:
        from app.modules import ModuleRegistry
        registry = ModuleRegistry()
    
    # Scrapers
    try:
        from app.modules.scrapers.static_scraper import StaticScraper
        registry.register(StaticScraper())
        print("✓ Registered StaticScraper")
    except ImportError:
        print("⚠️ StaticScraper not found")
    
    try:
        from app.modules.scrapers.dynamic_scraper import DynamicScraper
        registry.register(DynamicScraper())
        print("✓ Registered DynamicScraper")
    except ImportError:
        print("⚠️ DynamicScraper not found")
    
    # Extractors ← CRITICAL FOR TDS!
    try:
        from app.modules.extractors.data_extractor import DataExtractor
        registry.register(DataExtractor())
        print("✓ Registered DataExtractor")
    except ImportError:
        print("⚠️ DataExtractor not found - TDS WILL FAIL!")
    
    # Submitters ← CRITICAL FOR QUIZ SUBMISSION!
    try:
        from app.modules.submitters.answer_submitter import AnswerSubmitter
        registry.register(AnswerSubmitter())
        print("✓ Registered AnswerSubmitter")
    except ImportError:
        print("⚠️ AnswerSubmitter not found - QUIZ SUBMISSION WILL FAIL!")
    
    return registry

def get_fully_loaded_registry():
    """Get registry with all modules auto-registered"""
    registry = ModuleRegistry()
    return register_all_modules(registry)
